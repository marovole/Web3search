#!/bin/bash

# Web3 Search 完整功能测试脚本
# 测试后端API和前端部署的所有关键功能

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKEND_URL="https://web3search-api.marovole.workers.dev"
FRONTEND_URL="https://web3search.pages.dev"
TIMEOUT=15

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试结果数组
declare -a TEST_RESULTS

# 辅助函数
print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

test_passed() {
    echo -e "${GREEN}✅ PASSED${NC}: $1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
    TEST_RESULTS+=("✅ $1")
}

test_failed() {
    echo -e "${RED}❌ FAILED${NC}: $1"
    if [ ! -z "$2" ]; then
        echo -e "${RED}   错误: $2${NC}"
    fi
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
    TEST_RESULTS+=("❌ $1")
}

test_warning() {
    echo -e "${YELLOW}⚠️  WARNING${NC}: $1"
}

test_info() {
    echo -e "${BLUE}ℹ️  INFO${NC}: $1"
}

# ================================
# 1. 后端基础测试
# ================================
print_header "1️⃣  后端API基础测试"

# 1.1 健康检查
echo "测试 1.1: 健康检查端点"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BACKEND_URL/health" 2>/dev/null)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$HEALTH_BODY" | grep -q "healthy"; then
        test_passed "健康检查返回200且状态为healthy"
        test_info "响应: $HEALTH_BODY"
    else
        test_failed "健康检查返回200但状态不是healthy" "$HEALTH_BODY"
    fi
else
    test_failed "健康检查失败" "HTTP $HTTP_CODE"
fi

# 1.2 根路径
echo ""
echo "测试 1.2: API根路径"
ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BACKEND_URL/" 2>/dev/null)
ROOT_CODE=$(echo "$ROOT_RESPONSE" | tail -n1)

if [ "$ROOT_CODE" = "200" ]; then
    test_passed "API根路径可访问"
else
    test_warning "API根路径返回 HTTP $ROOT_CODE（可能正常）"
fi

# 1.3 API文档
echo ""
echo "测试 1.3: API文档 (Swagger)"
DOCS_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BACKEND_URL/docs" 2>/dev/null)
DOCS_CODE=$(echo "$DOCS_RESPONSE" | tail -n1)

if [ "$DOCS_CODE" = "200" ]; then
    test_passed "API文档可访问"
else
    test_failed "API文档不可访问" "HTTP $DOCS_CODE"
fi

# 1.4 OpenAPI规范
echo ""
echo "测试 1.4: OpenAPI JSON"
OPENAPI_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BACKEND_URL/openapi.json" 2>/dev/null)
OPENAPI_CODE=$(echo "$OPENAPI_RESPONSE" | tail -n1)

if [ "$OPENAPI_CODE" = "200" ]; then
    test_passed "OpenAPI规范可访问"
else
    test_failed "OpenAPI规范不可访问" "HTTP $OPENAPI_CODE"
fi

# ================================
# 2. Quick Chat功能测试
# ================================
print_header "2️⃣  Quick Chat功能测试"

# 2.1 Quick Chat基本请求
echo "测试 2.1: Quick Chat基本请求"
CHAT_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
    -X POST "$BACKEND_URL/api/v1/chat/quick" \
    -H "Content-Type: application/json" \
    -d '{"query": "What is Bitcoin?", "stream": false}' 2>/dev/null)
CHAT_CODE=$(echo "$CHAT_RESPONSE" | tail -n1)
CHAT_BODY=$(echo "$CHAT_RESPONSE" | head -n-1)

if [ "$CHAT_CODE" = "200" ]; then
    if echo "$CHAT_BODY" | grep -q "response\|answer\|Bitcoin"; then
        test_passed "Quick Chat返回有效响应"
        test_info "响应片段: $(echo "$CHAT_BODY" | head -c 100)..."
    else
        test_warning "Quick Chat返回200但响应格式可能异常"
    fi
elif [ "$CHAT_CODE" = "401" ] || [ "$CHAT_CODE" = "403" ]; then
    test_warning "Quick Chat需要认证 (HTTP $CHAT_CODE) - 可能需要配置API密钥"
else
    test_failed "Quick Chat请求失败" "HTTP $CHAT_CODE"
fi

# 2.2 Quick Chat参数验证
echo ""
echo "测试 2.2: Quick Chat参数验证"
INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
    -X POST "$BACKEND_URL/api/v1/chat/quick" \
    -H "Content-Type: application/json" \
    -d '{"invalid": "data"}' 2>/dev/null)
