import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """配置管理类"""
    
    def __init__(self, config_dir: str = './config'):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        self._app_config = {}
        self._models_config = {}
        
        # 加载环境变量
        load_dotenv()
        
        # 加载配置文件
        self._load_configs()
    
    def _load_configs(self):
        """加载所有配置文件"""
        try:
            # 加载应用主配置
            app_config_path = os.path.join(self.config_dir, 'app.json')
            with open(app_config_path, 'r', encoding='utf-8') as f:
                self._app_config = json.load(f)
            
            # 替换环境变量
            self._app_config = self._replace_env_vars(self._app_config)
            
            # 加载模型配置
            models_config_path = os.path.join(self.config_dir, 'models.json')
            with open(models_config_path, 'r', encoding='utf-8') as f:
                self._models_config = json.load(f)
            
            # 替换环境变量
            self._models_config = self._replace_env_vars(self._models_config)
            
            logger.info("Configuration loaded successfully")
            
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def _replace_env_vars(self, config: Any) -> Any:
        """
        递归替换配置中的环境变量
        
        Args:
            config: 配置数据
            
        Returns:
            替换后的配置数据
        """
        if isinstance(config, dict):
            return {key: self._replace_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._replace_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            # 提取环境变量名
            env_var = config[2:-1]
            return os.getenv(env_var, config)
        else:
            return config
    
    @property
    def app(self) -> Dict[str, Any]:
        """获取应用配置"""
        return self._app_config
    
    @property
    def models(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self._models_config
    
    def get_app_config(self, key: str, default: Any = None) -> Any:
        """
        获取应用配置项
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._app_config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        获取指定模型的配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置
        """
        return self._models_config.get(model_name, {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self._app_config.get('security', {})
    
    def get_file_config(self) -> Dict[str, Any]:
        """获取文件配置"""
        return self._app_config.get('file', {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self._app_config.get('llm', {})
    
    def reload(self):
        """重新加载配置"""
        self._load_configs()
        logger.info("Configuration reloaded")


# 全局配置实例
config = None


def get_config() -> Config:
    """获取全局配置实例"""
    global config
    if config is None:
        config = Config()
    return config


def init_config(config_dir: str = './config'):
    """
    初始化全局配置
    
    Args:
        config_dir: 配置文件目录
    """
    global config
    config = Config(config_dir)
    return config