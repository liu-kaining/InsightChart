import logging
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from ..core.config import get_config
from ..core.exceptions import LLMException, FileException, ErrorCode
from .llm_service import LLMService
from .file_service import FileService

logger = logging.getLogger(__name__)


class ChartService:
    """图表生成服务"""
    
    def __init__(self):
        """初始化图表服务"""
        self.config = get_config()
        
        # 初始化LLM服务
        models_config = self.config.models
        llm_config = self.config.get_llm_config()
        default_model = llm_config.get('default_model', 'qwen')
        
        self.llm_service = LLMService(models_config, llm_config, default_model)
        
        # 初始化文件服务
        self.file_service = FileService()
        
        # 配置参数
        self.min_charts = llm_config.get('min_charts', 5)
        self.max_charts = llm_config.get('max_charts', 5)
        self.timeout = llm_config.get('timeout', 30)
        self.retry_times = llm_config.get('retry_times', 3)
        
        # 记录最后使用的模型
        self.last_used_model = None
    
    def generate_charts_from_file(self, file, model_name: str = None) -> Dict[str, Any]:
        """
        从上传的文件生成图表
        
        Args:
            file: 上传的文件对象
            model_name: 指定使用的模型名称
            
        Returns:
            包含图表配置的结果字典
            
        Raises:
            FileException: 文件处理失败
            LLMException: 大模型调用失败
        """
        import time
        
        try:
            start_time = time.time()
            
            # 处理上传的文件
            logger.info("Processing uploaded file...")
            file_result = self.file_service.process_uploaded_file(file)
            
            session_id = file_result['session_id']
            data_summary = file_result['data_summary']
            
            # 生成图表配置
            logger.info(f"Generating charts for session {session_id}...")
            charts, retry_count = self._generate_charts_with_retry(data_summary, model_name)
            
            if not charts:
                raise LLMException(
                    ErrorCode.LLM_RESPONSE_INVALID,
                    "未能生成有效的图表配置",
                    "请检查数据格式或稍后重试"
                )
            
            # 限制和检查图表数量
            if len(charts) > self.max_charts:
                charts = charts[:self.max_charts]
                logger.info(f"Limited charts to {self.max_charts}")
            elif len(charts) < self.min_charts:
                logger.warning(f"Generated only {len(charts)} charts, expected minimum {self.min_charts}")
            
            # 保存图表到会话
            self.file_service.update_session_charts(session_id, charts)
            
            # 计算处理耗时
            generation_time = time.time() - start_time
            
            # 获取使用的模型信息
            used_model = model_name or self.llm_service.default_model
            adapter = self.llm_service.get_adapter(used_model)
            system_prompt = adapter.system_prompt if adapter else "未知"
            
            # 构建返回结果
            result = {
                'session_id': session_id,
                'charts': charts,
                'data_summary': {
                    'columns': data_summary['columns'],
                    'row_count': data_summary['row_count'],
                    'column_types': data_summary['column_types'],
                    'stats': data_summary.get('stats', {})
                },
                'file_info': file_result['file_info'],
                'processing_details': {
                    'model_used': used_model,
                    'prompt_used': system_prompt,
                    'generation_time': generation_time,
                    'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat(),
                    'retry_count': retry_count,
                    'max_retries': self.retry_times
                },
                'raw_data': {
                    'preview_data': data_summary.get('sample_data', [])[:50],  # 前50行数据
                    'total_rows': data_summary['row_count'],
                    'total_columns': len(data_summary['columns']),
                    'file_info': file_result['file_info']
                }
            }
            
            logger.info(f"Successfully generated {len(charts)} charts for session {session_id}")
            return result
            
        except (FileException, LLMException):
            raise
        except Exception as e:
            logger.error(f"Error generating charts from file: {e}")
            raise LLMException(ErrorCode.LLM_API_ERROR, f"图表生成失败: {str(e)}")
    
    def _generate_charts_with_retry(self, data_summary: Dict[str, Any], model_name: str = None) -> tuple[List[Dict[str, Any]], int]:
        """
        带重试机制和模型切换的图表生成
        
        Args:
            data_summary: 数据摘要
            model_name: 模型名称
            
        Returns:
            tuple[图表配置列表, 实际使用的重试次数]
        """
        last_error = None
        primary_model = model_name or self.llm_service.default_model
        backup_model = 'qwen' if primary_model == 'deepseek' else 'deepseek'
        
        # 先使用主要模型进行重试（减少重试次数，快速切换）
        max_primary_attempts = min(2, self.retry_times)  # 最多只试2次
        for attempt in range(max_primary_attempts):
            try:
                logger.info(f"Chart generation attempt {attempt + 1}/{max_primary_attempts} using {primary_model}")
                
                charts = self.llm_service.generate_charts(data_summary, primary_model)
                
                if charts and len(charts) >= self.min_charts:
                    logger.info(f"Generated {len(charts)} charts on attempt {attempt + 1} using {primary_model}")
                    return charts, attempt + 1
                elif charts and len(charts) >= 3:  # 如果有至少3个图表，也可以接受
                    logger.warning(f"Generated {len(charts)} charts on attempt {attempt + 1}, less than minimum {self.min_charts} but acceptable")
                    return charts, attempt + 1
                elif charts:
                    logger.warning(f"Generated only {len(charts)} charts on attempt {attempt + 1}, expected minimum {self.min_charts}")
                    # 如果图表数量太少，继续重试
                else:
                    logger.warning(f"No charts generated on attempt {attempt + 1} using {primary_model}")
                    
            except Exception as e:
                last_error = e
                logger.error(f"Chart generation attempt {attempt + 1} failed using {primary_model}: {e}")
                
                if attempt < max_primary_attempts - 1:
                    logger.info(f"Retrying with {primary_model}... ({attempt + 2}/{max_primary_attempts})")
        
        # 主要模型失败，尝试备用模型
        logger.warning(f"Primary model {primary_model} failed after {max_primary_attempts} attempts, switching to backup model {backup_model}")
        
        for attempt in range(self.retry_times):
            try:
                logger.info(f"Backup model attempt {attempt + 1}/{self.retry_times} using {backup_model}")
                
                charts = self.llm_service.generate_charts(data_summary, backup_model)
                
                if charts and len(charts) >= self.min_charts:
                    logger.info(f"Generated {len(charts)} charts on backup attempt {attempt + 1} using {backup_model}")
                    return charts, self.retry_times + attempt + 1
                elif charts:
                    logger.warning(f"Generated only {len(charts)} charts on backup attempt {attempt + 1}, expected minimum {self.min_charts}")
                    # 如果图表数量不足但不为空，返回这些图表
                    if attempt == self.retry_times - 1:  # 最后一次尝试
                        logger.info(f"Returning {len(charts)} charts from backup model as final attempt")
                        return charts, self.retry_times + attempt + 1
                else:
                    logger.warning(f"No charts generated on backup attempt {attempt + 1} using {backup_model}")
                    
            except Exception as e:
                last_error = e
                logger.error(f"Backup model attempt {attempt + 1} failed using {backup_model}: {e}")
                
                if attempt < self.retry_times - 1:
                    logger.info(f"Retrying with backup model {backup_model}... ({attempt + 2}/{self.retry_times})")
        
        # 所有重试都失败了
        total_attempts = self.retry_times * 2
        error_msg = f"图表生成失败，已尝试{primary_model}模型{self.retry_times}次和{backup_model}模型{self.retry_times}次"
        
        if last_error:
            error_msg += f"，最后错误：{str(last_error)}"
        
        logger.error(error_msg)
        raise LLMException(ErrorCode.LLM_RESPONSE_INVALID, error_msg)
    
    def generate_charts_with_progress(self, data_summary: Dict[str, Any], progress_callback=None, model_name=None) -> List[Dict[str, Any]]:
        """
        生成图表，支持进度回调（用于异步任务）
        
        Args:
            data_summary: 数据摘要
            progress_callback: 进度回调函数 callback(progress: int, step: str)
            model_name: 指定使用的模型名称（可选）
            
        Returns:
            图表配置列表
        """
        def update_progress(progress: int, step: str):
            if progress_callback:
                progress_callback(progress, step)
        
        try:
            update_progress(15, "开始生成图表...")
            
            last_error = None
            # 如果指定了模型，使用指定模型；否则使用默认模型
            primary_model = model_name if model_name else self.llm_service.default_model
            backup_model = 'qwen' if primary_model == 'deepseek' else 'deepseek'
            
            # 使用主要模型进行重试
            max_primary_attempts = min(2, self.retry_times)
            for attempt in range(max_primary_attempts):
                try:
                    progress = 20 + (30 * attempt // max_primary_attempts)
                    update_progress(progress, f"使用{primary_model}模型生成图表（第{attempt + 1}次尝试）...")
                    
                    logger.info(f"Chart generation attempt {attempt + 1}/{max_primary_attempts} using {primary_model}")
                    
                    charts = self.llm_service.generate_charts(data_summary, primary_model)
                    
                    if charts and len(charts) >= self.min_charts:
                        self.last_used_model = primary_model
                        update_progress(90, f"成功生成{len(charts)}个图表")
                        logger.info(f"Generated {len(charts)} charts on attempt {attempt + 1} using {primary_model}")
                        return charts
                    elif charts and len(charts) >= 3:
                        self.last_used_model = primary_model
                        update_progress(90, f"成功生成{len(charts)}个图表")
                        logger.warning(f"Generated {len(charts)} charts on attempt {attempt + 1}, less than minimum {self.min_charts} but acceptable")
                        return charts
                    elif charts:
                        logger.warning(f"Generated only {len(charts)} charts on attempt {attempt + 1}, expected minimum {self.min_charts}")
                    else:
                        logger.warning(f"No charts generated on attempt {attempt + 1} using {primary_model}")
                        
                except Exception as e:
                    last_error = e
                    logger.error(f"Chart generation attempt {attempt + 1} failed using {primary_model}: {e}")
                    
                    if attempt < max_primary_attempts - 1:
                        logger.info(f"Retrying with {primary_model}... ({attempt + 2}/{max_primary_attempts})")
            
            # 主要模型失败，尝试备用模型
            update_progress(55, f"{primary_model}模型失败，切换到{backup_model}模型...")
            logger.warning(f"Primary model {primary_model} failed after {max_primary_attempts} attempts, switching to backup model {backup_model}")
            
            for attempt in range(self.retry_times):
                try:
                    progress = 60 + (25 * attempt // self.retry_times)
                    update_progress(progress, f"使用{backup_model}模型生成图表（第{attempt + 1}次尝试）...")
                    
                    logger.info(f"Backup model attempt {attempt + 1}/{self.retry_times} using {backup_model}")
                    
                    charts = self.llm_service.generate_charts(data_summary, backup_model)
                    
                    if charts and len(charts) >= self.min_charts:
                        self.last_used_model = backup_model
                        update_progress(90, f"成功生成{len(charts)}个图表")
                        logger.info(f"Generated {len(charts)} charts on backup attempt {attempt + 1} using {backup_model}")
                        return charts
                    elif charts:
                        logger.warning(f"Generated only {len(charts)} charts on backup attempt {attempt + 1}, expected minimum {self.min_charts}")
                        if attempt == self.retry_times - 1:  # 最后一次尝试
                            self.last_used_model = backup_model
                            update_progress(90, f"成功生成{len(charts)}个图表")
                            logger.info(f"Returning {len(charts)} charts from backup model as final attempt")
                            return charts
                    else:
                        logger.warning(f"No charts generated on backup attempt {attempt + 1} using {backup_model}")
                        
                except Exception as e:
                    last_error = e
                    logger.error(f"Backup model attempt {attempt + 1} failed using {backup_model}: {e}")
                    
                    if attempt < self.retry_times - 1:
                        logger.info(f"Retrying with backup model {backup_model}... ({attempt + 2}/{self.retry_times})")
            
            # 所有重试都失败了
            total_attempts = self.retry_times * 2
            error_msg = f"图表生成失败，已尝试{primary_model}模型{max_primary_attempts}次和{backup_model}模型{self.retry_times}次"
            
            if last_error:
                error_msg += f"，最后错误：{str(last_error)}"
            
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            update_progress(0, f"生成失败: {str(e)}")
            raise
    
    def generate_charts(self, data_summary: Dict[str, Any], model_name: str = None) -> List[Dict[str, Any]]:
        """
        直接生成图表（用于异步任务）
        
        Args:
            data_summary: 数据摘要
            model_name: 指定的模型名称
            
        Returns:
            图表配置列表
        """
        charts, _ = self._generate_charts_with_retry(data_summary, model_name)
        return charts
    
    def get_session_charts(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的图表数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            图表数据，如果不存在则返回None
        """
        try:
            session_data = self.file_service.get_session_data(session_id)
            if not session_data:
                return None
            
            return {
                'session_id': session_id,
                'charts': session_data.get('charts', []),
                'data_summary': session_data.get('data_summary', {}),
                'file_info': session_data.get('file_info', {}),
                'timestamp': session_data.get('timestamp'),
                'updated_at': session_data.get('updated_at')
            }
            
        except Exception as e:
            logger.error(f"Error getting session charts {session_id}: {e}")
            return None
    
    def regenerate_charts(self, session_id: str, model_name: str = None) -> List[Dict[str, Any]]:
        """
        重新生成会话的图表
        
        Args:
            session_id: 会话ID
            model_name: 指定使用的模型名称
            
        Returns:
            新生成的图表配置列表
            
        Raises:
            LLMException: 生成失败
        """
        try:
            session_data = self.file_service.get_session_data(session_id)
            if not session_data:
                raise LLMException(
                    ErrorCode.LLM_API_ERROR,
                    "会话不存在或已过期",
                    f"Session ID: {session_id}"
                )
            
            data_summary = session_data.get('data_summary')
            if not data_summary:
                raise LLMException(
                    ErrorCode.LLM_API_ERROR,
                    "会话数据不完整",
                    "缺少数据摘要信息"
                )
            
            # 重新生成图表
            charts, retry_count = self._generate_charts_with_retry(data_summary, model_name)
            
            if not charts:
                raise LLMException(
                    ErrorCode.LLM_RESPONSE_INVALID,
                    "未能生成有效的图表配置"
                )
            
            # 限制图表数量
            if len(charts) > self.max_charts:
                charts = charts[:self.max_charts]
            
            # 更新会话数据
            self.file_service.update_session_charts(session_id, charts)
            
            logger.info(f"Regenerated {len(charts)} charts for session {session_id}")
            return charts
            
        except LLMException:
            raise
        except Exception as e:
            logger.error(f"Error regenerating charts for session {session_id}: {e}")
            raise LLMException(ErrorCode.LLM_API_ERROR, f"重新生成图表失败: {str(e)}")
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """
        获取可用的模型列表
        
        Returns:
            模型信息列表
        """
        return self.llm_service.get_available_models()
    
    def health_check(self) -> Dict[str, Any]:
        """
        检查服务健康状态
        
        Returns:
            健康状态信息
        """
        try:
            # 检查LLM服务状态
            llm_health = self.llm_service.health_check()
            
            # 检查文件服务状态
            file_stats = self.file_service.get_file_stats()
            
            # 整体状态
            overall_status = 'healthy' if llm_health['service'] == 'healthy' else 'degraded'
            
            return {
                'status': overall_status,
                'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat(),
                'llm_service': llm_health,
                'file_service': {
                    'status': 'healthy',
                    'stats': file_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def cleanup_old_sessions(self):
        """清理过期的会话数据"""
        try:
            self.file_service.cleanup_old_files()
            logger.info("Session cleanup completed")
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")