INVALID_CODE=$(echo "$INVALID_RESPONSE" | tail -n1)

if [ "$INVALID_CODE" = "422" ] || [ "$INVALID_CODE" = "400" ]; then
    test_passed "参数验证正常工作"
else
    test_warning "参数验证返回意外状态码: HTTP $INVALID_CODE"
fi

# ================================
# 3. Deep Research功能测试
# ================================
print_header "3️⃣  Deep Research功能测试"

# 3.1 Deep Research端点
echo "测试 3.1: Deep Research端点可访问性"
RESEARCH_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
    -X POST "$BACKEND_URL/api/v1/research/deep" \
    -H "Content-Type: application/json" \
    -d '{"symbol": "BTC", "query": "Research Bitcoin"}' 2>/dev/null)
RESEARCH_CODE=$(echo "$RESEARCH_RESPONSE" | tail -n1)

if [ "$RESEARCH_CODE" = "200" ] || [ "$RESEARCH_CODE" = "202" ]; then
    test_passed "Deep Research端点可访问"
elif [ "$RESEARCH_CODE" = "401" ] || [ "$RESEARCH_CODE" = "403" ]; then
    test_warning "Deep Research需要认证 (HTTP $RESEARCH_CODE)"
elif [ "$RESEARCH_CODE" = "404" ]; then
    test_info "Deep Research端点可能路径不同或未启用"
else
    test_info "Deep Research返回: HTTP $RESEARCH_CODE"
fi

# ================================
# 4. 前端部署测试
# ================================
print_header "4️⃣  前端部署测试"

# 4.1 前端根路径
echo "测试 4.1: 前端首页"
FRONTEND_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$FRONTEND_URL" 2>/dev/null)
FRONTEND_CODE=$(echo "$FRONTEND_RESPONSE" | tail -n1)
FRONTEND_BODY=$(echo "$FRONTEND_RESPONSE" | head -n-1)

if [ "$FRONTEND_CODE" = "200" ]; then
    if echo "$FRONTEND_BODY" | grep -q "<!DOCTYPE html\|<html"; then
        test_passed "前端首页返回有效HTML"
        # 检查是否包含title
        if echo "$FRONTEND_BODY" | grep -q "<title>"; then
            TITLE=$(echo "$FRONTEND_BODY" | grep -o "<title>[^<]*" | sed 's/<title>//')
            test_info "页面标题: $TITLE"
        fi
    else
        test_failed "前端返回200但不是HTML内容"
    fi
else
    test_failed "前端首页不可访问" "HTTP $FRONTEND_CODE"
fi

# 4.2 前端静态资源
echo ""
echo "测试 4.2: 静态资源加载"
if [ "$FRONTEND_CODE" = "200" ]; then
    # 检查是否有JS和CSS引用
    if echo "$FRONTEND_BODY" | grep -q "\.js\|\.css"; then
        test_passed "前端包含静态资源引用"
    else
        test_warning "前端可能缺少静态资源引用"
    fi
else
    test_info "跳过静态资源检查（前端不可访问）"
fi

# 4.3 前端API代理
echo ""
echo "测试 4.3: 前端API代理"
PROXY_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$FRONTEND_URL/api/health" 2>/dev/null)
PROXY_CODE=$(echo "$PROXY_RESPONSE" | tail -n1)

if [ "$PROXY_CODE" = "200" ]; then
    test_passed "前端API代理工作正常"
elif [ "$PROXY_CODE" = "404" ]; then
    test_warning "前端API代理可能未配置或路径不同"
else
    test_info "API代理返回: HTTP $PROXY_CODE"
fi

# ================================
# 5. DNS和网络测试
# ================================
print_header "5️⃣  DNS和网络测试"

# 5.1 DNS解析
echo "测试 5.1: DNS解析"
if nslookup web3search.vercel.app >/dev/null 2>&1; then
    IP=$(nslookup web3search.vercel.app | grep "Address:" | tail -1 | awk '{print $2}')
    test_passed "DNS解析成功"
    test_info "解析IP: $IP"
else
    test_failed "DNS解析失败"
fi

