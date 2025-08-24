import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Any, Optional
from app.models.task import ChartTask, TaskStatus, task_manager
from app.services.chart_service import ChartService

logger = logging.getLogger(__name__)


class AsyncTaskProcessor:
    """异步任务处理器"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.chart_service = ChartService()
        self.running_tasks: Dict[str, Future] = {}
        self._lock = threading.Lock()
        
        # 启动后台清理线程
        self._start_cleanup_thread()
    
    def submit_task(self, task: ChartTask) -> bool:
        """提交任务到后台处理"""
        try:
            with self._lock:
                if task.task_id in self.running_tasks:
                    logger.warning(f"Task {task.task_id} is already running")
                    return False
                
                # 提交任务到线程池
                future = self.executor.submit(self._process_task, task)
                self.running_tasks[task.task_id] = future
                
                logger.info(f"Task {task.task_id} submitted for async processing")
                return True
                
        except Exception as e:
            logger.error(f"Failed to submit task {task.task_id}: {e}")
            task.complete_failed(f"Failed to submit task: {str(e)}")
            return False
    
    def _process_task(self, task: ChartTask):
        """处理单个任务（在后台线程中执行）"""
        try:
            logger.info(f"Starting async processing for task {task.task_id}")
            
            # 标记任务开始
            task.start()
            
            # 执行图表生成
            task.update_progress(10, "准备生成图表...")
            
            # 调用原有的图表生成服务
            charts = self.chart_service.generate_charts_with_progress(
                task.data_summary, 
                progress_callback=lambda p, s: task.update_progress(p, s),
                model_name=task.model_used  # 传递用户选择的模型
            )
            
            if charts:
                # 任务成功
                task.update_progress(95, "图表生成完成，正在保存...")
                task.complete_success(charts, self.chart_service.last_used_model)
                
                # 保存结果到文件系统
                try:
                    from .file_service import FileService
                    file_service = FileService()
                    file_service._save_session_data(task.task_id, {
                        'charts': charts,
                        'model_used': self.chart_service.last_used_model,
                        'created_at': task.created_at.isoformat(),
                        'completed_at': task.completed_at.isoformat(),
                        'data_summary': task.data_summary,
                        'file_info': task.file_info
                    })
                    logger.info(f"Task {task.task_id} results saved to file system")
                except Exception as e:
                    logger.error(f"Failed to save task {task.task_id} results to file system: {e}")
                
                logger.info(f"Task {task.task_id} completed successfully with {len(charts)} charts")
            else:
                # 任务失败
                task.update_progress(0, "未能生成任何图表")
                task.complete_failed("未能生成任何图表")
                logger.error(f"Task {task.task_id} failed: no charts generated")
                
        except Exception as e:
            logger.error(f"Task {task.task_id} failed with exception: {e}")
            task.update_progress(0, f"生成失败: {str(e)}")
            task.complete_failed(str(e))
        
        finally:
            # 从运行列表中移除
            with self._lock:
                self.running_tasks.pop(task.task_id, None)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = task_manager.get_task(task_id)
        if not task:
            return None
        
        return task.to_dict()
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            future = self.running_tasks.get(task_id)
            if future and not future.done():
                future.cancel()
                self.running_tasks.pop(task_id, None)
                
                # 更新任务状态
                task = task_manager.get_task(task_id)
                if task:
                    task.complete_failed("任务被取消")
                
                logger.info(f"Task {task_id} cancelled")
                return True
            
        return False
    
    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_worker():
            while True:
                try:
                    # 每30分钟清理一次
                    time.sleep(1800)
                    
                    # 清理完成的Future对象
                    with self._lock:
                        completed_tasks = [
                            task_id for task_id, future in self.running_tasks.items()
                            if future.done()
                        ]
                        for task_id in completed_tasks:
                            self.running_tasks.pop(task_id, None)
                    
                    # 清理旧任务
                    task_manager.cleanup_old_tasks(max_age_hours=48)
                    
                    if completed_tasks:
                        logger.info(f"Cleaned up {len(completed_tasks)} completed tasks")
                        
                except Exception as e:
                    logger.error(f"Cleanup thread error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Async task cleanup thread started")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        with self._lock:
            running_count = len(self.running_tasks)
        
        total_tasks = len(task_manager.list_tasks(1000))
        
        return {
            'max_workers': self.max_workers,
            'running_tasks': running_count,
            'total_tasks': total_tasks,
            'available_workers': self.max_workers - running_count
        }


# 全局异步任务处理器实例
async_processor = AsyncTaskProcessor(max_workers=3)