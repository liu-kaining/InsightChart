from flask import Blueprint, jsonify, request
from ..core.auth import require_auth
from ..core.exceptions import create_error_response, ErrorCode
from ..services.cleanup_service import get_cleanup_service
from ..core.logger import get_logger

logger = get_logger(__name__)

cleanup_bp = Blueprint('cleanup', __name__, url_prefix='/api/cleanup')


@cleanup_bp.route('/status', methods=['GET'])
@require_auth
def get_cleanup_status():
    """
    获取文件清理服务状态
    
    Returns:
        JSON响应，包含清理服务状态信息
    """
    try:
        cleanup_service = get_cleanup_service()
        status = cleanup_service.get_status()
        
        return jsonify({
            'success': True,
            'data': status,
            'message': '清理服务状态获取成功'
        })
        
    except Exception as e:
        logger.error(f"Error getting cleanup status: {e}")
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "获取清理服务状态失败",
            str(e)
        )


@cleanup_bp.route('/force', methods=['POST'])
@require_auth
def force_cleanup():
    """
    手动触发文件清理
    
    Returns:
        JSON响应，包含清理结果
    """
    try:
        cleanup_service = get_cleanup_service()
        
        # 获取清理前的统计信息
        stats_before = cleanup_service.file_service.get_file_stats()
        
        # 执行清理
        cleanup_service.force_cleanup()
        
        # 获取清理后的统计信息
        stats_after = cleanup_service.file_service.get_file_stats()
        
        # 计算清理结果
        sessions_cleaned = stats_before['active_sessions'] - stats_after['active_sessions']
        charts_cleaned = stats_before['total_chart_files'] - stats_after['total_chart_files']
        
        logger.info(f"Manual cleanup completed: {sessions_cleaned} sessions, {charts_cleaned} charts removed")
        
        return jsonify({
            'success': True,
            'data': {
                'sessions_cleaned': sessions_cleaned,
                'charts_cleaned': charts_cleaned,
                'stats_before': stats_before,
                'stats_after': stats_after
            },
            'message': f'手动清理完成，删除了 {sessions_cleaned} 个会话和 {charts_cleaned} 个图表文件'
        })
        
    except Exception as e:
        logger.error(f"Error during force cleanup: {e}")
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "手动清理失败",
            str(e)
        )


@cleanup_bp.route('/session/<session_id>', methods=['DELETE'])
@require_auth
def cleanup_session(session_id: str):
    """
    立即清理指定会话
    
    Args:
        session_id: 会话ID
        
    Returns:
        JSON响应，包含清理结果
    """
    try:
        cleanup_service = get_cleanup_service()
        
        # 检查会话是否存在
        session_data = cleanup_service.file_service.get_session_data(session_id)
        if not session_data:
            return create_error_response(
                ErrorCode.RESOURCE_NOT_FOUND,
                f"会话 {session_id} 不存在"
            )
        
        # 执行清理
        cleanup_service.cleanup_session(session_id)
        
        logger.info(f"Session {session_id} cleaned up manually")
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'deleted': True
            },
            'message': f'会话 {session_id} 已成功清理'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {e}")
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            f"清理会话 {session_id} 失败",
            str(e)
        )


@cleanup_bp.route('/config', methods=['GET'])
@require_auth
def get_cleanup_config():
    """
    获取清理配置信息
    
    Returns:
        JSON响应，包含清理配置
    """
    try:
        cleanup_service = get_cleanup_service()
        
        config = {
            'cleanup_interval_seconds': cleanup_service.cleanup_interval,
            'cleanup_interval_minutes': cleanup_service.cleanup_interval / 60,
            'cleanup_interval_hours': cleanup_service.cleanup_interval / 3600,
            'auto_cleanup_enabled': cleanup_service.is_running(),
            'temp_directory': cleanup_service.file_service.temp_dir
        }
        
        return jsonify({
            'success': True,
            'data': config,
            'message': '清理配置获取成功'
        })
        
    except Exception as e:
        logger.error(f"Error getting cleanup config: {e}")
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "获取清理配置失败",
            str(e)
        )