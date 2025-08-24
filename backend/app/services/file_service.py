import os
import uuid
import json
import shutil
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage
from ..core.config import get_config
from ..core.exceptions import FileException, ErrorCode
from ..utils.data_processor import DataProcessor

logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理numpy和pandas数据类型"""
    
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        elif pd.isna(obj):
            return None
        return super().default(obj)


class FileService:
    """文件处理服务"""
    
    def __init__(self):
        """初始化文件服务"""
        self.config = get_config()
        file_config = self.config.get_file_config()
        
        self.temp_dir = file_config.get('temp_dir', './temp')
        self.max_size_mb = file_config.get('max_size_mb', 5)
        self.allowed_extensions = file_config.get('allowed_extensions', ['.xlsx', '.xls', '.csv'])
        self.cleanup_interval = file_config.get('cleanup_interval', 3600)
        
        # 创建临时目录
        self._ensure_temp_dirs()
        
        # 初始化数据处理器
        self.data_processor = DataProcessor(self.allowed_extensions, self.max_size_mb)
    
    def _ensure_temp_dirs(self):
        """确保临时目录存在"""
        uploads_dir = os.path.join(self.temp_dir, 'uploads')
        charts_dir = os.path.join(self.temp_dir, 'charts')
        
        os.makedirs(uploads_dir, exist_ok=True)
        os.makedirs(charts_dir, exist_ok=True)
        
        logger.info(f"Temp directories ensured: {uploads_dir}, {charts_dir}")
    
    def process_uploaded_file(self, file: FileStorage) -> Dict[str, Any]:
        """
        处理上传的文件
        
        Args:
            file: 上传的文件对象
            
        Returns:
            处理结果，包含session_id和数据摘要
            
        Raises:
            FileException: 处理失败时抛出异常
        """
        try:
            # 验证文件
            if not file or not file.filename:
                raise FileException(ErrorCode.FILE_FORMAT_UNSUPPORTED, "未选择文件")
            
            # 获取文件信息
            filename = file.filename
            file_size = self._get_file_size(file)
            
            # 验证文件
            self.data_processor.validate_file(filename, file_size)
            
            # 生成会话ID和文件路径
            session_id = str(uuid.uuid4())
            clean_filename = self.data_processor.clean_filename(filename)
            
            # 创建会话目录
            session_dir = os.path.join(self.temp_dir, 'uploads', session_id)
            os.makedirs(session_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(session_dir, clean_filename)
            file.save(file_path)
            
            logger.info(f"File saved: {file_path}")
            
            # 读取和分析数据
            df = self.data_processor.read_file(file_path)
            data_summary = self.data_processor.analyze_data(df)
            
            # 保存会话信息
            session_data = {
                'session_id': session_id,
                'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat(),
                'file_info': {
                    'original_filename': filename,
                    'clean_filename': clean_filename,
                    'file_path': file_path,
                    'size': file_size,
                    'type': file.content_type or 'unknown'
                },
                'data_summary': data_summary
            }
            
            self._save_session_data(session_id, session_data)
            
            logger.info(f"File processed successfully: {session_id}")
            
            return {
                'session_id': session_id,
                'data_summary': data_summary,
                'file_info': session_data['file_info']
            }
            
        except FileException:
            raise
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            raise FileException(ErrorCode.FILE_UPLOAD_FAILED, f"文件处理失败: {str(e)}")
    
    def _get_file_size(self, file: FileStorage) -> int:
        """
        获取文件大小
        
        Args:
            file: 文件对象
            
        Returns:
            文件大小(字节)
        """
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        return file_size
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，如果不存在则返回None
        """
        try:
            session_file = os.path.join(self.temp_dir, 'charts', f'{session_id}.json')
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error reading session data {session_id}: {e}")
            return None
    
    def _save_session_data(self, session_id: str, data: Dict[str, Any]):
        """
        保存会话数据
        
        Args:
            session_id: 会话ID
            data: 会话数据
        """
        try:
            session_file = os.path.join(self.temp_dir, 'charts', f'{session_id}.json')
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
            logger.debug(f"Session data saved: {session_id}")
        except Exception as e:
            logger.error(f"Error saving session data {session_id}: {e}")
    
    def update_session_charts(self, session_id: str, charts: list):
        """
        更新会话的图表数据
        
        Args:
            session_id: 会话ID
            charts: 图表列表
        """
        try:
            session_data = self.get_session_data(session_id)
            if session_data:
                session_data['charts'] = charts
                session_data['updated_at'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
                self._save_session_data(session_id, session_data)
                logger.debug(f"Charts updated for session: {session_id}")
        except Exception as e:
            logger.error(f"Error updating session charts {session_id}: {e}")
    
    def cleanup_old_files(self):
        """清理过期的临时文件"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.cleanup_interval)
            cleaned_sessions = 0
            cleaned_charts = 0
            
            logger.info(f"Starting file cleanup, cutoff time: {cutoff_time.isoformat()}")
            
            # 清理上传目录
            uploads_dir = os.path.join(self.temp_dir, 'uploads')
            if os.path.exists(uploads_dir):
                for session_dir in os.listdir(uploads_dir):
                    session_path = os.path.join(uploads_dir, session_dir)
                    if os.path.isdir(session_path):
                        try:
                            # 检查目录的创建时间
                            dir_ctime = datetime.fromtimestamp(os.path.getctime(session_path))
                            if dir_ctime < cutoff_time:
                                shutil.rmtree(session_path)
                                cleaned_sessions += 1
                                logger.debug(f"Cleaned up upload directory: {session_dir} (created: {dir_ctime.isoformat()})")
                        except Exception as e:
                            logger.error(f"Error cleaning up session directory {session_dir}: {e}")
            
            # 清理图表数据文件
            charts_dir = os.path.join(self.temp_dir, 'charts')
            if os.path.exists(charts_dir):
                for chart_file in os.listdir(charts_dir):
                    if chart_file.endswith('.json'):
                        chart_path = os.path.join(charts_dir, chart_file)
                        try:
                            # 检查文件的创建时间
                            file_ctime = datetime.fromtimestamp(os.path.getctime(chart_path))
                            if file_ctime < cutoff_time:
                                os.remove(chart_path)
                                cleaned_charts += 1
                                logger.debug(f"Cleaned up chart file: {chart_file} (created: {file_ctime.isoformat()})")
                        except Exception as e:
                            logger.error(f"Error cleaning up chart file {chart_file}: {e}")
            
            if cleaned_sessions > 0 or cleaned_charts > 0:
                logger.info(f"File cleanup completed: {cleaned_sessions} sessions and {cleaned_charts} chart files removed")
            else:
                logger.debug("File cleanup completed: no files to clean")
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
    
    def delete_session(self, session_id: str):
        """
        删除指定会话的所有文件
        
        Args:
            session_id: 会话ID
        """
        try:
            # 删除上传文件目录
            session_upload_dir = os.path.join(self.temp_dir, 'uploads', session_id)
            if os.path.exists(session_upload_dir):
                shutil.rmtree(session_upload_dir)
                logger.debug(f"Deleted upload directory: {session_id}")
            
            # 删除图表数据文件
            session_chart_file = os.path.join(self.temp_dir, 'charts', f'{session_id}.json')
            if os.path.exists(session_chart_file):
                os.remove(session_chart_file)
                logger.debug(f"Deleted chart file: {session_id}")
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
    
    def get_file_stats(self) -> Dict[str, Any]:
        """
        获取文件存储统计信息
        
        Returns:
            统计信息
        """
        try:
            uploads_dir = os.path.join(self.temp_dir, 'uploads')
            charts_dir = os.path.join(self.temp_dir, 'charts')
            
            upload_count = len([d for d in os.listdir(uploads_dir) if os.path.isdir(os.path.join(uploads_dir, d))])
            chart_count = len([f for f in os.listdir(charts_dir) if f.endswith('.json')])
            
            return {
                'active_sessions': upload_count,
                'total_chart_files': chart_count,
                'temp_dir': self.temp_dir
            }
            
        except Exception as e:
            logger.error(f"Error getting file stats: {e}")
            return {
                'active_sessions': 0,
                'total_chart_files': 0,
                'temp_dir': self.temp_dir
            }