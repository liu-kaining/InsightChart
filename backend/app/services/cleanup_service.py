import logging
import threading
import time
from typing import Optional
from datetime import datetime, timezone, timedelta
from ..core.config import get_config
from .file_service import FileService

logger = logging.getLogger(__name__)


class CleanupService:
    """文件清理服务 - 负责定期清理临时文件"""
    
    def __init__(self):
        """初始化清理服务"""
        self.config = get_config()
        file_config = self.config.get_file_config()
        
        # 清理间隔（秒）
        self.cleanup_interval = file_config.get('cleanup_interval', 300)  # 默认5分钟
        
        # 文件服务实例
        self.file_service = FileService()
        
        # 清理线程相关
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        
        logger.info(f"CleanupService initialized with interval: {self.cleanup_interval}s ({self.cleanup_interval/60:.1f}min)")
    
    def start(self):
        """启动后台清理任务"""
        if self._running:
            logger.warning("Cleanup service is already running")
            return
        
        self._stop_event.clear()
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        self._running = True
        
        logger.info("File cleanup service started")
    
    def stop(self):
        """停止后台清理任务"""
        if not self._running:
            logger.warning("Cleanup service is not running")
            return
        
        self._stop_event.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        
        self._running = False
        logger.info("File cleanup service stopped")
    
    def _cleanup_worker(self):
        """清理工作线程"""
        logger.info("Cleanup worker thread started")
        
        while not self._stop_event.is_set():
            try:
                # 执行清理
                self._perform_cleanup()
                
                # 等待下次清理时间，或者接收停止信号
                if self._stop_event.wait(timeout=self.cleanup_interval):
                    break  # 收到停止信号
                    
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                # 出错后等待较短时间再重试
                if self._stop_event.wait(timeout=30):
                    break
        
        logger.info("Cleanup worker thread stopped")
    
    def _perform_cleanup(self):
        """执行清理操作"""
        try:
            start_time = time.time()
            
            # 获取清理前的统计信息
            stats_before = self.file_service.get_file_stats()
            
            # 执行清理
            self.file_service.cleanup_old_files()
            
            # 获取清理后的统计信息
            stats_after = self.file_service.get_file_stats()
            
            cleanup_time = time.time() - start_time
            
            # 计算清理的文件数量
            sessions_cleaned = stats_before['active_sessions'] - stats_after['active_sessions']
            charts_cleaned = stats_before['total_chart_files'] - stats_after['total_chart_files']
            
            if sessions_cleaned > 0 or charts_cleaned > 0:
                logger.info(
                    f"Cleanup completed: {sessions_cleaned} sessions, {charts_cleaned} chart files "
                    f"removed in {cleanup_time:.2f}s"
                )
            else:
                logger.debug(f"Cleanup completed: no files to clean (took {cleanup_time:.2f}s)")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def force_cleanup(self):
        """强制执行一次清理"""
        logger.info("Force cleanup triggered")
        self._perform_cleanup()
    
    def cleanup_session(self, session_id: str):
        """立即清理指定会话"""
        try:
            logger.info(f"Immediate cleanup for session: {session_id}")
            self.file_service.delete_session(session_id)
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    
    def get_status(self) -> dict:
        """获取清理服务状态"""
        return {
            'running': self._running,
            'cleanup_interval': self.cleanup_interval,
            'cleanup_interval_minutes': self.cleanup_interval / 60,
            'thread_alive': self._cleanup_thread.is_alive() if self._cleanup_thread else False,
            'file_stats': self.file_service.get_file_stats()
        }
    
    def is_running(self) -> bool:
        """检查服务是否正在运行"""
        return self._running


# 全局清理服务实例
_cleanup_service_instance: Optional[CleanupService] = None


def get_cleanup_service() -> CleanupService:
    """获取清理服务单例"""
    global _cleanup_service_instance
    if _cleanup_service_instance is None:
        _cleanup_service_instance = CleanupService()
    return _cleanup_service_instance


def start_cleanup_service():
    """启动清理服务"""
    service = get_cleanup_service()
    service.start()


def stop_cleanup_service():
    """停止清理服务"""
    service = get_cleanup_service()
    service.stop()