"""
日志配置管理模块

提供完善的日志记录功能，包括：
- 控制台日志输出
- 文件日志记录
- 日志文件轮转
- 结构化JSON日志
- 不同级别的日志分离
- 错误日志邮件告警(可扩展)
"""

import os
import sys
import json
import logging
import logging.handlers
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON格式化器，输出结构化日志"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON格式"""
        # 基础日志信息
        log_entry = {
            'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # 添加额外字段
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录并添加颜色"""
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 格式化基础信息
        formatted = super().format(record)
        
        # 添加颜色
        return f"{color}{formatted}{reset}"


class LoggerManager:
    """日志管理器"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        初始化日志管理器
        
        Args:
            config_dict: 日志配置字典
        """
        self.config = config_dict or self._get_default_config()
        self.log_dir = Path(self.config.get('log_dir', './logs'))
        self.log_level = getattr(logging, self.config.get('level', 'INFO').upper())
        
        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 已配置的logger集合
        self._configured_loggers = set()
        
        # 配置根日志记录器
        self._setup_root_logger()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认日志配置"""
        return {
            'level': 'INFO',
            'log_dir': './logs',
            'max_bytes': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'console': {
                'enabled': True,
                'level': 'INFO',
                'colored': True
            },
            'file': {
                'enabled': True,
                'level': 'DEBUG',
                'format': 'json'
            },
            'error_file': {
                'enabled': True,
                'level': 'ERROR'
            }
        }
    
    def _setup_root_logger(self):
        """配置根日志记录器"""
        root_logger = logging.getLogger()
        
        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 设置日志级别
        root_logger.setLevel(self.log_level)
        
        # 添加处理器
        self._add_handlers(root_logger)
    
    def _add_handlers(self, logger: logging.Logger):
        """为日志记录器添加处理器"""
        # 控制台处理器
        if self.config.get('console', {}).get('enabled', True):
            console_handler = self._create_console_handler()
            logger.addHandler(console_handler)
        
        # 文件处理器
        if self.config.get('file', {}).get('enabled', True):
            file_handler = self._create_file_handler()
            logger.addHandler(file_handler)
        
        # 错误文件处理器
        if self.config.get('error_file', {}).get('enabled', True):
            error_handler = self._create_error_file_handler()
            logger.addHandler(error_handler)
    
    def _create_console_handler(self) -> logging.Handler:
        """创建控制台处理器"""
        handler = logging.StreamHandler(sys.stdout)
        
        # 设置级别
        console_config = self.config.get('console', {})
        level = getattr(logging, console_config.get('level', 'INFO').upper())
        handler.setLevel(level)
        
        # 设置格式化器
        if console_config.get('colored', True):
            formatter = ColoredConsoleFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        return handler
    
    def _create_file_handler(self) -> logging.Handler:
        """创建文件处理器"""
        log_file = self.log_dir / 'app.log'
        
        # 使用轮转文件处理器
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config.get('max_bytes', 10 * 1024 * 1024),
            backupCount=self.config.get('backup_count', 5),
            encoding='utf-8'
        )
        
        # 设置级别
        file_config = self.config.get('file', {})
        level = getattr(logging, file_config.get('level', 'DEBUG').upper())
        handler.setLevel(level)
        
        # 设置格式化器
        if file_config.get('format') == 'json':
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
            )
        
        handler.setFormatter(formatter)
        return handler
    
    def _create_error_file_handler(self) -> logging.Handler:
        """创建错误文件处理器"""
        error_log_file = self.log_dir / 'error.log'
        
        # 使用轮转文件处理器
        handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.config.get('max_bytes', 10 * 1024 * 1024),
            backupCount=self.config.get('backup_count', 5),
            encoding='utf-8'
        )
        
        # 只记录ERROR及以上级别的日志
        handler.setLevel(logging.ERROR)
        
        # 设置格式化器为JSON格式，便于错误分析
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        
        return handler
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            配置好的日志记录器
        """
        logger = logging.getLogger(name)
        
        # 如果还未配置过，则配置该logger
        if name not in self._configured_loggers:
            # 设置不传播到父logger，避免重复输出
            logger.propagate = False
            
            # 添加处理器
            self._add_handlers(logger)
            
            # 设置级别
            logger.setLevel(self.log_level)
            
            # 标记为已配置
            self._configured_loggers.add(name)
        
        return logger
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        更新日志配置
        
        Args:
            new_config: 新的配置字典
        """
        self.config.update(new_config)
        
        # 重新配置根logger
        self._setup_root_logger()
        
        # 重新配置所有已创建的logger
        for logger_name in self._configured_loggers.copy():
            logger = logging.getLogger(logger_name)
            
            # 清除现有处理器
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # 重新添加处理器
            self._add_handlers(logger)
    
    def create_request_logger(self, request_id: str, user_id: Optional[str] = None) -> logging.LoggerAdapter:
        """
        创建请求级别的日志记录器
        
        Args:
            request_id: 请求ID
            user_id: 用户ID
            
        Returns:
            携带请求上下文的日志适配器
        """
        logger = self.get_logger('app.request')
        
        extra = {
            'request_id': request_id,
        }
        
        if user_id:
            extra['user_id'] = user_id
        
        return logging.LoggerAdapter(logger, extra)


# 全局日志管理器实例
_logger_manager: Optional[LoggerManager] = None


def init_logging(config: Optional[Dict[str, Any]] = None) -> LoggerManager:
    """
    初始化日志系统
    
    Args:
        config: 日志配置字典
        
    Returns:
        日志管理器实例
    """
    global _logger_manager
    _logger_manager = LoggerManager(config)
    return _logger_manager


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，默认为调用模块名
        
    Returns:
        日志记录器实例
    """
    global _logger_manager
    
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    
    if name is None:
        # 自动获取调用模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return _logger_manager.get_logger(name)


def get_request_logger(request_id: str, user_id: Optional[str] = None) -> logging.LoggerAdapter:
    """
    获取请求级别的日志记录器
    
    Args:
        request_id: 请求ID
        user_id: 用户ID
        
    Returns:
        携带请求上下文的日志适配器
    """
    global _logger_manager
    
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    
    return _logger_manager.create_request_logger(request_id, user_id)


def log_performance(func):
    """
    性能监控装饰器
    
    记录函数执行时间
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 记录性能日志
            logger.info(
                f"Function {func.__name__} executed successfully",
                extra={'duration': duration, 'function': func.__name__}
            )
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            # 记录错误和执行时间
            logger.error(
                f"Function {func.__name__} failed after {duration:.2f}ms: {str(e)}",
                extra={'duration': duration, 'function': func.__name__},
                exc_info=True
            )
            
            raise
    
    return wrapper