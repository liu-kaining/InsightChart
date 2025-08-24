#!/bin/bash

# InsightChart AI 项目完整性验证脚本
# 检查所有必要的文件和目录是否正确创建

echo "🔍 正在验证 InsightChart AI 项目完整性..."
echo

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
total_checks=0
passed_checks=0

# 检查函数
check_file() {
    local file_path="$1"
    local description="$2"
    
    total_checks=$((total_checks + 1))
    
    if [[ -f "$file_path" ]]; then
        echo -e "${GREEN}✓${NC} $description"
        passed_checks=$((passed_checks + 1))
    else
        echo -e "${RED}✗${NC} $description (文件不存在: $file_path)"
    fi
}

check_dir() {
    local dir_path="$1"
    local description="$2"
    
    total_checks=$((total_checks + 1))
    
    if [[ -d "$dir_path" ]]; then
        echo -e "${GREEN}✓${NC} $description"
        passed_checks=$((passed_checks + 1))
    else
        echo -e "${RED}✗${NC} $description (目录不存在: $dir_path)"
    fi
}

echo "📁 项目结构检查:"

# 根目录文件
check_file "README.md" "项目说明文档"
check_file "Dockerfile" "Docker构建文件"
check_file "docker-compose.yml" "Docker Compose配置"
check_file "docker-compose.dev.yml" "开发环境Docker配置"
check_file "deploy.sh" "部署脚本"
check_file ".env.example" "环境变量模板"
check_file ".dockerignore" "Docker忽略文件"
check_file "docs/prd.md" "产品需求文档"

echo
echo "🗂️ 目录结构检查:"

# 目录结构
check_dir "backend" "后端目录"
check_dir "frontend" "前端目录"
check_dir "docs" "文档目录"
check_dir "tests" "测试目录"

echo
echo "🐍 后端文件检查:"

# 后端文件
check_file "backend/app.py" "后端应用入口"
check_file "backend/requirements.txt" "Python依赖文件"
check_file "backend/.env" "后端环境变量"
check_dir "backend/app" "后端应用目录"
check_dir "backend/config" "后端配置目录"
check_file "backend/config/app.json" "应用配置文件"
check_file "backend/config/models.json" "模型配置文件"

echo
echo "🔧 后端核心模块检查:"

# 后端核心模块
check_dir "backend/app/core" "核心模块目录"
check_file "backend/app/core/config.py" "配置管理模块"
check_file "backend/app/core/auth.py" "认证模块"
check_file "backend/app/core/exceptions.py" "异常处理模块"

check_dir "backend/app/services" "服务模块目录"
check_file "backend/app/services/llm_service.py" "大模型服务"
check_file "backend/app/services/file_service.py" "文件处理服务"
check_file "backend/app/services/chart_service.py" "图表生成服务"

check_dir "backend/app/adapters" "适配器目录"
check_file "backend/app/adapters/base_llm.py" "基础适配器"
check_file "backend/app/adapters/qwen_adapter.py" "Qwen适配器"
check_file "backend/app/adapters/deepseek_adapter.py" "DeepSeek适配器"

check_dir "backend/app/api" "API目录"
check_dir "backend/app/api/endpoints" "API端点目录"
check_file "backend/app/api/endpoints/auth.py" "认证API"
check_file "backend/app/api/endpoints/file.py" "文件处理API"
check_file "backend/app/api/endpoints/system.py" "系统API"

echo
echo "🖥️ 前端文件检查:"

# 前端文件
check_file "frontend/package.json" "前端依赖文件"
check_file "frontend/vite.config.ts" "Vite配置文件"
check_file "frontend/tsconfig.json" "TypeScript配置"
check_file "frontend/index.html" "HTML模板"
check_file "frontend/env.d.ts" "环境类型声明"

echo
echo "⚛️ 前端核心模块检查:"

# 前端核心模块
check_dir "frontend/src" "前端源码目录"
check_file "frontend/src/main.ts" "前端入口文件"
check_file "frontend/src/App.vue" "根组件"

check_dir "frontend/src/types" "类型定义目录"
check_file "frontend/src/types/api.ts" "API类型定义"
check_file "frontend/src/types/chart.ts" "图表类型定义"

check_dir "frontend/src/services" "服务层目录"
check_file "frontend/src/services/auth.ts" "认证服务"
check_file "frontend/src/services/api.ts" "API服务"
check_file "frontend/src/services/chart.ts" "图表服务"

check_dir "frontend/src/components" "组件目录"
check_dir "frontend/src/components/Authentication" "认证组件目录"
check_file "frontend/src/components/Authentication/LoginForm.vue" "登录表单组件"
check_dir "frontend/src/components/FileUpload" "文件上传组件目录"
check_file "frontend/src/components/FileUpload/FileUpload.vue" "文件上传组件"
check_dir "frontend/src/components/ChartDisplay" "图表展示组件目录"
check_file "frontend/src/components/ChartDisplay/ChartDisplay.vue" "图表展示组件"

check_dir "frontend/src/views" "视图目录"
check_file "frontend/src/views/Home.vue" "主页视图"

echo
echo "📋 测试文件检查:"

# 测试文件
check_file "tests/sample_data.csv" "示例数据文件"

echo
echo "📄 文档检查:"

# 文档文件
check_file "docs/技术架构文档.md" "技术架构文档"

echo
echo "=" "$(printf '%.0s=' {1..50})"

# 输出结果
if [[ $passed_checks -eq $total_checks ]]; then
    echo -e "${GREEN}🎉 项目验证完成！所有检查项都通过了 ($passed_checks/$total_checks)${NC}"
    echo
    echo "✅ 项目结构完整，可以开始部署和测试"
    echo
    echo "下一步操作:"
    echo "1. 配置 .env 文件中的API密钥"
    echo "2. 运行 ./deploy.sh 进行部署"
    echo "3. 访问 http://localhost:5000 开始使用"
    exit 0
else
    echo -e "${RED}❌ 项目验证失败！有 $((total_checks - passed_checks)) 个检查项未通过 ($passed_checks/$total_checks)${NC}"
    echo
    echo "请检查缺失的文件并重新运行验证脚本"
    exit 1
fi