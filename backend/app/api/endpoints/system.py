import logging
from flask import Blueprint, jsonify
from datetime import datetime, timezone, timedelta
from ...services.chart_service import ChartService

logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__, url_prefix='/api/system')

# 初始化图表服务
chart_service = ChartService()


@system_bp.route('/health', methods=['GET'])
def health_check():
    """
    系统健康检查
    
    响应:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "timestamp": "2025-08-24T10:00:00Z",
            "services": {
                "llm_service": {...},
                "file_service": {...}
            }
        }
    }
    """
    try:
        # 获取服务健康状态
        health_info = chart_service.health_check()
        
        # 添加时间戳
        health_info['timestamp'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
        
        return jsonify({
            'success': True,
            'data': health_info
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'success': False,
            'data': {
                'status': 'error',
                'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat(),
                'error': str(e)
            }
        }), 503


@system_bp.route('/models', methods=['GET'])
def get_available_models():
    """
    获取可用的模型列表
    
    响应:
    {
        "success": true,
        "data": {
            "models": [
                {
                    "name": "Qwen",
                    "type": "qwen",
                    "provider": "Alibaba Cloud",
                    "status": "available"
                }
            ]
        }
    }
    """
    try:
        models = chart_service.get_available_models()
        
        return jsonify({
            'success': True,
            'data': {
                'models': models
            }
        })
        
    except Exception as e:
        logger.error(f"Get models error: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYS_001',
                'message': '获取模型列表失败',
                'details': str(e)
            }
        }), 500


@system_bp.route('/info', methods=['GET'])
def get_system_info():
    """
    获取系统信息
    
    响应:
    {
        "success": true,
        "data": {
            "name": "InsightChart AI",
            "version": "1.0.0",
            "description": "智能图表生成器"
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'name': 'InsightChart AI',
                'version': '1.0.0',
                'description': '智能图表生成器',
                'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Get system info error: {e}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYS_001',
                'message': '获取系统信息失败',
                'details': str(e)
            }
        }), 500