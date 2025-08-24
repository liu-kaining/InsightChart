#!/bin/bash

# InsightChart AI 开发环境启动脚本
# 作者: AI Assistant
# 版本: 1.0.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "系统依赖检查完成"
}

# 检查环境变量
check_env() {
    log_info "检查环境变量配置..."
    
    if [[ ! -f ".env" ]]; then
        log_warning ".env 文件不存在，从模板创建..."
        cp .env.example .env
        log_warning "请编辑 .env 文件并配置正确的API密钥"
        log_warning "配置完成后重新运行开发脚本"
        exit 1
    fi
    
    log_success "环境变量检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p backend/temp/uploads
    mkdir -p backend/temp/charts
    mkdir -p logs/backend
    
    log_success "目录创建完成"
}

# 启动开发环境
start_dev() {
    log_info "启动开发环境..."
    
    # 停止现有服务
    log_info "停止现有开发服务..."
    docker-compose -f docker-compose.dev.yml down --remove-orphans || true
    
    # 构建开发镜像
    log_info "构建开发镜像..."
    docker-compose -f docker-compose.dev.yml build --no-cache
    
    # 启动开发服务
    log_info "启动开发服务..."
    docker-compose -f docker-compose.dev.yml up -d
    
    # 等待服务启动
    log_info "等待服务启动完成..."
    sleep 10
    
    # 检查服务状态
    if docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
        log_success "开发环境启动成功！"
        log_info "开发服务器地址: http://localhost:5004"
        log_info "健康检查地址: http://localhost:5004/health"
        log_info "注意：这是单容器开发环境，前端和后端都在同一个容器中"
    else
        log_error "开发环境启动失败，请检查日志"
        docker-compose -f docker-compose.dev.yml logs
        exit 1
    fi
}

# 显示服务状态
show_status() {
    log_info "开发环境状态:"
    docker-compose -f docker-compose.dev.yml ps
    
    log_info "服务日志 (最后20行):"
    docker-compose -f docker-compose.dev.yml logs --tail=20
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 可以在这里添加清理逻辑
}

# 主函数
main() {
    log_info "启动 InsightChart AI 开发环境..."
    log_info "项目地址: https://github.com/your-repo/InsightChart"
    log_info "版本: 1.0.0"
    echo
    
    check_dependencies
    check_env
    create_directories
    start_dev
    show_status
    
    log_success "开发环境启动完成！"
    log_info "使用以下命令管理开发环境:"
    log_info "  查看日志: docker-compose -f docker-compose.dev.yml logs -f"
    log_info "  停止服务: docker-compose -f docker-compose.dev.yml down"
    log_info "  重启服务: docker-compose -f docker-compose.dev.yml restart"
    log_info "  重新构建: docker-compose -f docker-compose.dev.yml build --no-cache"
}

# 错误处理
trap cleanup EXIT

# 解析命令行参数
case "${1:-start}" in
    "start")
        main
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose -f docker-compose.dev.yml logs -f
        ;;
    "stop")
        docker-compose -f docker-compose.dev.yml down
        log_success "开发环境已停止"
        ;;
    "restart")
        docker-compose -f docker-compose.dev.yml restart
        log_success "开发环境已重启"
        ;;
    "rebuild")
        log_info "重新构建开发环境..."
        docker-compose -f docker-compose.dev.yml down
        docker-compose -f docker-compose.dev.yml build --no-cache
        docker-compose -f docker-compose.dev.yml up -d
        log_success "开发环境重新构建完成"
        ;;
    "help")
        echo "InsightChart AI 开发环境启动脚本"
        echo "用法: $0 [命令]"
        echo
        echo "命令:"
        echo "  start    - 启动开发环境 (默认)"
        echo "  status   - 显示服务状态"
        echo "  logs     - 查看服务日志"
        echo "  stop     - 停止开发环境"
        echo "  restart  - 重启开发环境"
        echo "  rebuild  - 重新构建开发环境"
        echo "  help     - 显示帮助信息"
        ;;
    *)
        log_error "未知命令: $1"
        log_info "使用 '$0 help' 查看帮助信息"
        exit 1
        ;;
esac
