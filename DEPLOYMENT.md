# InsightChart AI - 部署架构说明

## 🏗️ 部署架构概览

InsightChart AI 采用**单容器部署**架构，前端和后端都在同一个Docker容器中运行，简化了部署和维护。

## 📦 容器架构

### 生产环境（单容器）

```
┌─────────────────────────────────────┐
│           Docker Container          │
│  ┌─────────────────────────────────┐ │
│  │         Flask Backend           │ │
│  │  - Python 3.9                  │ │
│  │  - Flask 3.0                   │ │
│  │  - Pandas                      │ │
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

### 开发环境（单容器）

```
┌─────────────────────────────────────┐
│        Development Container        │
│  ┌─────────────────────────────────┐ │
│  │         Flask Backend           │ │
│  │  - Python 3.9                  │ │
│  │  - Flask 3.0 (开发模式)         │ │
│  │  - 代码热重载                   │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │      Static Frontend Files      │ │
│  │  - Vue 3 构建产物               │ │
│  │  - 开发模式构建                 │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 🔧 技术实现

### 多阶段构建 (Dockerfile)

```dockerfile
# 第一阶段：构建前端
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build  # 生成静态文件

# 第二阶段：构建后端
FROM python:3.9-slim AS backend
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./

# 关键步骤：复制前端构建产物到后端静态目录
COPY --from=frontend-builder /app/frontend/dist ./static
```

### Flask静态文件服务

```python
# backend/app.py
app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index():
    """服务前端首页"""
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/<path:path>')
def serve_frontend(path):
    """服务前端静态文件或SPA路由"""
    if path.startswith('api/'):
        abort(404)  # 让Flask处理API路由
    
    try:
        return send_from_directory(app.static_folder, path)
    except FileNotFoundError:
        return send_file(os.path.join(app.static_folder, 'index.html'))
```

## 🚀 部署方式

### 生产环境部署

```bash
# 一键部署（推荐）
./deploy.sh

# 或手动部署
docker-compose up -d
```

**特点**：
- ✅ 单容器部署，简化运维
- ✅ 前端构建后集成，性能优化
- ✅ 自动健康检查
- ✅ 端口映射：5004:5000

### 开发环境部署

```bash
# 开发环境（单容器）
docker-compose -f docker-compose.dev.yml up -d
```

**特点**：
- ✅ 单容器部署，简化开发流程
- ✅ 前端构建后集成，与生产环境一致
- ✅ 后端代码热重载支持（通过卷挂载）
- ✅ 统一的开发服务器端口：5004

## 📊 架构优势

### 单容器部署优势

1. **简化部署**
   - 只需要启动一个容器
   - 减少网络配置复杂度
   - 降低资源消耗

2. **统一管理**
   - 单一日志流
   - 统一监控和健康检查
   - 简化备份和恢复

3. **性能优化**
   - 前端静态文件由Flask直接服务
   - 减少网络跳转
   - 更好的缓存控制

4. **运维友好**
   - 减少容器间通信问题
   - 简化故障排查
   - 降低部署失败风险

### 开发环境优势

1. **简化开发流程**
   - 单容器部署，减少配置复杂度
   - 与生产环境架构一致，避免环境差异
   - 统一的端口和访问方式

2. **代码热重载**
   - 后端代码热重载（通过卷挂载）
   - 前端代码修改后需要重新构建（可选）
   - 支持实时调试和开发

3. **资源优化**
   - 减少容器资源消耗
   - 简化网络配置
   - 统一的日志管理

## 🔍 验证部署

### 检查服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 健康检查
curl http://localhost:5004/health
```

### 访问应用

- **生产环境**: http://localhost:5004
- **开发环境**: http://localhost:5004

## 🛠️ 故障排除

### 常见问题

1. **前端文件未找到**
   ```bash
   # 检查构建是否成功
   docker-compose build --no-cache
   ```

2. **端口冲突**
   ```bash
   # 修改端口映射
   # docker-compose.yml
   ports:
     - "8080:5000"  # 改为其他端口
   ```

3. **静态文件服务问题**
   ```bash
   # 检查容器内文件
   docker exec insightchart-app ls -la /app/static
   ```

## 📝 总结

InsightChart AI 采用统一的单容器部署架构：

- **生产环境**：单容器部署，简化运维，提升性能
- **开发环境**：单容器部署，简化开发流程，与生产环境一致

这种架构设计既保证了生产环境的稳定性和性能，又为开发人员提供了简化的开发体验，避免了环境差异带来的问题。
