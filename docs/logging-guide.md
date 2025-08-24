# InsightChart AI 日志系统

## 概述

InsightChart AI 配备了完善的日志管理系统，支持结构化日志记录、文件轮转、错误跟踪和性能监控。

## 日志功能特性

### 🏗️ 多层次日志记录
- **控制台日志**: 彩色输出，开发调试友好
- **文件日志**: JSON格式，便于后续分析和监控
- **错误日志**: 单独记录ERROR级别以上的日志
- **请求日志**: 记录所有API请求的详细信息

### 🔄 自动文件轮转
- 单个日志文件最大 10MB
- 保留最近 5 个备份文件
- 自动压缩和清理旧日志

### 📊 结构化日志格式
JSON格式包含以下信息：
```json
{
  "timestamp": "2025-08-24T12:00:00.000000",
  "level": "INFO",
  "logger": "app.auth",
  "message": "User login successful",
  "module": "auth",
  "function": "login",
  "line": 45,
  "thread": 140123456789120,
  "thread_name": "MainThread",
  "request_id": "uuid-string",
  "user_id": "user123",
  "duration_ms": 150.5
}
```

## 日志配置

### 配置文件位置
- 主配置: `backend/config/app.json`
- 环境变量: `.env` 文件中的 `LOG_LEVEL`

### 配置示例
```json
{
  "logging": {
    "level": "INFO",
    "log_dir": "./logs",
    "max_bytes": 10485760,
    "backup_count": 5,
    "console": {
      "enabled": true,
      "level": "INFO",
      "colored": true
    },
    "file": {
      "enabled": true,
      "level": "DEBUG",
      "format": "json"
    },
    "error_file": {
      "enabled": true,
      "level": "ERROR"
    }
  }
}
```

## 日志文件结构

```
logs/
├── app.log          # 主日志文件（JSON格式）
├── app.log.1        # 轮转备份文件
├── app.log.2
├── ...
├── error.log        # 错误日志文件（JSON格式）
├── error.log.1      # 错误日志备份
└── ...
```

## 使用日志查看工具

项目提供了专门的日志查看工具 `log_viewer.py`：

### 查看日志尾部
```bash
# 查看最后50行日志
python log_viewer.py tail

# 查看最后100行日志
python log_viewer.py tail -n 100

# 实时跟踪日志
python log_viewer.py tail -f

# 只显示错误级别日志
python log_viewer.py tail -l ERROR
```

### 搜索日志
```bash
# 搜索包含"login"的日志
python log_viewer.py search "login"

# 搜索最近3天的日志
python log_viewer.py search "error" -d 3

# 区分大小写搜索
python log_viewer.py search "ERROR" -c
```

### 错误摘要
```bash
# 查看今天的错误摘要
python log_viewer.py errors

# 查看最近7天的错误摘要
python log_viewer.py errors -d 7
```

## 在代码中使用日志

### 基础日志记录
```python
from app.core.logger import get_logger

logger = get_logger(__name__)

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息", exc_info=True)  # 包含异常堆栈
logger.critical("严重错误")
```

### 请求级别日志
```python
from app.core.logger import get_request_logger
from flask import g

# 在视图函数中使用
request_logger = get_request_logger(g.request_id, user_id="user123")
request_logger.info("处理用户请求", extra={'action': 'upload_file'})
```

### 性能监控装饰器
```python
from app.core.logger import log_performance

@log_performance
def expensive_operation():
    # 耗时操作
    time.sleep(1)
    return "result"
```

### 添加上下文信息
```python
logger.info(
    "文件上传成功",
    extra={
        'file_name': 'data.xlsx',
        'file_size': 1024000,
        'user_id': 'user123',
        'session_id': 'session456'
    }
)
```

## Docker环境中的日志

### 日志目录映射
- 开发环境: `./logs/backend` -> `/app/logs`
- 生产环境: `./data/logs` -> `/app/logs`

### 查看Docker容器日志
```bash
# 查看容器标准输出日志
docker-compose -f docker-compose.dev.yml logs backend-dev

# 实时跟踪容器日志
docker-compose -f docker-compose.dev.yml logs -f backend-dev

# 查看应用文件日志
docker exec -it insightchart-backend-dev python log_viewer.py tail -f
```

## 日志级别说明

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 详细调试信息 | 函数调用参数、中间计算结果 |
| INFO | 一般信息记录 | 用户操作、系统状态变化 |
| WARNING | 警告信息 | 请求超时、配置问题 |
| ERROR | 错误信息 | 异常处理、API调用失败 |
| CRITICAL | 严重错误 | 系统无法继续运行的错误 |

## 最佳实践

### 1. 日志内容建议
- ✅ 记录关键业务操作（登录、文件上传、图表生成）
- ✅ 记录性能指标（处理时间、文件大小）
- ✅ 记录错误和异常（包含堆栈信息）
- ✅ 记录用户行为（便于问题排查）
- ❌ 避免记录敏感信息（密码、API密钥）
- ❌ 避免过度日志记录（影响性能）

### 2. 错误处理
```python
try:
    result = risky_operation()
    logger.info(f"操作成功: {result}")
except SpecificException as e:
    logger.error(f"特定错误: {e}", exc_info=True)
    # 处理特定错误
except Exception as e:
    logger.critical(f"未预期错误: {e}", exc_info=True)
    # 处理通用错误
```

### 3. 性能监控
```python
import time

start_time = time.time()
try:
    result = expensive_operation()
    duration = (time.time() - start_time) * 1000
    logger.info(f"操作完成", extra={'duration_ms': duration})
except Exception as e:
    duration = (time.time() - start_time) * 1000
    logger.error(f"操作失败", extra={'duration_ms': duration}, exc_info=True)
```

## 监控和告警

### 日志监控指标
- 错误率: ERROR级别日志数量/总日志数量
- 响应时间: API请求处理时间分布
- 异常类型: 不同异常类型的出现频率
- 用户活动: 活跃用户数、操作频率

### 集成外部监控
日志系统支持与以下工具集成：
- **ELK Stack**: Elasticsearch + Logstash + Kibana
- **Prometheus**: 指标收集和告警
- **Grafana**: 日志可视化和仪表板
- **Sentry**: 错误跟踪和性能监控

## 故障排查

### 常见问题
1. **日志文件过大**: 检查轮转配置，考虑降低日志级别
2. **日志缺失**: 检查文件权限和目录映射
3. **性能影响**: 考虑异步日志记录或减少日志输出

### 诊断命令
```bash
# 检查日志目录
ls -la logs/

# 检查磁盘空间
df -h

# 查看最近的错误
python log_viewer.py errors -d 1

# 搜索特定错误
python log_viewer.py search "Exception" -d 7
```

---

通过完善的日志系统，你可以更好地监控应用运行状态、快速定位问题、分析用户行为，并为系统优化提供数据支持。