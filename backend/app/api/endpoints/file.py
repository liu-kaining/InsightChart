import logging
from flask import Blueprint, request, jsonify
from ...core.auth import require_auth
from ...core.exceptions import FileException, LLMException, create_error_response, ErrorCode
from ...services.chart_service import ChartService
from ...services.async_processor import async_processor
from ...models.task import task_manager
import time
from datetime import datetime
import uuid
import zipfile
import io
import base64
from PIL import Image
import json

logger = logging.getLogger(__name__)

file_bp = Blueprint('file', __name__, url_prefix='/api/file')

# 初始化图表服务
chart_service = ChartService()


@file_bp.route('/upload', methods=['POST'])
@require_auth
def upload_file():
    """
    上传文件并生成图表（同步处理）
    
    Headers:
    Authorization: Bearer <token>
    Content-Type: multipart/form-data
    
    表单参数:
    file: 要上传的文件
    model: 可选，指定使用的模型 (qwen/deepseek)
    
    响应:
    {
        "success": true,
        "data": {
            "charts": [...],
            "model_used": "qwen",
            "file_info": {...},
            "data_summary": {...},
            "processing_time": 12.5
        }
    }
    """
    try:
        if 'file' not in request.files:
            return create_error_response(
                ErrorCode.INVALID_REQUEST,
                "未找到文件"
            )
        
        file = request.files['file']
        if not file or file.filename == '':
            return create_error_response(
                ErrorCode.INVALID_REQUEST,
                "未选择文件"
            )
        
        # 获取可选的模型参数
        model_name = request.form.get('model')
        
        logger.info(f"Processing file upload (sync): {file.filename}, model: {model_name}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 处理文件，获取数据摘要
        file_result = chart_service.file_service.process_uploaded_file(file)
        data_summary = file_result['data_summary']
        
        # 直接生成图表（同步处理）
        charts = chart_service.generate_charts_with_progress(
            data_summary,
            progress_callback=None,  # 同步处理不需要进度回调
            model_name=model_name
        )
        
        if not charts:
            return create_error_response(
                ErrorCode.INTERNAL_ERROR,
                "图表生成失败，请检查数据格式或稍后重试"
            )
        
        # 计算处理时间
        processing_time = round(time.time() - start_time, 2)
        
        # 获取详细的处理信息
        processing_details = {
            'model_used': chart_service.last_used_model,
            'generation_time': processing_time,
            'timestamp': datetime.now().isoformat(),
            'prompt_used': getattr(chart_service.llm_service, 'last_generation_details', {}).get('prompt_used', ''),
            'input_tokens': getattr(chart_service.llm_service, 'last_generation_details', {}).get('input_tokens', 0),
            'output_tokens': getattr(chart_service.llm_service, 'last_generation_details', {}).get('output_tokens', 0),
            'total_tokens': getattr(chart_service.llm_service, 'last_generation_details', {}).get('total_tokens', 0),
            'start_time': getattr(chart_service.llm_service, 'last_generation_details', {}).get('start_time', 0),
            'end_time': getattr(chart_service.llm_service, 'last_generation_details', {}).get('end_time', 0)
        }
        
        # 保存结果到文件系统（可选）
        try:
            session_id = str(uuid.uuid4())
            
            # 获取原始数据用于预览
            raw_data = {
                'preview_data': data_summary.get('preview_data', []),
                'total_rows': data_summary.get('row_count', 0),
                'total_columns': len(data_summary.get('columns', [])),
                'file_info': file_result['file_info']
            }
            
            chart_service.file_service._save_session_data(session_id, {
                'charts': charts,
                'model_used': chart_service.last_used_model,
                'created_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat(),
                'data_summary': data_summary,
                'file_info': file_result['file_info'],
                'processing_time': processing_time,
                'raw_data': raw_data,
                'processing_details': processing_details
            })
            logger.info(f"Results saved to session: {session_id}")
        except Exception as e:
            logger.warning(f"Failed to save session data: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'charts': charts,
                'model_used': chart_service.last_used_model,
                'file_info': file_result['file_info'],
                'data_summary': data_summary,
                'processing_time': processing_time,
                'session_id': session_id if 'session_id' in locals() else None,
                'raw_data': raw_data if 'raw_data' in locals() else None,
                'processing_details': processing_details
            },
            'message': f'图表生成完成，共生成 {len(charts)} 个图表，耗时 {processing_time} 秒'
        })
        
    except FileException as e:
        return create_error_response(e.error_code, e.message, e.details)
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "文件处理过程中发生错误",
            status_code=500
        )


# 删除异步任务相关的端点，只保留同步上传和会话获取功能

@file_bp.route('/session/<session_id>', methods=['GET'])
@require_auth
def get_session_charts(session_id):
    """
    获取会话的图表数据
    
    Headers:
    Authorization: Bearer <token>
    
    路径参数:
    session_id: 会话ID
    
    响应:
    {
        "success": true,
        "data": {
            "session_id": "string",
            "charts": [...],
            "data_summary": {...},
            "timestamp": "2025-08-24T10:00:00Z"
        }
    }
    """
    try:
        result = chart_service.get_session_charts(session_id)
        
        if not result:
            return create_error_response(
                ErrorCode.INVALID_REQUEST,
                "会话不存在或已过期",
                f"Session ID: {session_id}",
                404
            )
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Get session charts error: {e}")
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "获取会话数据时发生错误",
            status_code=500
        )


@file_bp.route('/download-charts-zip', methods=['POST'])
@require_auth
def download_charts_zip():
    """
    批量下载图表为ZIP文件
    
    Headers:
    Authorization: Bearer <token>
    
    请求体:
    {
        "charts": [
            {
                "id": "chart_1",
                "title": "图表标题",
                "type": "bar",
                "option": { ECharts配置对象 }
            }
        ]
    }
    
    响应:
    返回ZIP文件的二进制数据
    """
    try:
        data = request.get_json()
        if not data or 'charts' not in data:
            return create_error_response(
                ErrorCode.INVALID_REQUEST,
                "缺少图表数据"
            )
        
        charts = data['charts']
        if not charts:
            return create_error_response(
                ErrorCode.INVALID_REQUEST,
                "图表列表为空"
            )
        
        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, chart in enumerate(charts):
                try:
                    # 这里需要实现图表渲染逻辑
                    # 暂时保存为JSON文件
                    chart_data = {
                        'title': chart.get('title', f'图表{i+1}'),
                        'type': chart.get('type', 'unknown'),
                        'option': chart.get('option', {}),
                        'description': chart.get('description', '')
                    }
                    
                    # 保存为JSON文件
                    json_content = json.dumps(chart_data, ensure_ascii=False, indent=2)
                    filename = f"{chart_data['title']}-{i+1}.json"
                    zip_file.writestr(filename, json_content.encode('utf-8'))
                    
                except Exception as e:
                    logger.error(f"Failed to add chart {i} to ZIP: {e}")
                    continue
        
        zip_buffer.seek(0)
        
        # 返回ZIP文件
        from flask import send_file
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'图表集合-{datetime.now().strftime("%Y%m%d-%H%M%S")}.zip'
        )
        
    except Exception as e:
        logger.error(f"Download charts ZIP error: {e}")
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "生成ZIP文件失败",
            status_code=500
        )