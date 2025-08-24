from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
import json


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ChartTask:
    """图表生成任务模型"""
    
    def __init__(self, task_id: str = None):
        self.task_id = task_id or str(uuid.uuid4())
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress = 0  # 0-100
        self.current_step = ""
        self.data_summary: Optional[Dict[str, Any]] = None
        self.file_info: Optional[Dict[str, Any]] = None
        self.result: Optional[List[Dict[str, Any]]] = None
        self.error_message: Optional[str] = None
        self.model_used: Optional[str] = None
        self.total_attempts = 0
        self.current_attempt = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'current_step': self.current_step,
            'result': self.result,
            'error_message': self.error_message,
            'model_used': self.model_used,
            'total_attempts': self.total_attempts,
            'current_attempt': self.current_attempt,
            'data_summary': self.data_summary,
            'file_info': self.file_info
        }
    
    def start(self):
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.progress = 5
        self.current_step = "开始生成图表..."
    
    def update_progress(self, progress: int, step: str = ""):
        """更新进度"""
        self.progress = min(100, max(0, progress))
        if step:
            self.current_step = step
    
    def complete_success(self, result: List[Dict[str, Any]], model_used: str = None):
        """任务成功完成"""
        self.status = TaskStatus.SUCCESS
        self.completed_at = datetime.now()
        self.progress = 100
        self.current_step = "图表生成完成"
        self.result = result
        if model_used:
            self.model_used = model_used
    
    def complete_failed(self, error_message: str):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        self.current_step = f"生成失败: {error_message}"


class TaskManager:
    """任务管理器（内存存储）"""
    
    def __init__(self):
        self._tasks: Dict[str, ChartTask] = {}
    
    def create_task(self, data_summary: Dict[str, Any]) -> ChartTask:
        """创建新任务"""
        task = ChartTask()
        task.data_summary = data_summary
        self._tasks[task.task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[ChartTask]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def update_task(self, task: ChartTask):
        """更新任务（内存中已经是引用，这里主要用于扩展）"""
        self._tasks[task.task_id] = task
    
    def list_tasks(self, limit: int = 100) -> List[ChartTask]:
        """列出所有任务"""
        tasks = list(self._tasks.values())
        # 按创建时间倒序排列
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks[:limit]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        now = datetime.now()
        to_remove = []
        
        for task_id, task in self._tasks.items():
            age = (now - task.created_at).total_seconds() / 3600
            if age > max_age_hours:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._tasks[task_id]


# 全局任务管理器实例
task_manager = TaskManager()