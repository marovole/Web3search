#!/bin/bash

# 生产环境快速测试脚本
# 测试所有核心功能是否正常工作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# API URLs
API_URL="https://web3search-api.marovole.workers.dev"
FRONTEND_URL="https://web3search.pages.dev"

echo ""
echo "🧪 Web3search 生产环境测试"
echo "================================"
echo ""

# 测试计数器
PASSED=0
FAILED=0

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    echo -n "Testing $name... "

    response=$(curl -s -w "\n%{http_code}" "$url" -m 10)
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $status_code, expected $expected_status)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 测试带JSON数据的POST请求
test_post_endpoint() {
    local name=$1
    local url=$2
    local data=$3
    local expected_status=${4:-200}

    echo -n "Testing $name... "

    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$data" \
        -m 30)
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))
        echo "Response preview: $(echo "$body" | head -c 100)..."
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $status_code, expected $expected_status)"
        echo "Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "📡 测试后端API端点"
echo "--------------------------------"

# 1. 健康检查
test_endpoint "Health Check" "$API_URL/api/v1/health"

# 2. 搜索自动完成
test_endpoint "Search Autocomplete" "$API_URL/api/v1/search/autocomplete?q=bitcoin"

# 3. Quick Chat（非流式）
test_post_endpoint "Quick Chat API" "$API_URL/api/v1/chat/quick-chat" \
    '{"query":"What is Bitcoin?","stream":false}'

# 4. Deep Research创建
test_post_endpoint "Deep Research Create" "$API_URL/api/v1/deep-research" \
    '{"symbol":"BTC","query":"Research Bitcoin"}'

echo ""
echo "🌐 测试前端访问"
echo "--------------------------------"

# 5. 前端页面
test_endpoint "Frontend Page" "$FRONTEND_URL"

echo ""
echo "================================"
echo "📊 测试结果统计"
echo "--------------------------------"
echo -e "${GREEN}✅ 通过: $PASSED${NC}"
echo -e "${RED}❌ 失败: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！系统可以投入使用。${NC}"
    echo ""
    echo "🚀 访问你的应用:"
    echo "  前端: $FRONTEND_URL"
    echo "  API:  $API_URL"
    exit 0
else
    echo -e "${RED}⚠️  有 $FAILED 个测试失败，请检查配置。${NC}"
    echo ""
    echo "🔧 可能的问题:"
    echo "  1. API密钥未配置或配置错误"
    echo "  2. 数据库连接问题"
    echo "  3. 网络连接问题"
    echo ""
    echo "💡 解决方法:"
    echo "  - 运行配置脚本: cd workers-api && ../scripts/quick-setup.sh"
    echo "  - 检查日志: wrangler tail"
    echo "  - 查看文档: docs/TROUBLESHOOTING.md"
    exit 1
fi
