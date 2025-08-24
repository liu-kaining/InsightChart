# InsightChart AI - 单容器部署架构

## 🎯 修改目标

将 InsightChart AI 的部署架构统一为**单容器部署**，无论是生产环境还是开发环境，都只需要启动一个容器即可运行完整的应用。

## 🔄 修改内容

### 1. 生产环境（已支持单容器）

**文件**: `docker-compose.yml`
- ✅ 移除了可选的 nginx 服务
- ✅ 只保留一个 `insightchart` 服务
- ✅ 前端构建后集成到后端容器中

### 2. 开发环境（修改为单容器）

**文件**: `docker-compose.dev.yml`
- ✅ 移除了前端容器 `frontend-dev`
- ✅ 只保留一个 `insightchart-dev` 服务
- ✅ 前端构建后集成到后端容器中

**文件**: `backend/Dockerfile.dev`
- ✅ 使用多阶段构建
- ✅ 第一阶段构建前端
- ✅ 第二阶段构建后端并集成前端

**文件**: `frontend/Dockerfile.dev`
- ✅ 已删除（不再需要）

### 3. 新增开发环境启动脚本

**文件**: `dev.sh`
- ✅ 开发环境快速启动脚本
- ✅ 支持多种管理命令
- ✅ 自动检查和配置

## 🏗️ 架构对比

### 修改前（开发环境）
```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│   Container     │    │   Container     │
│   Port: 3003    │◄──►│   Port: 5004    │
└─────────────────┘    └─────────────────┘
```

### 修改后（统一单容器）
```
┌─────────────────────────────────────┐
│           Single Container          │
│  ┌─────────────────────────────────┐ │
│  │         Flask Backend           │ │
│  │  - Python 3.9                  │ │
│  │  - Flask 3.0                   │ │
│  │  - 大模型适配器                 │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │      Static Frontend Files      │ │
│  │  - Vue 3 构建产物               │ │
│  │  - ECharts 图表库               │ │
│  │  - Element Plus UI组件          │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 🚀 部署方式

### 生产环境
```bash
# 一键部署
./deploy.sh

# 或手动部署
docker-compose up -d

# 访问地址
http://localhost:5004
```

### 开发环境
```bash
# 一键启动开发环境
./dev.sh

# 或手动启动
docker-compose -f docker-compose.dev.yml up -d

# 访问地址
http://localhost:5004
```

## 📊 优势对比

### 单容器部署优势

1. **简化部署**
   - ✅ 只需要启动一个容器
   - ✅ 减少网络配置复杂度
   - ✅ 降低资源消耗

2. **统一管理**
   - ✅ 单一日志流
   - ✅ 统一监控和健康检查
   - ✅ 简化备份和恢复

3. **环境一致性**
   - ✅ 开发环境和生产环境架构一致
   - ✅ 避免环境差异带来的问题
   - ✅ 减少调试和部署问题

4. **运维友好**
   - ✅ 减少容器间通信问题
   - ✅ 简化故障排查
   - ✅ 降低部署失败风险

### 开发体验

1. **代码热重载**
   - ✅ 后端代码热重载（通过卷挂载）
   - ✅ 前端代码修改后需要重新构建（可选）
   - ✅ 支持实时调试和开发

2. **统一端口**
   - ✅ 开发环境和生产环境使用相同端口
   - ✅ 避免端口配置混乱
   - ✅ 简化访问方式

## 🔧 技术实现

### 多阶段构建
```dockerfile
# 第一阶段：构建前端
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# 第二阶段：构建后端
FROM python:3.9-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./

# 关键：复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./static
```

### Flask静态文件服务
```python
# 配置静态文件目录
app = Flask(__name__, static_folder='static', static_url_path='')

# 服务前端首页
@app.route('/')
def index():
    return send_file(os.path.join(app.static_folder, 'index.html'))

# 服务前端路由（SPA支持）
@app.route('/<path:path>')
def serve_frontend(path):
    if path.startswith('api/'):
        abort(404)  # 让Flask处理API路由
    
    try:
        return send_from_directory(app.static_folder, path)
    except FileNotFoundError:
        return send_file(os.path.join(app.static_folder, 'index.html'))
```

## 📝 使用说明

### 开发环境管理

```bash
# 启动开发环境
./dev.sh

# 查看状态
./dev.sh status

# 查看日志
./dev.sh logs

# 停止开发环境
./dev.sh stop

# 重启开发环境
./dev.sh restart

# 重新构建
./dev.sh rebuild
```

### 生产环境管理

```bash
# 部署生产环境
./deploy.sh

# 查看状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 停止服务
./deploy.sh stop

# 重启服务
./deploy.sh restart
```

## ✅ 验证清单

- [x] 生产环境单容器部署
- [x] 开发环境单容器部署
- [x] 前端构建集成
- [x] 静态文件服务
- [x] SPA路由支持
- [x] 健康检查
- [x] 开发环境启动脚本
- [x] 文档更新
- [x] 端口统一（5004）

## 🎉 总结

通过这次修改，InsightChart AI 现在采用统一的单容器部署架构：

- **生产环境**：单容器部署，简化运维
- **开发环境**：单容器部署，简化开发流程
- **统一端口**：5004端口访问
- **统一管理**：简化的启动和管理脚本

这种架构设计既保证了生产环境的稳定性和性能，又为开发人员提供了简化的开发体验，避免了环境差异带来的问题。
