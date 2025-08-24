#!/usr/bin/env python3
"""
WSGI启动文件
用于Gunicorn启动Flask应用
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# 创建应用实例
application = create_app()

if __name__ == "__main__":
    application.run()