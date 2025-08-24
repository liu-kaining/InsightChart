import requests
import json
import logging
from typing import Dict, List, Any
from .base_llm import BaseLLMAdapter

logger = logging.getLogger(__name__)


class DeepSeekAdapter(BaseLLMAdapter):
    """DeepSeek模型适配器"""
    
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
            logger.info(f"DeepSeek: Starting chart generation for data with {data_summary.get('row_count', 0)} rows")
            
            prompt = self._build_prompt(data_summary)
            logger.info(f"DeepSeek: Built prompt, length: {len(prompt)}")
            
            logger.info("DeepSeek: Making API request...")
            response = self._make_api_request(prompt)
            logger.info(f"DeepSeek: API request completed, response length: {len(response) if response else 0}")
            
            if not response:
                logger.error("DeepSeek: Empty response from API")
                return []
            
            logger.info("DeepSeek: Parsing response...")
            charts = self._parse_response(response)
            logger.info(f"DeepSeek: Parsed {len(charts)} charts")
            
            # 为每个图表添加唯一ID
            for i, chart in enumerate(charts):
                chart['id'] = f'deepseek_chart_{i+1}'
            
            logger.info(f"DeepSeek: Successfully generated {len(charts)} charts")
            return charts
            
        except Exception as e:
            logger.error(f"DeepSeek: Error generating charts: {e}")
            return []
    
    def _make_api_request(self, prompt: str) -> str:
        """
        发起DeepSeek API请求
        
        Args:
            prompt: 用户提示词
            
        Returns:
            API响应内容
        """
        try:
            logger.info(f"DeepSeek API: Making request to {self.base_url}/chat/completions")
            
            # DeepSeek API的消息格式
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
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return content.strip()
            else:
                logger.error(f"DeepSeek API: Unexpected response format: {result}")
                return ""
                
        except requests.exceptions.Timeout as e:
            logger.error(f"DeepSeek API: Request timeout after {self.timeout}s: {e}")
            return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API: Request failed: {e}")
            return ""
        except json.JSONDecodeError as e:
            logger.error(f"DeepSeek API: Failed to decode response: {e}")
            return ""
        except Exception as e:
            logger.error(f"DeepSeek API: Unexpected error: {e}")
            return ""
    
    def get_model_info(self) -> Dict[str, str]:
        """获取DeepSeek模型信息"""
        info = super().get_model_info()
        info['provider'] = 'DeepSeek'
        info['type'] = 'deepseek'
        return info