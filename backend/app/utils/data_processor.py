import pandas as pd
import numpy as np
import pandas as pd
import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from werkzeug.utils import secure_filename
from ..core.exceptions import FileException, ErrorCode

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理器"""
    
    def __init__(self, allowed_extensions: List[str], max_size_mb: int):
        """
        初始化数据处理器
        
        Args:
            allowed_extensions: 允许的文件扩展名
            max_size_mb: 最大文件大小(MB)
        """
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        self.max_size_bytes = max_size_mb * 1024 * 1024
    
    def validate_file(self, filename: str, file_size: int) -> bool:
        """
        验证文件
        
        Args:
            filename: 文件名
            file_size: 文件大小(字节)
            
        Returns:
            是否验证通过
            
        Raises:
            FileException: 验证失败时抛出异常
        """
        # 检查文件扩展名
        if not filename:
            raise FileException(ErrorCode.FILE_FORMAT_UNSUPPORTED, "文件名不能为空")
        
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in self.allowed_extensions:
            raise FileException(
                ErrorCode.FILE_FORMAT_UNSUPPORTED,
                f"不支持的文件格式: {file_ext}",
                f"支持的格式: {', '.join(self.allowed_extensions)}"
            )
        
        # 检查文件大小
        if file_size > self.max_size_bytes:
            raise FileException(
                ErrorCode.FILE_TOO_LARGE,
                f"文件大小超过限制",
                f"文件大小: {file_size / 1024 / 1024:.2f}MB, 限制: {self.max_size_bytes / 1024 / 1024}MB"
            )
        
        return True
    
    def read_file(self, file_path: str) -> pd.DataFrame:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            DataFrame对象
            
        Raises:
            FileException: 读取失败时抛出异常
        """
        try:
            file_ext = os.path.splitext(file_path.lower())[1]
            
            if file_ext == '.csv':
                # 尝试不同的编码
                for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise FileException(
                        ErrorCode.FILE_CONTENT_INVALID,
                        "无法解析CSV文件编码"
                    )
            
            elif file_ext in ['.xlsx', '.xls']:
                engine = 'openpyxl' if file_ext == '.xlsx' else 'xlrd'
                df = pd.read_excel(file_path, engine=engine)
            
            else:
                raise FileException(
                    ErrorCode.FILE_FORMAT_UNSUPPORTED,
                    f"不支持的文件格式: {file_ext}"
                )
            
            # 验证DataFrame是否为空
            if df.empty:
                raise FileException(
                    ErrorCode.FILE_CONTENT_INVALID,
                    "文件内容为空"
                )
            
            logger.info(f"Successfully read file: {file_path}, shape: {df.shape}")
            return df
            
        except pd.errors.EmptyDataError:
            raise FileException(ErrorCode.FILE_CONTENT_INVALID, "文件内容为空")
        except pd.errors.ParserError as e:
            raise FileException(ErrorCode.FILE_CONTENT_INVALID, f"文件格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise FileException(ErrorCode.FILE_CONTENT_INVALID, f"读取文件失败: {str(e)}")
    
    def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析数据特征
        
        Args:
            df: DataFrame对象
            
        Returns:
            数据分析结果
        """
        try:
            # 基本信息
            columns = df.columns.tolist()
            row_count = int(len(df))  # 确保转换为Python int
            
            # 分析列类型
            column_types = {}
            for col in columns:
                col_type = self._infer_column_type(df[col])
                column_types[col] = col_type
            
            # 获取示例数据（前5行，处理NaN值和数据类型转换）
            sample_data = []
            for i in range(min(5, row_count)):
                row = []
                for col in columns:
                    value = df.iloc[i][col]
                    if pd.isna(value):
                        row.append(None)
                    else:
                        # 转换pandas数据类型为Python原生类型
                        row.append(self._convert_to_json_serializable(value))
                sample_data.append(row)
            
            # 统计信息
            stats = {}
            for col in columns:
                col_stats = self._get_column_stats(df[col], column_types[col])
                if col_stats:
                    stats[col] = col_stats
            
            result = {
                'columns': columns,
                'row_count': row_count,
                'column_types': column_types,
                'sample_data': sample_data,
                'stats': stats
            }
            
            logger.info(f"Data analysis completed: {row_count} rows, {len(columns)} columns")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            raise FileException(ErrorCode.FILE_CONTENT_INVALID, f"数据分析失败: {str(e)}")
    
    def _infer_column_type(self, series: pd.Series) -> str:
        """
        推断列的数据类型
        
        Args:
            series: 列数据
            
        Returns:
            数据类型字符串
        """
        # 移除空值
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return "空值"
        
        # 检查是否为数值类型
        if pd.api.types.is_numeric_dtype(series):
            if pd.api.types.is_integer_dtype(series):
                return "整数"
            else:
                return "小数"
        
        # 检查是否为日期时间类型
        if pd.api.types.is_datetime64_any_dtype(series):
            return "日期时间"
        
        # 检查是否可以转换为数值
        try:
            pd.to_numeric(non_null_series)
            return "数值"
        except (ValueError, TypeError):
            pass
        
        # 检查是否为日期
        try:
            pd.to_datetime(non_null_series)
            return "日期"
        except (ValueError, TypeError):
            pass
        
        # 检查唯一值数量，判断是否为分类数据
        unique_count = series.nunique()
        total_count = len(series)
        
        if unique_count <= 10 or unique_count / total_count < 0.1:
            return "分类"
        
        return "文本"
    
    def _get_column_stats(self, series: pd.Series, col_type: str) -> Optional[Dict[str, Any]]:
        """
        获取列的统计信息
        
        Args:
            series: 列数据
            col_type: 列类型
            
        Returns:
            统计信息字典
        """
        try:
            stats: Dict[str, Any] = {  # type: ignore
                'null_count': int(series.isnull().sum()),  # 转换为int
                'unique_count': int(series.nunique())     # 转换为int
            }
            
            if col_type in ["整数", "小数", "数值"]:
                stats['min'] = self._convert_to_json_serializable(series.min())
                stats['max'] = self._convert_to_json_serializable(series.max())
                stats['mean'] = self._convert_to_json_serializable(series.mean())
                stats['median'] = self._convert_to_json_serializable(series.median())
            
            elif col_type == "分类":
                value_counts = series.value_counts().head(5)
                # 转换value_counts为普通dict
                top_values = {}
                for key, val in value_counts.items():
                    top_values[str(key)] = int(val)
                stats['top_values'] = top_values
            
            elif col_type in ["文本"]:
                if series.nunique() <= 20:  # 如果唯一值不多，显示前几个
                    value_counts = series.value_counts().head(5)
                    # 转换value_counts为普通dict
                    top_values = {}
                    for key, val in value_counts.items():
                        top_values[str(key)] = int(val)
                    stats['top_values'] = top_values
            
            return stats
            
        except Exception as e:
            logger.warning(f"Error getting stats for column: {e}")
            return None
    
    def _convert_to_json_serializable(self, value: Any) -> Union[int, float, bool, str, list, dict, None]:
        """
        将pandas/numpy数据类型转换为JSON可序列化的Python原生类型
        
        Args:
            value: 原始值
            
        Returns:
            转换后的值
        """
        import numpy as np
        
        # 处理NaN值
        if pd.isna(value):
            return None
        
        # 处理numpy数据类型 - 使用dtype检查而不是isinstance
        if hasattr(value, 'dtype'):
            if np.issubdtype(value.dtype, np.integer):
                return int(value)
            elif np.issubdtype(value.dtype, np.floating):
                return float(value)
            elif np.issubdtype(value.dtype, np.bool_):
                return bool(value)
        
        # 处理numpy数组
        elif isinstance(value, np.ndarray):
            return value.tolist()
        
        # 处理pandas特殊类型
        elif hasattr(value, 'item'):  # numpy scalar
            return value.item()
        
        # 处理日期时间类型
        elif isinstance(value, pd.Timestamp):
            return value.isoformat()
        
        # 已经是Python原生类型
        elif isinstance(value, (int, float, str, bool, list, dict)):
            return value
        
        # 其他情况，转换为字符串
        else:
            return str(value)
    
    def clean_filename(self, filename: str) -> str:
        """
        清理文件名
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        return secure_filename(filename)