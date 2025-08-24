import os
import atexit
from flask import Flask, send_from_directory, send_file
from flask_cors import CORS
from app.core import init_config, register_error_handlers, get_config
from app.core.logger import init_logging, get_logger
from app.middleware import init_request_logging
from app.api import auth_bp, file_bp, system_bp, cleanup_bp
from app.services.cleanup_service import start_cleanup_service, stop_cleanup_service

# 初始化日志系统（需要在其他模块导入之前）
logger = None


def create_app(config_dir='./config'):
    """
    创建Flask应用
    
    Args:
        config_dir: 配置文件目录
        
    Returns:
        Flask应用实例
    """
    global logger
    
    try:
        # 初始化配置
        init_config(config_dir)
        config = get_config()
        
        # 初始化日志系统
        log_config = config.get_app_config('logging', {})
        init_logging(log_config)
        logger = get_logger(__name__)
        
        logger.info("Starting InsightChart AI Backend...")
        logger.info(f"Log configuration: {log_config}")
        
        # 创建 Flask 应用（配置静态文件目录）
        static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        app = Flask(__name__, static_folder=static_folder, static_url_path='')
        
        # 配置Flask应用
        app.config['SECRET_KEY'] = config.get_security_config().get('token_secret', 'dev-secret-key')
        app.config['MAX_CONTENT_LENGTH'] = config.get_file_config().get('max_size_mb', 5) * 1024 * 1024
        
        logger.info("Flask application created and configured")
        
        # 启用CORS
        CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
        logger.info("CORS enabled")
        
        # 初始化请求日志中间件
        init_request_logging(app)
        logger.info("Request logging middleware initialized")
        
        # 注册蓝图
        app.register_blueprint(auth_bp)
        app.register_blueprint(file_bp)
        app.register_blueprint(system_bp)
        app.register_blueprint(cleanup_bp)
        logger.info("API blueprints registered")
        
        # 注册错误处理器
        register_error_handlers(app)
        logger.info("Error handlers registered")
        
        # 启动文件清理服务
        try:
            start_cleanup_service()
            logger.info("File cleanup service started")
            
            # 注册应用关闭时停止清理服务
            atexit.register(stop_cleanup_service)
            logger.info("Cleanup service shutdown handler registered")
        except Exception as e:
            logger.error(f"Failed to start cleanup service: {e}")
            # 不阻止应用启动，但记录错误
        
        # 添加静态文件服务路由
        @app.route('/')
        def index():
            """服务前端首页"""
            logger.info("Frontend index page requested")
            try:
                return send_file(os.path.join(app.static_folder, 'index.html'))
            except FileNotFoundError:
                logger.warning("Frontend files not found, serving API info")
                return {
                    'message': 'InsightChart AI Backend',
                    'version': '1.0.0',
                    'status': 'running',
                    'note': 'Frontend files not available'
                }
        
        # 添加前端路由支持（SPA路由回退）
        @app.route('/<path:path>')
        def serve_frontend(path):
            """服务前端静态文件或SPA路由"""
            logger.debug(f"Frontend path requested: {path}")
            
            # 检查是否是API路由
            if path.startswith('api/'):
                # 让Flask继续处理API路由
                from flask import abort
                abort(404)
            
            # 尝试服务静态文件
            try:
                return send_from_directory(app.static_folder, path)
            except FileNotFoundError:
                # 如果静态文件不存在，返回index.html（用于SPA路由）
                try:
                    logger.debug(f"File {path} not found, serving index.html for SPA routing")
                    return send_file(os.path.join(app.static_folder, 'index.html'))
                except FileNotFoundError:
                    logger.warning("Frontend files not found")
                    return {
                        'error': 'Frontend files not available',
                        'message': 'This is a backend API server'
                    }, 404
        
        # 添加健康检查路由
        @app.route('/health')
        def health():
            """健康检查端点"""
            logger.info("Health check endpoint accessed")
            return {'status': 'healthy'}
        
        logger.info("Application initialization completed successfully")
        return app
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to create Flask application: {e}", exc_info=True)
        else:
            print(f"Failed to create Flask application: {e}")
        raise


def main():
    """主函数"""
    try:
        # 创建应用
        app = create_app()
        config = get_config()
        
        # 获取运行配置
        app_config = config.get_app_config('app', {})
        host = app_config.get('host', '0.0.0.0')
        port = app_config.get('port', 5000)
        debug = app_config.get('debug', False)
        
        logger.info(f"Starting InsightChart AI Backend on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # 启动应用
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        if logger:
            logger.error(f"Error starting application: {e}", exc_info=True)
        else:
            print(f"Error starting application: {e}")
        exit(1)


if __name__ == '__main__':
    main()