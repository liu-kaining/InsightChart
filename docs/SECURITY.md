# 环境变量安全配置指南

## 📋 概述

本文档说明了 InsightChart AI 项目中环境变量的安全管理和配置最佳实践。

## 🔒 安全措施

### 1. Git 忽略配置

`.gitignore` 文件已配置以下排除规则：

```gitignore
# Environment variables
.env
.env.local
.env.development
.env.test
.env.production
```

### 2. 文件说明

| 文件 | 用途 | Git 跟踪 | 说明 |
|------|------|----------|------|
| `.env` | 实际环境变量配置 | ❌ 不跟踪 | 包含敏感信息，仅本地使用 |
| `.env.example` | 环境变量模板 | ✅ 跟踪 | 示例配置，不含敏感信息 |

### 3. 敏感信息保护

以下信息属于敏感信息，不应暴露：

- `ACCESS_PASSWORD` - 系统访问口令
- `TOKEN_SECRET` - JWT签名密钥
- `QWEN_API_KEY` - 通义千问API密钥
- `DEEPSEEK_API_KEY` - DeepSeek API密钥

## 🚀 配置步骤

### 1. 初始配置

```bash
# 1. 复制模板文件
cp .env.example .env

# 2. 编辑环境变量
vim .env  # 或使用其他编辑器

# 3. 设置合适的文件权限
chmod 600 .env
```

### 2. 密钥生成建议

```bash
# 生成强JWT密钥
TOKEN_SECRET=$(openssl rand -hex 32)

# 生成强访问密码（建议手动设置）
ACCESS_PASSWORD="YourSecurePassword123!"
```

### 3. 验证配置

```bash
# 检查.env文件不在Git跟踪中
git status | grep -E "\.env$"  # 应该无输出

# 检查.gitignore是否包含.env
grep -E "^\.env" .gitignore
```

## ⚠️ 安全注意事项

### 开发环境

1. **本地开发**：
   - 确保 `.env` 文件权限设置为 `600`（仅用户可读写）
   - 不要在代码中硬编码任何敏感信息
   - 使用测试用的API密钥，避免产生费用

2. **团队协作**：
   - 通过安全渠道分享环境变量配置
   - 每个开发者使用独立的API密钥
   - 定期轮换测试环境的密钥

### 生产环境

1. **部署安全**：
   - 使用环境变量注入（如 Docker secrets）
   - 避免在镜像中包含 `.env` 文件
   - 使用强密码和复杂密钥

2. **密钥管理**：
   - 定期轮换所有密钥
   - 使用密钥管理服务（如 HashiCorp Vault）
   - 监控API密钥使用情况

## 🔧 故障排除

### .env 文件意外被Git跟踪

如果 `.env` 文件已经被Git跟踪，使用以下命令移除：

```bash
# 从Git索引中移除（保留本地文件）
git rm --cached .env

# 提交变更
git commit -m "Remove .env from version control"

# 确认.gitignore规则生效
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .env to .gitignore"
```

### 检查文件安全性

```bash
# 检查文件权限
ls -la .env

# 检查是否在Git中
git ls-files | grep -E "\.env$"

# 检查.gitignore规则
git check-ignore .env  # 应该输出 .env
```

## 📝 最佳实践总结

1. ✅ 始终使用 `.env.example` 作为模板
2. ✅ 确保 `.env` 在 `.gitignore` 中
3. ✅ 生产环境使用强密码和随机密钥
4. ✅ 定期轮换敏感信息
5. ✅ 通过安全渠道分享配置
6. ❌ 永远不要提交 `.env` 文件到Git
7. ❌ 不要在代码中硬编码敏感信息
8. ❌ 不要通过不安全渠道分享密钥

## 🆘 紧急处理

如果敏感信息意外泄露：

1. **立即行动**：
   - 轮换所有相关密钥
   - 撤销泄露的API密钥
   - 更改系统访问密码

2. **Git历史清理**：
   ```bash
   # 如果敏感信息在Git历史中，使用git-filter-repo清理
   git filter-repo --path .env --invert-paths
   ```

3. **通知相关方**：
   - 通知团队成员
   - 联系API服务提供商
   - 检查可能的未授权访问