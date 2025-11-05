#!/bin/bash

# Vercel 部署监控脚本

echo "🔍 Web3 Search 部署状态检查"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. 检查 GitHub Actions 状态
echo "📊 1. GitHub Actions 工作流状态"
echo "   访问: https://github.com/marovole/Web3search/actions"
echo ""

# 2. 检查前端部署
echo "🌐 2. 检查前端部署..."
FRONTEND_URL="https://web3search.vercel.app"

if curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$FRONTEND_URL" | grep -q "200\|301\|302"; then
    echo -e "   ${GREEN}✅ 前端可访问${NC}: $FRONTEND_URL"
else
    echo -e "   ${YELLOW}⏳ 前端部署中或不可访问${NC}: $FRONTEND_URL"
    echo "   提示: 首次部署可能需要3-5分钟"
fi
echo ""

# 3. 检查 API 健康状态
echo "🔌 3. 检查后端 API..."
API_HEALTH_URL="https://web3search-api.onrender.com/health"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$API_HEALTH_URL")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✅ 后端 API 正常${NC}: $API_HEALTH_URL"
    # 获取详细健康信息
    HEALTH_DATA=$(curl -s --max-time 5 "$API_HEALTH_URL" 2>/dev/null)
    if [ ! -z "$HEALTH_DATA" ]; then
        echo "   响应: $HEALTH_DATA"
    fi
else
    echo -e "   ${RED}❌ 后端 API 不可访问${NC} (HTTP $HTTP_CODE)"
fi
echo ""

# 4. 检查 API 代理
echo "🔗 4. 检查前端 API 代理..."
PROXY_URL="$FRONTEND_URL/api/health"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$PROXY_URL" 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✅ API 代理正常${NC}: $PROXY_URL"
elif [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "000" ]; then
    echo -e "   ${YELLOW}⏳ 前端可能还在部署中${NC}"
else
    echo -e "   ${YELLOW}⚠️  API 代理状态${NC}: HTTP $HTTP_CODE"
fi
echo ""

# 5. DNS 检查
echo "🌍 5. DNS 解析状态..."
if nslookup web3search.vercel.app >/dev/null 2>&1; then
    IP=$(nslookup web3search.vercel.app | grep "Address:" | tail -1 | awk '{print $2}')
    echo -e "   ${GREEN}✅ DNS 解析成功${NC}"
    echo "   IP 地址: $IP"
else
    echo -e "   ${YELLOW}⏳ DNS 传播中${NC}"
fi
echo ""

# 6. Vercel 部署信息
echo "📦 6. Vercel 部署信息"
echo "   Dashboard: https://vercel.com/dashboard"
echo "   生产 URL: $FRONTEND_URL"
echo ""

# 7. 测试建议
echo "🧪 7. 手动测试建议"
echo ""
echo "   测试前端:"
echo "   ${BLUE}curl $FRONTEND_URL${NC}"
echo ""
echo "   测试 API 健康检查:"
echo "   ${BLUE}curl $PROXY_URL${NC}"
echo ""
echo "   测试 Quick Chat:"
echo "   ${BLUE}curl -X POST $FRONTEND_URL/api/v1/chat/quick \\${NC}"
echo "   ${BLUE}  -H 'Content-Type: application/json' \\${NC}"
echo "   ${BLUE}  -d '{\"query\": \"What is Bitcoin?\", \"stream\": false}'${NC}"
echo ""

# 8. 部署状态总结
echo "======================================"
echo "📋 部署状态总结"
echo ""

# 计算整体状态
CHECKS_PASSED=0
CHECKS_TOTAL=3

# 检查前端
if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$FRONTEND_URL" | grep -q "200\|301\|302"; then
    ((CHECKS_PASSED++))
fi

# 检查后端
if [ "$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$API_HEALTH_URL")" = "200" ]; then
    ((CHECKS_PASSED++))
fi

# 检查DNS
if nslookup web3search.vercel.app >/dev/null 2>&1; then
    ((CHECKS_PASSED++))
fi

echo "   通过检查: $CHECKS_PASSED/$CHECKS_TOTAL"
echo ""

if [ $CHECKS_PASSED -eq $CHECKS_TOTAL ]; then
    echo -e "   ${GREEN}🎉 部署完成！所有系统运行正常${NC}"
elif [ $CHECKS_PASSED -gt 0 ]; then
    echo -e "   ${YELLOW}⏳ 部署进行中...部分服务已就绪${NC}"
    echo "   建议: 等待3-5分钟后重新检查"
else
    echo -e "   ${YELLOW}⏳ 部署刚开始...请稍候${NC}"
    echo "   建议: 访问 GitHub Actions 查看构建进度"
fi

echo ""
echo "======================================"
echo "🔗 有用链接"
echo ""
echo "   GitHub Actions:"
echo "   https://github.com/marovole/Web3search/actions"
echo ""
echo "   Vercel Dashboard:"
echo "   https://vercel.com/dashboard"
echo ""
echo "   前端应用:"
echo "   $FRONTEND_URL"
echo ""
echo "   后端 API:"
echo "   https://web3search-api.onrender.com"
echo ""
