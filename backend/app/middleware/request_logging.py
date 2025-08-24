"""
请求日志中间件

记录所有API请求的详细信息，包括：
- 请求方法、路径、参数
- 请求头信息（过滤敏感信息）
- 请求体大小
- 响应状态码
- 处理时间
- 客户端IP地址
- 用户代理信息
"""

import time
import uuid
import json
from typing import Dict, Any, Optional
from flask import Flask, request, g
from werkzeug.exceptions import HTTPException
from ..core.logger import get_request_logger, get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    """请求日志中间件"""
    
    def __init__(self, app: Optional[Flask] = None):
        """
        初始化请求日志中间件
        
        Args:
            app: Flask应用实例
        """
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        初始化应用
        
        Args:
            app: Flask应用实例
        """
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
    
    def before_request(self):
        """请求前处理"""
        # 生成请求ID
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()
        
        # 获取请求信息
        request_info = self._extract_request_info()
        
        # 创建请求日志记录器
        g.request_logger = get_request_logger(g.request_id)
        
        # 记录请求开始
        g.request_logger.info(
            f"Request started: {request.method} {request.path}",
            extra=request_info
        )
    
    def after_request(self, response):
        """请求后处理"""
        try:
            # 计算处理时间
            duration = (time.time() - g.start_time) * 1000  # 转换为毫秒
            
            # 获取响应信息
            response_info = self._extract_response_info(response, duration)
            
            # 记录请求完成
            if response.status_code >= 400:
                g.request_logger.warning(
                    f"Request completed with error: {request.method} {request.path} -> {response.status_code}",
                    extra=response_info
                )
            else:
                g.request_logger.info(
                    f"Request completed successfully: {request.method} {request.path} -> {response.status_code}",
                    extra=response_info
                )
            
            # 在响应头中添加请求ID，便于跟踪
            response.headers['X-Request-ID'] = g.request_id
            
        except Exception as e:
            logger.error(f"Error in after_request middleware: {e}", exc_info=True)
        
        return response
    
    def teardown_request(self, error=None):
        """请求结束处理"""
        if error:
            try:
                duration = (time.time() - g.start_time) * 1000 if hasattr(g, 'start_time') else 0
                
                # 记录异常信息
                if hasattr(g, 'request_logger'):
                    g.request_logger.error(
                        f"Request failed with exception: {request.method} {request.path}",
                        extra={
                            'duration_ms': duration,
                            'exception_type': type(error).__name__,
                            'exception_message': str(error)
                        },
                        exc_info=True
                    )
                else:
                    logger.error(
                        f"Request failed with exception: {request.method} {request.path} - {error}",
                        exc_info=True
                    )
            except Exception as e:
                logger.error(f"Error in teardown_request middleware: {e}", exc_info=True)
    
    def _extract_request_info(self) -> Dict[str, Any]:
        """提取请求信息"""
        try:
            # 基础请求信息
            info = {
                'method': request.method,
                'path': request.path,
                'full_path': request.full_path,
                'url': request.url,
                'remote_addr': self._get_client_ip(),
                'user_agent': request.headers.get('User-Agent', ''),
                'content_type': request.content_type,
                'content_length': request.content_length or 0,
            }
            
            # 查询参数
            if request.args:
                info['query_params'] = dict(request.args)
            
            # 请求头（过滤敏感信息）
            headers = {}
            for key, value in request.headers:
                # 过滤敏感头信息
                if key.lower() not in ['authorization', 'cookie', 'x-api-key']:
                    headers[key] = value
                else:
                    headers[key] = '[FILTERED]'
            info['headers'] = headers
            
            # 表单数据（不记录文件内容）
            if request.form:
                form_data = {}
                for key, value in request.form.items():
                    if len(str(value)) > 1000:  # 限制长度
                        form_data[key] = f"[TRUNCATED: {len(str(value))} chars]"
                    else:
                        form_data[key] = value
                info['form_data'] = form_data
            
            # 文件上传信息
            if request.files:
                files_info = {}
                for key, file in request.files.items():
                    files_info[key] = {
                        'filename': file.filename,
                        'content_type': file.content_type,
                        'content_length': file.content_length
                    }
                info['files'] = files_info
            
            return info
            
        except Exception as e:
            logger.error(f"Error extracting request info: {e}", exc_info=True)
            return {'error': 'Failed to extract request info'}
    
    def _extract_response_info(self, response, duration: float) -> Dict[str, Any]:
        """提取响应信息"""
        try:
            info = {
                'status_code': response.status_code,
                'status': response.status,
                'duration_ms': round(duration, 2),
                'content_type': response.content_type,
                'content_length': response.content_length or 0,
            }
            
            # 响应头（过滤敏感信息）
            headers = {}
            for key, value in response.headers:
                if key.lower() not in ['set-cookie']:
                    headers[key] = value
                else:
                    headers[key] = '[FILTERED]'
            info['response_headers'] = headers
            
            return info
            
        except Exception as e:
            logger.error(f"Error extracting response info: {e}", exc_info=True)
            return {'error': 'Failed to extract response info', 'duration_ms': duration}
    
    def _get_client_ip(self) -> str:
        """获取客户端真实IP地址"""
        # 尝试从代理头获取真实IP
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        elif request.headers.get('X-Forwarded-Host'):
            return request.headers.get('X-Forwarded-Host')
        else:
            return request.remote_addr or 'unknown'


def init_request_logging(app: Flask):
    """
    初始化请求日志中间件
    
    Args:
        app: Flask应用实例
    """
    middleware = RequestLoggingMiddleware(app)
    logger.info("Request logging middleware initialized")
    return middleware