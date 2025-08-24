#!/bin/bash

# 测试文件清理功能脚本

echo "=== InsightChart AI 文件清理功能测试 ==="
echo

# 设置API基础URL
API_BASE="http://localhost:5004/api"

# 步骤1：登录获取token
echo "1. 正在登录获取token..."
TOKEN_RESPONSE=$(curl -s -H "Content-Type: application/json" -X POST "$API_BASE/auth/login" -d '{"password": "lkn@qxmy"}')
TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    echo "响应: $TOKEN_RESPONSE"
    exit 1
fi

echo "✅ 登录成功，获得token"
echo

# 步骤2：检查清理服务状态
echo "2. 检查清理服务状态..."
STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/cleanup/status")
echo "清理服务状态: $STATUS_RESPONSE"
echo

# 步骤3：检查清理配置
echo "3. 检查清理配置..."
CONFIG_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/cleanup/config")
echo "清理配置: $CONFIG_RESPONSE"
echo

# 步骤4：创建一些测试文件
echo "4. 创建测试文件..."
mkdir -p backend/temp/uploads/test_session_1
mkdir -p backend/temp/uploads/test_session_2
echo '{"test": "data1"}' > backend/temp/charts/test_session_1.json
echo '{"test": "data2"}' > backend/temp/charts/test_session_2.json
echo "test file" > backend/temp/uploads/test_session_1/test.csv
echo "test file" > backend/temp/uploads/test_session_2/test.csv

echo "✅ 测试文件已创建:"
ls -la backend/temp/uploads/
ls -la backend/temp/charts/
echo

# 步骤5：触发手动清理
echo "5. 触发手动清理..."
CLEANUP_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" -X POST "$API_BASE/cleanup/force")
echo "清理结果: $CLEANUP_RESPONSE"
echo

# 步骤6：验证文件是否被清理
echo "6. 验证文件清理结果..."
echo "uploads目录内容:"
ls -la backend/temp/uploads/
echo "charts目录内容:"
ls -la backend/temp/charts/
echo

# 步骤7：再次检查清理服务状态
echo "7. 清理后服务状态..."
FINAL_STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/cleanup/status")
echo "最终状态: $FINAL_STATUS"
echo

echo "=== 测试完成 ==="
echo "💡 提示：文件清理服务配置为每5分钟自动运行一次"
echo "📁 临时文件目录: backend/temp/"
echo "🔄 自动清理间隔: 5分钟 (300秒)"