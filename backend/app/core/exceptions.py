import logging
from typing import Dict, Any, Optional
from flask import jsonify
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class ErrorCode:
    """错误码定义"""
    
    # 认证相关
    INVALID_PASSWORD = "AUTH_001"
    TOKEN_EXPIRED = "AUTH_002"
    TOKEN_INVALID = "AUTH_003"
    
    # 文件相关
    FILE_TOO_LARGE = "FILE_001"
    FILE_FORMAT_UNSUPPORTED = "FILE_002"
    FILE_CONTENT_INVALID = "FILE_003"
    FILE_UPLOAD_FAILED = "FILE_004"
    
    # 大模型相关
    LLM_API_ERROR = "LLM_001"
    LLM_RESPONSE_INVALID = "LLM_002"
    LLM_TIMEOUT = "LLM_003"
    
    # 系统相关
    INTERNAL_ERROR = "SYS_001"
    SERVICE_UNAVAILABLE = "SYS_002"
    INVALID_REQUEST = "SYS_003"


class AppException(Exception):
    """应用自定义异常基类"""
    
    def __init__(self, error_code: str, message: str, details: Optional[str] = None):
        """
        初始化异常
        
        Args:
            error_code: 错误码
            message: 错误消息
            details: 详细错误信息
        """
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(message)


class AuthException(AppException):
    """认证相关异常"""
    pass


class FileException(AppException):
    """文件处理相关异常"""
    pass


class LLMException(AppException):
    """大模型相关异常"""
    pass


class SystemException(AppException):
    """系统相关异常"""
    pass


def create_error_response(error_code: str, message: str, details: Optional[str] = None, status_code: int = 400) -> tuple:
    """
    创建标准错误响应
    
    Args:
        error_code: 错误码
        message: 错误消息
        details: 详细错误信息
        status_code: HTTP状态码
        
    Returns:
        (响应体, 状态码)
    """
    response = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message
        },
        'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat()
    }
    
    if details:
        response['error']['details'] = details
    
    return jsonify(response), status_code


def handle_app_exception(e: AppException) -> tuple:
    """
    处理应用自定义异常
    
    Args:
        e: 应用异常实例
        
    Returns:
        (响应体, 状态码)
    """
    logger.error(f"Application exception: {e.error_code} - {e.message}")
    
    # 根据异常类型确定状态码
    status_code = 400
    if isinstance(e, AuthException):
        status_code = 401
    elif isinstance(e, FileException):
        status_code = 400
    elif isinstance(e, LLMException):
        status_code = 503
    elif isinstance(e, SystemException):
        status_code = 500
    
    return create_error_response(e.error_code, e.message, e.details, status_code)


def handle_unexpected_exception(e: Exception) -> tuple:
    """
    处理未预期的异常
    
    Args:
        e: 异常实例
        
    Returns:
        (响应体, 状态码)
    """
    logger.error(f"Unexpected exception: {type(e).__name__}: {str(e)}", exc_info=True)
    
    return create_error_response(
        ErrorCode.INTERNAL_ERROR,
        "服务器内部错误",
        "请稍后重试或联系管理员",
        500
    )


def register_error_handlers(app):
    """
    注册全局错误处理器
    
    Args:
        app: Flask应用实例
    """
    
    @app.errorhandler(AppException)
    def handle_app_exception_handler(e):
        return handle_app_exception(e)
    
    @app.errorhandler(404)
    def handle_not_found(e):
        return create_error_response(
            ErrorCode.INVALID_REQUEST,
            "请求的资源不存在",
            status_code=404
        )
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return create_error_response(
            ErrorCode.INVALID_REQUEST,
            "请求方法不被允许",
            status_code=405
        )
    
    @app.errorhandler(500)
    def handle_internal_error(e):
        return handle_unexpected_exception(e)
    
    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        return handle_unexpected_exception(e)