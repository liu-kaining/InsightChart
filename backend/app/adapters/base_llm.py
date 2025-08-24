from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import json
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def safe_json_dumps(obj, **kwargs):
    """安全的JSON序列化，处理numpy/pandas数据类型"""
    def convert_types(obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj) 
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        elif pd.isna(obj):
            return None
        return obj
    
    return json.dumps(convert_types(obj), **kwargs)


class BaseLLMAdapter(ABC):
    """大模型基础适配器抽象类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM适配器
        
        Args:
            config: 模型配置
        """
        self.name = config.get('name', 'Unknown')
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.model_name = config.get('model_name')
        self.max_tokens = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.7)
        self.system_prompt = config.get('system_prompt', '')
        self.timeout = config.get('timeout', 60)
        
        # 添加token计数和提示词记录
        self.last_input_tokens = 0
        self.last_output_tokens = 0
        self.last_prompt = ''
        
        if not self.api_key:
            raise ValueError(f"API key not configured for {self.name}")
        
        logger.info(f"Initialized {self.name} adapter with model: {self.model_name}")
    
    @abstractmethod
    def generate_charts(self, data_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成图表配置
        
        Args:
            data_summary: 数据摘要信息
            
        Returns:
            图表配置列表
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(data_summary)
            self.last_prompt = prompt
            
            # 调用API
            response = self._make_api_request(prompt)
            
            # 解析响应
            charts = self._parse_response(response)
            
            # 记录token使用情况（如果API返回了token信息）
            if hasattr(self, '_extract_token_usage'):
                token_usage = self._extract_token_usage(response)
                self.last_input_tokens = token_usage.get('input_tokens', 0)
                self.last_output_tokens = token_usage.get('output_tokens', 0)
            
            return charts if charts else self._generate_fallback_charts()
            
        except Exception as e:
            logger.error(f"{self.name}: Error generating charts: {e}")
            return self._generate_fallback_charts()
    
    @abstractmethod
    def _make_api_request(self, prompt: str) -> str:
        """
        发起API请求
        
        Args:
            prompt: 用户提示词
            
        Returns:
            API响应内容
        """
        pass
    
    def validate_response(self, response: str) -> bool:
        """
        验证响应格式
        
        Args:
            response: API响应内容
            
        Returns:
            是否为有效的JSON格式
        """
        try:
            json.loads(response)
            return True
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON response from {self.name}: {response[:100]}...")
            return False
    
    def get_model_info(self) -> Dict[str, str]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            'name': self.name,
            'model_name': self.model_name,
            'base_url': self.base_url
        }
    
    def _build_prompt(self, data_summary: Dict[str, Any]) -> str:
        """
        构建提示词
        
        Args:
            data_summary: 数据摘要
            
        Returns:
            完整的提示词
        """
        columns = data_summary.get('columns', [])
        row_count = data_summary.get('row_count', 0)
        column_types = data_summary.get('column_types', {})
        sample_data = data_summary.get('sample_data', [])
        stats = data_summary.get('stats', {})
        
        # 构建数据背景描述
        data_background = f"这是一份包含{row_count}行数据的业务数据表，共有{len(columns)}个字段。"
        
        # 构建列信息描述
        column_info = []
        for col in columns:
            col_type = column_types.get(col, '未知')
            col_stats = stats.get(col, {})
            if isinstance(col_stats, dict) and 'count' in col_stats:
                count_info = f"(非空值: {col_stats['count']})"
            else:
                count_info = ""
            column_info.append(f"{col} ({col_type}) {count_info}")
        
        # 构建示例数据
        sample_rows = []
        for i, row in enumerate(sample_data[:3]):
            if isinstance(row, list) and len(row) == len(columns):
                row_data = {col: row[j] for j, col in enumerate(columns)}
                sample_rows.append(safe_json_dumps(row_data, ensure_ascii=False))
        
        prompt = f"""
## 数据信息

**数据背景:** {data_background}

**数据字段信息:**
{chr(10).join([f"- {info}" for info in column_info])}

**示例数据:**
{chr(10).join([f"行{i+1}: {row}" for i, row in enumerate(sample_rows)])}

**数据统计:**
- 总行数: {row_count}
- 字段数量: {len(columns)}
- 数据类型分布: {safe_json_dumps(column_types, ensure_ascii=False)}

## 分析要求

请基于以上数据信息，按照你的专业知识完成数据分析和图表生成。特别注意：

1. 深入理解数据的业务含义
2. 识别数据中的关键模式和趋势
3. 推荐最能体现数据价值的图表类型
4. 生成专业、美观、实用的ECharts配置

请严格按照系统提示词中的格式要求输出分析结果。
"""
        return prompt
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """
        解析API响应
        
        Args:
            response: API响应内容
            
        Returns:
            解析后的图表配置列表
        """
        try:
            # 预处理响应内容
            cleaned_response = self._clean_json_response(response)
            
            # 尝试直接解析JSON
            if cleaned_response.strip().startswith('['):
                parsed_data = json.loads(cleaned_response)
            else:
                # 如果响应包含其他内容，尝试提取JSON部分
                start_idx = cleaned_response.find('[')
                end_idx = cleaned_response.rfind(']') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = cleaned_response[start_idx:end_idx]
                    parsed_data = json.loads(json_str)
                else:
                    logger.error(f"Unable to find JSON array in response from {self.name}")
                    logger.error(f"Raw response content (first 500 chars): {response[:500]}...")
                    return self._generate_fallback_charts()
            
            # 处理解析后的数据
            charts = []
            for item in parsed_data:
                if isinstance(item, dict):
                    # 处理新格式（包含analysis字段）
                    if 'analysis' in item:
                        # 提取analysis信息并保存到metadata中
                        analysis = item.get('analysis', {})
                        chart = {
                            'title': item.get('title', '未命名图表'),
                            'type': item.get('type', 'bar'),
                            'option': item.get('option', {}),
                            'description': item.get('description', ''),
                            'metadata': {
                                'data_understanding': analysis.get('data_understanding', ''),
                                'core_insights': analysis.get('core_insights', []),
                                'chart_recommendations': analysis.get('chart_recommendations', []),
                                'chart_reasoning': item.get('description', '')
                            }
                        }
                    else:
                        # 处理旧格式
                        chart = {
                            'title': item.get('title', '未命名图表'),
                            'type': item.get('type', 'bar'),
                            'option': item.get('option', {}),
                            'description': item.get('description', '')
                        }
                    
                    # 验证图表配置的有效性
                    if self._validate_chart_config(chart):
                        charts.append(chart)
                    else:
                        logger.warning(f"Invalid chart configuration: {chart.get('title', 'Unknown')}")
            
            logger.info(f"Successfully parsed {len(charts)} charts from {self.name}")
            return charts if charts else self._generate_fallback_charts()
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from {self.name}: {e}")
            logger.error(f"Raw response content (first 500 chars): {response[:500]}...")
            # 尝试修复JSON格式
            return self._try_fix_json_and_parse(response)
        except Exception as e:
            logger.error(f"Unexpected error parsing response from {self.name}: {e}")
            return self._generate_fallback_charts()
    
    def _clean_json_response(self, response: str) -> str:
        """
        清理JSON响应内容
        
        Args:
            response: 原始响应内容
            
        Returns:
            清理后的响应内容
        """
        # 移除可能的markdown代码块标记（更全面的清理）
        import re
        # 处理 ```json...``` 格式
        response = re.sub(r'```json\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'```\s*$', '', response, flags=re.MULTILINE)
        response = re.sub(r'^```\s*', '', response, flags=re.MULTILINE)
        # 移除其他可能的代码块标记
        response = re.sub(r'```[a-zA-Z]*\s*', '', response)
        response = response.replace('```', '')
        
        # 移除前后空白字符
        response = response.strip()
        
        # 处理常见的格式问题（保留JSON结构需要的空格）
        response = re.sub(r'\n\s*', ' ', response)  # 将换行和后续空格替换为单个空格
        response = response.replace('\t', ' ')      # 将tab替换为空格
        
        # 移除多余的空格（但不影响JSON结构）
        response = re.sub(r'\s+', ' ', response)    # 将多个空格替换为单个空格
        
        return response
    
    def _try_fix_json_and_parse(self, response: str) -> List[Dict[str, Any]]:
        """
        尝试修复JSON格式错误并重新解析
        
        Args:
            response: 原始响应内容
            
        Returns:
            解析后的图表配置列表
        """
        logger.info(f"Attempting to fix JSON format errors for {self.name}")
        
        try:
            # 清理响应
            cleaned = self._clean_json_response(response)
            logger.info(f"Cleaned response (first 200 chars): {cleaned[:200]}...")
            
            # 先尝试解析为JSON数组
            charts = self._try_parse_json_array(cleaned)
            if charts:
                return charts
            
            # 如果数组解析失败，尝试解析多个JSON对象
            charts = self._try_parse_multiple_json_objects(cleaned)
            if charts:
                return charts
            
            # 如果以上都失败，尝试其他修复方法
            charts = self._try_parse_with_regex_fix(cleaned)
            if charts:
                return charts
                
        except Exception as fix_error:
            logger.error(f"Error during JSON fix attempt: {fix_error}")
        
        # 如果所有修复尝试都失败，返回后备图表
        logger.warning(f"All JSON parsing attempts failed for {self.name}, using fallback")
        return self._generate_fallback_charts()
    
    def _try_parse_json_array(self, json_str: str) -> List[Dict[str, Any]]:
        """
        尝试解析JSON数组，包含错误修复逻辑
        
        Args:
            json_str: 要解析的JSON字符串
            
        Returns:
            图表配置列表，失败时返回None
        """
        logger.info("Trying to parse JSON array")
        
        # 首先尝试直接解析
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                charts = []
                for item in data:
                    if isinstance(item, dict) and ('title' in item or 'type' in item):
                        chart = {
                            'title': item.get('title', '未命名图表'),
                            'type': item.get('type', 'bar'),
                            'option': item.get('option', self._get_default_chart_option()),
                            'description': item.get('description', '从JSON数组中解析的图表')
                        }
                        charts.append(chart)
                
                if charts:
                    logger.info(f"Successfully parsed {len(charts)} charts from JSON array")
                    return charts
        except json.JSONDecodeError as e:
            logger.warning(f"Direct JSON parsing failed: {e}")
        
        # 尝试修复常见的JSON格式问题
        try:
            # 修复缺少逗号的问题
            fixed_json = self._fix_json_format(json_str)
            data = json.loads(fixed_json)
            if isinstance(data, list):
                charts = []
                for item in data:
                    if isinstance(item, dict) and ('title' in item or 'type' in item):
                        chart = {
                            'title': item.get('title', '未命名图表'),
                            'type': item.get('type', 'bar'),
                            'option': item.get('option', self._get_default_chart_option()),
                            'description': item.get('description', '从修复后的JSON数组中解析的图表')
                        }
                        charts.append(chart)
                
                if charts:
                    logger.info(f"Successfully parsed {len(charts)} charts from fixed JSON array")
                    return charts
        except json.JSONDecodeError as fix_error:
            logger.error(f"Failed to parse fixed JSON array: {fix_error}")
            logger.error(f"JSON array content: {json_str[:200]}...")
        
        # 最后尝试：手动修复特定的错误模式
        try:
            # 针对Qwen常见的错误模式进行修复
            manual_fixed = self._manual_fix_qwen_json(json_str)
            data = json.loads(manual_fixed)
            if isinstance(data, list):
                charts = []
                for item in data:
                    if isinstance(item, dict) and ('title' in item or 'type' in item):
                        chart = {
                            'title': item.get('title', '未命名图表'),
                            'type': item.get('type', 'bar'),
                            'option': item.get('option', self._get_default_chart_option()),
                            'description': item.get('description', '从手动修复的JSON数组中解析的图表')
                        }
                        charts.append(chart)
                
                if charts:
                    logger.info(f"Successfully parsed {len(charts)} charts from manually fixed JSON array")
                    return charts
        except json.JSONDecodeError as manual_error:
            logger.error(f"Failed to parse manually fixed JSON array: {manual_error}")
        
        return None
    
    def _try_parse_multiple_json_objects(self, cleaned: str) -> List[Dict[str, Any]]:
        """
        尝试解析多个JSON对象（不是数组格式）
        
        Args:
            cleaned: 清理后的响应内容
            
        Returns:
            图表配置列表，失败时返回None
        """
        logger.info("Trying to parse multiple JSON objects")
        
        # 查找所有的JSON对象
        json_objects = []
        current_pos = 0
        
        while current_pos < len(cleaned):
            # 查找下一个'{'
            start_idx = cleaned.find('{', current_pos)
            if start_idx == -1:
                break
            
            # 找到对应的'}'
            brace_count = 0
            in_string = False
            escape_next = False
            end_idx = start_idx
            
            for i, char in enumerate(cleaned[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
            
            if brace_count == 0:
                json_str = cleaned[start_idx:end_idx]
                
                # 尝试解析这个JSON对象
                try:
                    obj = json.loads(json_str)
                    if isinstance(obj, dict):
                        json_objects.append(obj)
                        logger.info(f"Successfully parsed JSON object {len(json_objects)}: {obj.get('title', 'No title')}")
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON object at position {start_idx}: {e}")
                    logger.warning(f"Object content: {json_str[:100]}...")
                
                current_pos = end_idx
            else:
                # 如果找不到匹配的括号，移到下一个位置
                current_pos = start_idx + 1
        
        if json_objects:
            logger.info(f"Found {len(json_objects)} JSON objects")
            
            # 将JSON对象转换为图表配置
            charts = []
            for i, obj in enumerate(json_objects):
                if 'title' in obj or 'type' in obj:
                    chart = {
                        'title': obj.get('title', f'图表{i+1}'),
                        'type': obj.get('type', 'bar'),
                        'option': obj.get('option', self._get_default_chart_option()),
                        'description': obj.get('description', f'从多个JSON对象中解析的图表{i+1}')
                    }
                    charts.append(chart)
            
            return charts if charts else None
        
        logger.info("No valid JSON objects found")
        return None
    
    def _try_parse_with_regex_fix(self, cleaned: str) -> List[Dict[str, Any]]:
        """
        使用正则表达式修复并解析JSON
        
        Args:
            cleaned: 清理后的响应内容
            
        Returns:
            图表配置列表，失败时返回None
        """
        logger.info("Trying regex-based JSON fix")
        
        import re
        
        try:
            # 尝试修复常见的JSON问题
            
            # 1. 修复缺少逗号的问题
            fixed = re.sub(r'}\s*{', '},{', cleaned)
            
            # 2. 如果是多个对象，尝试包装成数组
            if not cleaned.strip().startswith('[') and not cleaned.strip().endswith(']'):
                # 检查是否有多个{}
                brace_count = cleaned.count('{')
                if brace_count > 1:
                    fixed = '[' + fixed + ']'
                    logger.info("Wrapped multiple objects in array brackets")
            
            # 3. 修复未闭合的引号
            # 这里可以添加更复杂的修复逻辑
            
            # 尝试解析修复后的JSON
            try:
                parsed_data = json.loads(fixed)
                logger.info(f"Successfully parsed with regex fix from {self.name}")
                
                # 确保是列表格式
                if isinstance(parsed_data, dict):
                    parsed_data = [parsed_data]
                elif not isinstance(parsed_data, list):
                    logger.warning(f"Unexpected data type after regex fix: {type(parsed_data)}")
                    return None
                
                # 处理解析后的数据
                charts = []
                for i, item in enumerate(parsed_data):
                    if isinstance(item, dict):
                        chart = {
                            'title': item.get('title', f'正则修复图表{i+1}'),
                            'type': item.get('type', 'bar'),
                            'option': item.get('option', self._get_default_chart_option()),
                            'description': item.get('description', f'通过正则修复获得的图表{i+1}')
                        }
                        charts.append(chart)
                
                return charts if charts else None
                
            except json.JSONDecodeError as fix_error:
                logger.error(f"Failed to parse regex-fixed JSON: {fix_error}")
                logger.error(f"Regex-fixed content: {fixed[:200]}...")
                
        except Exception as e:
            logger.error(f"Error during regex fix: {e}")
        
        return None
    
    def _get_default_chart_option(self) -> Dict[str, Any]:
        """
        获取默认图表配置
        
        Returns:
            默认图表配置
        """
        return {
            'title': {
                'text': '数据图表',
                'left': 'center'
            },
            'tooltip': {
                'trigger': 'axis'
            },
            'xAxis': {
                'type': 'category',
                'data': ['数据1', '数据2', '数据3']
            },
            'yAxis': {
                'type': 'value'
            },
            'series': [{
                'name': '数据系列',
                'type': 'bar',
                'data': [10, 20, 30],
                'itemStyle': {
                    'color': '#5470c6'
                }
            }]
        }
    
    def _validate_chart_config(self, chart: Dict[str, Any]) -> bool:
        """
        验证图表配置的有效性
        
        Args:
            chart: 图表配置
            
        Returns:
            是否有效
        """
        required_fields = ['title', 'type', 'option']
        
        # 检查必需字段
        for field in required_fields:
            if field not in chart:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # 检查option字段是否为有效的字典
        if not isinstance(chart['option'], dict):
            logger.warning("Chart option must be a dictionary")
            return False
        
        return True
    
    def _generate_fallback_charts(self) -> List[Dict[str, Any]]:
        """
        生成后备图表（当解析失败时）
        
        Returns:
            后备图表配置列表
        """
        logger.info(f"Generating fallback chart for {self.name}")
        
        fallback_chart = {
            'title': '数据视图',
            'type': 'bar',
            'option': {
                'title': {
                    'text': '数据视图',
                    'left': 'center'
                },
                'tooltip': {
                    'trigger': 'axis'
                },
                'xAxis': {
                    'type': 'category',
                    'data': ['类别1', '类别2', '类别3']
                },
                'yAxis': {
                    'type': 'value'
                },
                'series': [{
                    'name': '数据',
                    'type': 'bar',
                    'data': [10, 20, 30],
                    'itemStyle': {
                        'color': '#5470c6'
                    }
                }]
            },
            'description': '由于数据解析失败，生成的默认图表'
        }
        
        return [fallback_chart]

    def _fix_json_format(self, json_str: str) -> str:
        """
        修复常见的JSON格式问题
        
        Args:
            json_str: 原始JSON字符串
            
        Returns:
            修复后的JSON字符串
        """
        import re
        
        # 修复缺少逗号的问题：在 } 后面添加逗号（如果不是最后一个元素）
        # 更精确的匹配：在 } 后面如果不是逗号、空格+}、空格+] 就添加逗号
        fixed = re.sub(r'}(\s*)(?=[^,}\]])', r'},\1', json_str)
        
        # 修复多余的逗号
        fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
        
        # 修复缺少引号的键名
        fixed = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed)
        
        # 修复字符串中的转义问题
        fixed = re.sub(r'\\(?!["\\/bfnrt])', r'\\\\', fixed)
        
        # 修复缺少引号的字符串值
        fixed = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*[,}])', r': "\1"', fixed)
        
        logger.info("JSON format fixed with enhanced rules")
        return fixed

    def _manual_fix_qwen_json(self, json_str: str) -> str:
        """
        手动修复Qwen返回的特定JSON格式问题
        
        Args:
            json_str: 原始JSON字符串
            
        Returns:
            修复后的JSON字符串
        """
        # 针对Qwen常见的错误模式
        fixed = json_str
        
        # 修复缺少逗号的问题：在 } 和 "description" 之间添加逗号
        import re
        fixed = re.sub(r'}(\s*)"description"', r'},\1"description"', fixed)
        
        # 修复缺少逗号的问题：在 "description" 和 } 之间添加逗号
        fixed = re.sub(r'"description":\s*"[^"]*"(\s*)}', r'"description": "\1",\1}', fixed)
        
        # 修复缺少逗号的问题：在 } 和 { 之间添加逗号
        fixed = re.sub(r'}(\s*){', r'},\1{', fixed)
        
        # 修复多余的逗号
        fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
        
        logger.info("Manual Qwen JSON fix applied")
        return fixed