import requests
import json
import logging
from typing import Dict, List, Any
from .base_llm import BaseLLMAdapter

logger = logging.getLogger(__name__)


class QwenAdapter(BaseLLMAdapter):
    """Qwen模型适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_charts(self, data_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成图表配置
        
        Args:
            data_summary: 数据摘要信息
            
        Returns:
            图表配置列表
        """
        try:
            prompt = self._build_prompt(data_summary)
            response = self._make_api_request(prompt)
            
            if not response:
                logger.error("Empty response from Qwen API")
                return []
            
            charts = self._parse_response(response)
            
            # 为每个图表添加唯一ID
            for i, chart in enumerate(charts):
                chart['id'] = f'qwen_chart_{i+1}'
            
            logger.info(f"Successfully generated {len(charts)} charts using Qwen")
            return charts
            
        except Exception as e:
            logger.error(f"Error generating charts with Qwen: {e}")
            return []
    
    def _make_api_request(self, prompt: str) -> str:
        """
        发起Qwen API请求
        
        Args:
            prompt: 用户提示词
            
        Returns:
            API响应内容
        """
        try:
            # Qwen API的消息格式
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # 构建请求体
            request_body = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }
            
            # 发起请求
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=request_body,
                timeout=self.timeout  # 使用配置的超时时间
            )
            
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return content.strip()
            else:
                logger.error(f"Unexpected Qwen API response format: {result}")
                return ""
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Qwen API request failed: {e}")
            return ""
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode Qwen API response: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error in Qwen API request: {e}")
            return ""
    
    def get_model_info(self) -> Dict[str, str]:
        """获取Qwen模型信息"""
        info = super().get_model_info()
        info['provider'] = 'Alibaba Cloud'
        info['type'] = 'qwen'
        return info