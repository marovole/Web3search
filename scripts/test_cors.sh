#!/bin/bash

# CORS 测试脚本
# 用于验证后端 CORS 配置是否正确

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="https://web3search-api.onrender.com"
ORIGIN="https://web3search.pages.dev"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CORS 配置测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 测试 1: 健康检查
echo -e "${YELLOW}[1/4] 测试后端健康状态...${NC}"
HEALTH=$(curl -s "$API_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ 后端服务正常运行${NC}"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo -e "${RED}✗ 后端服务异常${NC}"
    echo "$HEALTH"
fi
echo ""

# 测试 2: OPTIONS 预检请求
echo -e "${YELLOW}[2/4] 测试 OPTIONS 预检请求...${NC}"
OPTIONS_RESPONSE=$(curl -s -I -X OPTIONS \
    -H "Origin: $ORIGIN" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" \
    "$API_URL/api/v1/trending/hotspots" 2>&1)

echo "$OPTIONS_RESPONSE" | grep -i "HTTP"
echo ""

# 检查 Access-Control-Allow-Origin
if echo "$OPTIONS_RESPONSE" | grep -qi "access-control-allow-origin"; then
    ALLOW_ORIGIN=$(echo "$OPTIONS_RESPONSE" | grep -i "access-control-allow-origin")
    echo -e "${GREEN}✓ Access-Control-Allow-Origin: $ALLOW_ORIGIN${NC}"
else
    echo -e "${RED}✗ 缺少 Access-Control-Allow-Origin 头部${NC}"
    echo -e "${YELLOW}这是 CORS 失败的主要原因！${NC}"
fi

# 检查其他 CORS 头部
if echo "$OPTIONS_RESPONSE" | grep -qi "access-control-allow-methods"; then
    echo -e "${GREEN}✓ Access-Control-Allow-Methods 存在${NC}"
fi

if echo "$OPTIONS_RESPONSE" | grep -qi "access-control-allow-credentials"; then
    echo -e "${GREEN}✓ Access-Control-Allow-Credentials 存在${NC}"
fi

if echo "$OPTIONS_RESPONSE" | grep -qi "access-control-allow-headers"; then
    echo -e "${GREEN}✓ Access-Control-Allow-Headers 存在${NC}"
fi
echo ""

# 测试 3: GET 请求
echo -e "${YELLOW}[3/4] 测试 GET 请求...${NC}"
GET_RESPONSE=$(curl -s -I -X GET \
    -H "Origin: $ORIGIN" \
    "$API_URL/api/v1/trending/hotspots?limit=10" 2>&1)

echo "$GET_RESPONSE" | grep -i "HTTP"
echo ""

# 检查 Access-Control-Allow-Origin
if echo "$GET_RESPONSE" | grep -qi "access-control-allow-origin"; then
    ALLOW_ORIGIN=$(echo "$GET_RESPONSE" | grep -i "access-control-allow-origin")
    echo -e "${GREEN}✓ Access-Control-Allow-Origin: $ALLOW_ORIGIN${NC}"
else
    echo -e "${RED}✗ 缺少 Access-Control-Allow-Origin 头部${NC}"
fi
echo ""

# 测试 4: 完整的 CORS 头部
echo -e "${YELLOW}[4/4] 完整的 CORS 响应头部：${NC}"
echo -e "${BLUE}OPTIONS 响应：${NC}"
echo "$OPTIONS_RESPONSE" | grep -i "access-control" || echo "无 CORS 头部"
echo ""

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}测试总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查是否有 Access-Control-Allow-Origin
if echo "$OPTIONS_RESPONSE" | grep -qi "access-control-allow-origin.*$ORIGIN" || \
   echo "$GET_RESPONSE" | grep -qi "access-control-allow-origin.*$ORIGIN"; then
    echo -e "${GREEN}✅ CORS 配置正确！${NC}"
    echo -e "${GREEN}前端应该可以成功调用 API${NC}"
else
    echo -e "${RED}❌ CORS 配置有问题！${NC}"
    echo ""
    echo -e "${YELLOW}可能的原因：${NC}"
    echo "1. Render 环境变量 CORS_ORIGINS 不包含 $ORIGIN"
    echo "2. 服务还没有完全重启（等待 2-3 分钟）"
    echo "3. 环境变量格式不正确"
    echo ""
    echo -e "${YELLOW}建议操作：${NC}"
    echo "1. 在 Render Dashboard 确认 CORS_ORIGINS 值为："
    echo "   $ORIGIN"
    echo ""
    echo "2. 手动重启服务："
    echo "   Render Dashboard → Manual Deploy → Clear build cache & deploy"
    echo ""
    echo "3. 等待 2-3 分钟后重新运行此脚本"
fi
echo ""

# 显示当前 Render 配置建议
echo -e "${BLUE}建议的 Render 环境变量配置：${NC}"
echo -e "${YELLOW}CORS_ORIGINS=${NC}"
echo "$ORIGIN,https://web3-search.netlify.app,https://web3search.vercel.app,https://web3search.ai,https://www.web3search.ai"
echo ""
