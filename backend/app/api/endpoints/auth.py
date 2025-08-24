from flask import Blueprint, request, jsonify
from ...core.auth import get_auth_service
from ...core.exceptions import AuthException, ErrorCode, create_error_response
from ...core.logger import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录（口令认证）
    
    请求体:
    {
        "password": "string"
    }
    
    响应:
    {
        "success": true,
        "data": {
            "token": "string",
            "expires_in": 3600
        },
        "message": "认证成功"
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return create_error_response(
                ErrorCode.INVALID_REQUEST,
                "请求体不能为空"
            )
        
        password = data.get('password')
        if not password:
            return create_error_response(
                ErrorCode.INVALID_REQUEST,
                "密码不能为空"
            )
        
        # 验证密码
        auth_service = get_auth_service()
        if not auth_service.verify_password(password):
            return create_error_response(
                ErrorCode.INVALID_PASSWORD,
                "口令错误，请重新输入",
                status_code=401
            )
        
        # 生成Token
        token = auth_service.generate_token()
        
        logger.info("User authentication successful")
        
        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'expires_in': auth_service.token_expires
            },
            'message': '认证成功'
        })
        
    except AuthException as e:
        return create_error_response(e.error_code, e.message, e.details, 401)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "登录过程中发生错误",
            status_code=500
        )


@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """
    验证Token有效性
    
    Headers:
    Authorization: Bearer <token>
    
    响应:
    {
        "success": true,
        "data": {
            "valid": true,
            "expires_at": "2025-08-24T11:00:00Z"
        }
    }
    """
    try:
        # 获取Authorization头
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            return create_error_response(
                ErrorCode.TOKEN_INVALID,
                "缺少Authorization头",
                status_code=401
            )
        
        # 提取Token
        auth_service = get_auth_service()
        token = auth_service.extract_token_from_header(authorization_header)
        if not token:
            return create_error_response(
                ErrorCode.TOKEN_INVALID,
                "Authorization头格式不正确",
                status_code=401
            )
        
        # 验证Token
        payload = auth_service.verify_token(token)
        if not payload:
            return create_error_response(
                ErrorCode.TOKEN_EXPIRED,
                "Token无效或已过期",
                status_code=401
            )
        
        # 返回验证结果
        return jsonify({
            'success': True,
            'data': {
                'valid': True,
                'expires_at': payload.get('exp'),
                'issued_at': payload.get('iat')
            }
        })
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "Token验证过程中发生错误",
            status_code=500
        )