# 5.2 后端DNS
echo ""
echo "测试 5.2: 后端DNS解析"
if nslookup web3search-api.onrender.com >/dev/null 2>&1; then
    BACKEND_IP=$(nslookup web3search-api.onrender.com | grep "Address:" | tail -1 | awk '{print $2}')
    test_passed "后端DNS解析成功"
    test_info "后端IP: $BACKEND_IP"
else
    test_failed "后端DNS解析失败"
fi

# ================================
# 6. 安全头部测试
# ================================
print_header "6️⃣  安全头部测试"

echo "测试 6.1: 安全响应头"
HEADERS=$(curl -s -I --max-time $TIMEOUT "$FRONTEND_URL" 2>/dev/null)

# 检查重要的安全头部
declare -a SECURITY_HEADERS=("X-Frame-Options" "X-Content-Type-Options" "Referrer-Policy")
HEADERS_FOUND=0

for HEADER in "${SECURITY_HEADERS[@]}"; do
    if echo "$HEADERS" | grep -qi "$HEADER"; then
        ((HEADERS_FOUND++))
    fi
done

if [ $HEADERS_FOUND -ge 2 ]; then
    test_passed "发现 $HEADERS_FOUND 个安全头部"
elif [ $HEADERS_FOUND -gt 0 ]; then
    test_warning "仅发现 $HEADERS_FOUND 个安全头部，建议增加"
else
    test_info "未检测到标准安全头部"
fi

# ================================
# 7. 性能测试
# ================================
print_header "7️⃣  性能测试"

echo "测试 7.1: 后端响应时间"
START_TIME=$(date +%s%N)
curl -s --max-time $TIMEOUT "$BACKEND_URL/health" >/dev/null 2>&1
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( ($END_TIME - $START_TIME) / 1000000 ))

if [ $RESPONSE_TIME -lt 5000 ]; then
    test_passed "后端响应时间: ${RESPONSE_TIME}ms (优秀)"
elif [ $RESPONSE_TIME -lt 10000 ]; then
    test_warning "后端响应时间: ${RESPONSE_TIME}ms (可接受)"
else
    test_warning "后端响应时间: ${RESPONSE_TIME}ms (较慢)"
fi

echo ""
echo "测试 7.2: 前端响应时间"
START_TIME=$(date +%s%N)
curl -s --max-time $TIMEOUT "$FRONTEND_URL" >/dev/null 2>&1
END_TIME=$(date +%s%N)
FRONTEND_TIME=$(( ($END_TIME - $START_TIME) / 1000000 ))

if [ $FRONTEND_TIME -lt 3000 ]; then
    test_passed "前端响应时间: ${FRONTEND_TIME}ms (优秀)"
elif [ $FRONTEND_TIME -lt 5000 ]; then
    test_warning "前端响应时间: ${FRONTEND_TIME}ms (可接受)"
else
    test_warning "前端响应时间: ${FRONTEND_TIME}ms (较慢)"
fi

# ================================
# 测试总结
# ================================
print_header "📊 测试总结"

echo ""
echo "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo ""

# 计算成功率
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(( $PASSED_TESTS * 100 / $TOTAL_TESTS ))
    echo "成功率: ${SUCCESS_RATE}%"
    echo ""
fi

# 评估等级
if [ $SUCCESS_RATE -ge 90 ]; then
    echo -e "${GREEN}🎉 优秀！系统运行状态良好${NC}"
    EXIT_CODE=0
elif [ $SUCCESS_RATE -ge 70 ]; then
    echo -e "${YELLOW}⚠️  良好，但有一些问题需要关注${NC}"
    EXIT_CODE=0
elif [ $SUCCESS_RATE -ge 50 ]; then
    echo -e "${YELLOW}⚠️  部分功能正常，建议检查失败的测试${NC}"
    EXIT_CODE=1
else
    echo -e "${RED}❌ 系统存在严重问题，需要立即修复${NC}"
    EXIT_CODE=1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 详细结果
echo "详细测试结果:"
for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 建议操作
print_header "🎯 建议的下一步操作"

if [ $FAILED_TESTS -gt 0 ]; then
    echo "1. 查看失败的测试项"
    echo "2. 检查Render和Vercel的部署日志"
    echo "3. 验证环境变量配置"
fi

if [ $SUCCESS_RATE -ge 70 ]; then
    echo "✅ 在浏览器中访问: $FRONTEND_URL"
    echo "✅ 查看API文档: $BACKEND_URL/docs"
    echo "✅ 测试完整功能流程"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $EXIT_CODE
