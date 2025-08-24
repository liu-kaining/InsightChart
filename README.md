# InsightChart AI - 智能图表生成器

<div align="center">

![InsightChart AI](https://img.shields.io/badge/InsightChart-AI-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Vue](https://img.shields.io/badge/vue-3.0+-green.svg)

基于大语言模型的智能图表生成器，让数据可视化变得简单高效

[功能特性](#功能特性) • [快速开始](#快速开始) • [部署指南](#部署指南) • [日志管理](#日志管理和监控) • [API文档](#api文档) • [技术架构](#技术架构)

</div>

## 📋 项目概述

InsightChart AI 是一个智能的数据可视化工具，通过集成先进的大语言模型（支持Qwen和DeepSeek），实现从数据文件到精美图表的自动化生成。用户只需上传Excel或CSV文件，AI将自动分析数据特征并生成多种类型的ECharts图表。

### 🎯 核心价值

- **智能化**：AI自动识别数据类型和关系，推荐最合适的图表类型
- **零门槛**：无需专业知识，拖拽上传即可生成专业图表
- **高效率**：1分钟内从原始数据到可视化图表
- **高质量**：生成的图表美观、专业，可直接用于报告和演示

## ✨ 功能特性

### 🔐 安全认证
- 口令认证机制，无需注册登录
- JWT Token会话管理
- 数据隐私保护，处理后自动清理

### 📊 智能分析
- 自动识别数据类型（数值、文本、日期、分类等）
- 智能推荐图表类型（柱状图、折线图、饼图、散点图等）
- 一次上传生成3-5个不同风格的图表

### 🎨 可视化功能
- 基于ECharts的高质量图表渲染
- 支持图表交互和动画效果
- 多种导出格式（PNG、JPG）
- 图表复制到剪贴板功能

### 🤖 大模型支持
- 统一的大模型适配层架构
- 支持Qwen（阿里云通义千问）
- 支持DeepSeek
- 易于扩展其他大模型

### 🚀 现代化技术栈
- **前端**：Vue 3 + TypeScript + Element Plus + ECharts
- **后端**：Flask + Python 3.9+ + Pandas
- **部署**：Docker + Docker Compose
- **架构**：前后端分离，RESTful API

## 🚀 快速开始

### 环境要求

- Docker >= 20.0
- Docker Compose >= 2.0
- 大模型API密钥（Qwen或DeepSeek）

### 一键部署

1. **克隆项目**
```bash
git clone https://github.com/your-repo/InsightChart.git
cd InsightChart
```

2. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

⚠️ **重要安全提醒**：
- `.env` 文件包含敏感信息，已被 `.gitignore` 排除，不会被 Git 跟踪
- 请勿将 `.env` 文件提交到代码仓库或分享给他人
- 生产环境请使用强密码和随机生成的密钥

必需配置项：
```bash
# 访问口令
ACCESS_PASSWORD=your_secure_password

# JWT密钥
TOKEN_SECRET=your_jwt_secret_key

# 大模型API密钥（至少配置一个）
QWEN_API_KEY=your_qwen_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

3. **一键部署**
```bash
# 运行部署脚本
./deploy.sh

# 或手动部署
docker-compose up -d
```

4. **访问应用**
- 应用地址：http://localhost:5004
- 健康检查：http://localhost:5004/health

**注意**：这是一个单容器部署，前端和后端都在同一个Docker容器中运行，无需启动多个服务。

## 📖 使用指南

### 基本使用流程

1. **访问系统**：打开浏览器访问应用地址
2. **输入口令**：使用配置的访问口令登录系统
3. **上传文件**：支持拖拽或点击上传Excel/CSV文件（最大5MB）
4. **AI分析**：系统自动分析数据并生成图表（通常需要10-30秒）
5. **查看结果**：浏览AI生成的多个图表
6. **导出使用**：下载图表或复制到剪贴板

### 支持的文件格式

- **Excel文件**：`.xlsx`, `.xls`
- **CSV文件**：`.csv`（支持多种编码格式）

### 数据要求

- 结构化的二维表格数据
- 包含表头的数据格式
- 避免合并单元格和复杂公式

## 🔧 部署指南

### 生产环境部署

1. **服务器要求**
   - 2核CPU，4GB内存
   - 20GB可用磁盘空间
   - Docker运行环境

2. **安全配置**
```bash
# 修改默认口令
ACCESS_PASSWORD=your_complex_password

# 使用强JWT密钥
TOKEN_SECRET=$(openssl rand -hex 32)

# 配置HTTPS（推荐）
# 在nginx配置中添加SSL证书
```

3. **性能优化**
```yaml
# docker-compose.yml
services:
  insightchart:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### 开发环境

```bash
# 启动开发环境（单容器部署）
./dev.sh

# 或手动启动
docker-compose -f docker-compose.dev.yml up -d

# 开发服务器：http://localhost:5004
```

**开发环境说明**：
- 开发环境也采用单容器部署，简化开发流程
- 前端构建后集成到后端容器中
- 支持后端代码热重载（通过卷挂载）
- 统一的开发服务器端口：5004

**开发环境管理命令**：
```bash
./dev.sh start    # 启动开发环境
./dev.sh status   # 查看状态
./dev.sh logs     # 查看日志
./dev.sh stop     # 停止开发环境
./dev.sh restart  # 重启开发环境
./dev.sh rebuild  # 重新构建
```

## 📚 API文档

### 认证接口

#### POST /api/auth/login
登录获取Token
```json
{
  "password": "access_password"
}
```

#### POST /api/auth/verify
验证Token有效性

### 文件处理接口

#### POST /api/file/upload
上传文件并生成图表
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@data.xlsx" \
  -F "model=qwen" \
  http://localhost:5004/api/file/upload
```

#### GET /api/file/session/{session_id}
获取会话图表数据

### 系统接口

#### GET /api/system/health
系统健康检查

#### GET /api/system/models
获取可用模型列表

详细API文档请参考：[API Reference](docs/api.md)

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (Vue3)    │◄──►│   后端 (Flask)   │◄──►│   大模型 API     │
│                 │    │                 │    │                 │
│ - 用户界面       │    │ - 认证中间件     │    │ - Qwen          │
│ - 文件上传       │    │ - 文件处理       │    │ - DeepSeek      │
│ - 图表展示       │    │ - 数据分析       │    │ - 其他模型...    │
│ - ECharts渲染   │    │ - 图表生成       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件

#### 前端架构
- **Vue 3 + Composition API**：现代化的响应式框架
- **TypeScript**：类型安全和更好的开发体验
- **Element Plus**：企业级UI组件库
- **ECharts**：专业的图表渲染引擎

#### 后端架构
- **Flask**：轻量级Python Web框架
- **统一适配层**：支持多种大模型的扩展架构
- **Pandas**：强大的数据处理能力
- **JWT认证**：无状态的安全认证机制

#### 部署架构
- **Docker容器化**：确保环境一致性
- **多阶段构建**：优化镜像大小
- **单容器部署**：前端构建后集成到后端容器，简化部署
- **健康检查**：自动监控服务状态

## 📊 日志管理和监控

### 日志系统特性

InsightChart AI 配备了企业级的日志管理系统，提供完整的系统监控和问题排查能力：

- **多层次日志记录**：控制台日志（彩色输出）和文件日志（JSON结构化格式）
- **自动日志轮转**：单文件最大10MB，保留5个备份文件
- **请求追踪**：每个API请求都有唯一ID，便于问题排查
- **性能监控**：自动记录函数执行时间和系统性能指标
- **异常处理**：完整的异常堆栈信息记录

### 日志查看工具

项目提供了专业的 `log_viewer.py` 工具，支持实时日志监控和分析：

#### 🔍 查看最新日志
```bash
# 在Docker容器中查看最新日志
docker exec insightchart-backend-dev python log_viewer.py tail

# 查看最新50行日志
docker exec insightchart-backend-dev python log_viewer.py tail -n 50

# 只显示错误级别日志
docker exec insightchart-backend-dev python log_viewer.py tail -l ERROR
```

#### 📺 实时日志跟踪
```bash
# 实时跟踪所有日志
docker exec insightchart-backend-dev python log_viewer.py tail -f

# 实时跟踪错误日志
docker exec insightchart-backend-dev python log_viewer.py tail -f -l ERROR
```

#### 🔎 日志搜索功能
```bash
# 搜索包含"login"的日志
docker exec insightchart-backend-dev python log_viewer.py search "login"

# 搜索最近3天的日志
docker exec insightchart-backend-dev python log_viewer.py search "error" -d 3

# 区分大小写搜索
docker exec insightchart-backend-dev python log_viewer.py search "ERROR" -c
```

#### 📈 错误日志摘要
```bash
# 查看今天的错误摘要
docker exec insightchart-backend-dev python log_viewer.py errors

# 查看最近7天的错误摘要
docker exec insightchart-backend-dev python log_viewer.py errors -d 7
```

### 日志文件结构

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

### 监控指标

系统自动记录以下关键指标：

- **请求统计**：API调用次数、响应时间、成功率
- **错误统计**：错误类型分布、错误频率、异常堆栈
- **性能指标**：文件处理时间、图表生成时间、内存使用
- **用户行为**：文件上传统计、图表生成统计

### 日志配置

日志行为可通过配置文件调整：

```json
// backend/config/app.json
{
  "logging": {
    "level": "INFO",
    "log_dir": "./logs",
    "max_bytes": 10485760,  // 10MB
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

## 🔧 开发指南

### 本地开发

1. **后端开发**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

2. **前端开发**
```bash
cd frontend
npm install
npm run dev
```

### 扩展大模型

1. **创建新适配器**
```python
# backend/app/adapters/new_model_adapter.py
from .base_llm import BaseLLMAdapter

class NewModelAdapter(BaseLLMAdapter):
    def generate_charts(self, data_summary):
        # 实现具体的API调用逻辑
        pass
```

2. **注册适配器**
```python
# backend/app/services/llm_service.py
adapter_classes = {
    'qwen': QwenAdapter,
    'deepseek': DeepSeekAdapter,
    'new_model': NewModelAdapter,  # 添加新模型
}
```

### 代码规范

- **Python**：遵循PEP 8规范
- **TypeScript**：使用ESLint + Prettier
- **Git提交**：使用Conventional Commits格式

## 📊 性能指标

- **响应时间**：文件上传到图表生成平均15秒内
- **并发支持**：单实例支持10+并发用户
- **文件限制**：支持最大5MB的数据文件
- **图表类型**：支持10+种常见图表类型

## 🛠️ 故障排除

### 常见问题

1. **图表生成失败**
   - 检查大模型API密钥配置
   - 确认数据格式符合要求
   - 查看服务日志：`docker-compose logs`

2. **文件上传失败**
   - 检查文件大小是否超过5MB
   - 确认文件格式为支持的类型
   - 检查网络连接状态

3. **认证失败**
   - 确认ACCESS_PASSWORD配置正确
   - 检查Token是否过期
   - 清除浏览器缓存重试

### 日志查看

使用内置的 `log_viewer.py` 工具进行问题诊断：

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f insightchart

# 使用日志查看工具
docker exec insightchart-backend-dev python log_viewer.py tail -n 100

# 查看最近的错误日志
docker exec insightchart-backend-dev python log_viewer.py errors

# 实时跟踪错误日志
docker exec insightchart-backend-dev python log_viewer.py tail -f -l ERROR

# 搜索特定错误
docker exec insightchart-backend-dev python log_viewer.py search "FileException"
```

### 常见问题诊断

使用日志工具快速定位问题：

1. **查看系统启动情况**
```bash
docker exec insightchart-backend-dev python log_viewer.py search "Starting InsightChart"
```

2. **检查认证问题**
```bash
docker exec insightchart-backend-dev python log_viewer.py search "authentication"
```

3. **监控文件上传**
```bash
docker exec insightchart-backend-dev python log_viewer.py search "upload"
```

4. **查看大模型API调用**
```bash
docker exec insightchart-backend-dev python log_viewer.py search "LLM"
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！请参考 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 贡献类型

- 🐛 Bug修复
- ✨ 新功能开发
- 📚 文档改进
- 🎨 UI/UX优化
- 🔧 性能优化

## 📄 许可证

本项目采用 MIT 许可证。详情请参考 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [ECharts](https://echarts.apache.org/) - 强大的图表库
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Flask](https://flask.palletsprojects.com/) - 轻量级Python Web框架
- [Element Plus](https://element-plus.org/) - Vue 3 UI组件库

## 📞 联系方式

- 项目地址：https://github.com/your-repo/InsightChart
- 问题反馈：https://github.com/your-repo/InsightChart/issues
- 邮箱：your-email@example.com

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐️**

Made with ❤️ by InsightChart Team

</div>