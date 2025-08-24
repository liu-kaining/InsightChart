import jwt
import datetime
import logging
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, jsonify, current_app
from .config import get_config

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""
    
    def __init__(self):
        self.config = get_config()
        self.secret_key = self.config.get_security_config().get('token_secret')
        self.token_expires = self.config.get_security_config().get('token_expires', 3600)
        self.access_password = self.config.get_security_config().get('access_password')
        
        if not self.secret_key:
            raise ValueError("JWT secret key is not configured")
        if not self.access_password:
            raise ValueError("Access password is not configured")
    
    def verify_password(self, password: str) -> bool:
        """
        验证访问口令
        
        Args:
            password: 用户输入的口令
            
        Returns:
            是否验证通过
        """
        return password == self.access_password
    
    def generate_token(self) -> str:
        """
        生成JWT Token
        
        Returns:
            JWT Token字符串
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=self.token_expires),
                'iat': datetime.datetime.utcnow(),
                'sub': 'insight_chart_user'
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            logger.info("JWT token generated successfully")
            return token
            
        except Exception as e:
            logger.error(f"Error generating JWT token: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT Token
        
        Args:
            token: JWT Token字符串
            
        Returns:
            解码后的载荷，如果验证失败则返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            logger.error(f"Error verifying JWT token: {e}")
            return None
    
    def extract_token_from_header(self, authorization_header: str) -> Optional[str]:
        """
        从Authorization头中提取Token
        
        Args:
            authorization_header: Authorization头的值
            
        Returns:
            提取的Token，如果格式不正确则返回None
        """
        if not authorization_header:
            return None
        
        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        return parts[1]


# 全局认证服务实例
auth_service = None


def get_auth_service() -> AuthService:
    """获取全局认证服务实例"""
    global auth_service
    if auth_service is None:
        auth_service = AuthService()
    return auth_service


def require_auth(f):
    """
    认证装饰器，要求请求必须包含有效的JWT Token
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = get_auth_service()
        
        # 获取Authorization头
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTH_003',
                    'message': '缺少Authorization头'
                }
            }), 401
        
        # 提取Token
        token = auth.extract_token_from_header(authorization_header)
        if not token:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTH_003',
                    'message': 'Authorization头格式不正确'
                }
            }), 401
        
        # 验证Token
        payload = auth.verify_token(token)
        if not payload:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AUTH_002',
                    'message': 'Token无效或已过期'
                }
            }), 401
        
        # 将用户信息添加到请求上下文
        request.user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def login_required(f):
    """
    登录装饰器的别名，与require_auth功能相同
    """
    return require_auth(f)