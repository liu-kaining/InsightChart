import json
import logging
from typing import Dict, List, Any, Optional
from ..adapters import BaseLLMAdapter, QwenAdapter, DeepSeekAdapter

logger = logging.getLogger(__name__)


class LLMService:
    """大模型服务统一接口"""
    
    def __init__(self, models_config: Dict[str, Any], app_config: Dict[str, Any], default_model: str = 'qwen'):
        """
        初始化LLM服务
        
        Args:
            models_config: 模型配置字典
            app_config: 应用配置字典
            default_model: 默认使用的模型名称
        """
        self.models_config = models_config
        self.app_config = app_config
        self.default_model = default_model
        self.adapters: Dict[str, BaseLLMAdapter] = {}
        self.timeout = app_config.get('timeout', 30)  # 获取超时配置
        
        # 初始化所有可用的适配器
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """初始化所有可用的适配器"""
        adapter_classes = {
            'qwen': QwenAdapter,
            'deepseek': DeepSeekAdapter
        }
        
        for model_name, config in self.models_config.items():
            if model_name in adapter_classes:
                try:
                    adapter_class = adapter_classes[model_name]
                    # 将timeout添加到config中
                    config_with_timeout = config.copy()
                    config_with_timeout['timeout'] = self.timeout
                    self.adapters[model_name] = adapter_class(config_with_timeout)
                    logger.info(f"Initialized {model_name} adapter successfully with timeout {self.timeout}s")
                except Exception as e:
                    logger.error(f"Failed to initialize {model_name} adapter: {e}")
    
    def get_adapter(self, model_name: Optional[str] = None) -> Optional[BaseLLMAdapter]:
        """
        获取指定的适配器
        
        Args:
            model_name: 模型名称，如果为None则使用默认模型
            
        Returns:
            模型适配器实例
        """
        if model_name is None:
            model_name = self.default_model
        
        adapter = self.adapters.get(model_name)
        if adapter is None:
            logger.error(f"Adapter {model_name} not found or not initialized")
        
        return adapter
    
    def generate_charts(self, data_summary: Dict[str, Any], model_name: str = None) -> List[Dict[str, Any]]:
        """
        生成图表配置
        
        Args:
            data_summary: 数据摘要信息
            model_name: 指定使用的模型，如果为None则使用默认模型
            
        Returns:
            图表配置列表
        """
        import time
        start_time = time.time()
        
        target_model = model_name or self.default_model
        logger.info(f"LLMService: Starting chart generation using model: {target_model}")
        
        adapter = self.get_adapter(target_model)
        if adapter is None:
            logger.error(f"LLMService: No available adapter for model: {target_model}")
            return []
        
        logger.info(f"LLMService: Found adapter for {target_model}, calling generate_charts...")
        
        try:
            # 记录开始时间
            generation_start = time.time()
            
            charts = adapter.generate_charts(data_summary)
            
            # 记录结束时间和处理详情
            generation_end = time.time()
            generation_time = generation_end - generation_start
            
            logger.info(f"LLMService: Adapter returned {len(charts) if charts else 0} charts")
            
            # 验证生成的图表配置
            logger.info("LLMService: Validating charts...")
            validated_charts = self._validate_charts(charts)
            
            # 记录处理详情
            self.last_used_model = target_model
            self.last_generation_details = {
                'model_used': target_model,
                'start_time': generation_start,
                'end_time': generation_end,
                'generation_time': generation_time,
                'total_time': time.time() - start_time,
                'input_tokens': getattr(adapter, 'last_input_tokens', 0),
                'output_tokens': getattr(adapter, 'last_output_tokens', 0),
                'total_tokens': getattr(adapter, 'last_input_tokens', 0) + getattr(adapter, 'last_output_tokens', 0),
                'prompt_used': getattr(adapter, 'last_prompt', ''),
                'charts_count': len(validated_charts),
                'timestamp': time.time()
            }
            
            logger.info(f"LLMService: Generated {len(validated_charts)} valid charts using {adapter.name}")
            logger.info(f"LLMService: Generation details - Time: {generation_time:.2f}s, Tokens: {self.last_generation_details['total_tokens']}")
            
            return validated_charts
            
        except Exception as e:
            logger.error(f"LLMService: Error generating charts with {adapter.name}: {e}")
            return []
    
    def _validate_charts(self, charts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证图表配置的有效性
        
        Args:
            charts: 图表配置列表
            
        Returns:
            验证通过的图表配置列表
        """
        validated_charts = []
        
        for chart in charts:
            if self._is_valid_chart(chart):
                validated_charts.append(chart)
            else:
                logger.warning(f"Invalid chart configuration: {chart.get('title', 'Unknown')}")
        
        return validated_charts
    
    def _is_valid_chart(self, chart: Dict[str, Any]) -> bool:
        """
        检查单个图表配置是否有效
        
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
        
        # 检查基本的ECharts结构
        option = chart['option']
        if 'series' not in option and 'xAxis' not in option and 'yAxis' not in option:
            logger.warning("Chart option missing required ECharts structure")
            return False
        
        return True
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """
        获取所有可用的模型信息
        
        Returns:
            模型信息列表
        """
        models = []
        for name, adapter in self.adapters.items():
            model_info = adapter.get_model_info()
            model_info['status'] = 'available'
            models.append(model_info)
        
        return models
    
    def health_check(self) -> Dict[str, Any]:
        """
        检查服务健康状态
        
        Returns:
            健康状态信息
        """
        status = {
            'service': 'healthy',
            'adapters': {}
        }
        
        for name, adapter in self.adapters.items():
            try:
                # 这里可以添加具体的健康检查逻辑
                status['adapters'][name] = 'healthy'
            except Exception as e:
                status['adapters'][name] = f'error: {str(e)}'
                status['service'] = 'degraded'
        
        return status