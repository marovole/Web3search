#!/bin/bash

# Cloudflare Pages 部署测试脚本
# 用于验证部署是否正常工作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SITE_URL="https://web3search.pages.dev"
TEST_PAGE="${SITE_URL}/test.html"
API_HEALTH="${SITE_URL}/api/health"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cloudflare Pages 部署测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 测试 1: DNS 解析
echo -e "${YELLOW}[1/5] 测试 DNS 解析...${NC}"
if nslookup web3search.pages.dev > /dev/null 2>&1; then
    IP=$(nslookup web3search.pages.dev | grep "Address:" | tail -1 | awk '{print $2}')
    echo -e "${GREEN}✓ DNS 解析成功: ${IP}${NC}"
else
    echo -e "${RED}✗ DNS 解析失败${NC}"
    exit 1
fi
echo ""

# 测试 2: 测试页面访问
echo -e "${YELLOW}[2/5] 测试部署测试页面...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${TEST_PAGE}" || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ 测试页面访问成功 (${TEST_PAGE})${NC}"
    echo -e "  HTTP 状态码: ${HTTP_CODE}"
else
    echo -e "${RED}✗ 测试页面访问失败${NC}"
    echo -e "  HTTP 状态码: ${HTTP_CODE}"
    echo -e "${YELLOW}  提示: 这可能意味着基础部署有问题${NC}"
fi
echo ""

# 测试 3: 主页访问
echo -e "${YELLOW}[3/5] 测试主页访问...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SITE_URL}/" || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ 主页访问成功 (${SITE_URL}/)${NC}"
    echo -e "  HTTP 状态码: ${HTTP_CODE}"
    
    # 检查内容
    CONTENT=$(curl -s "${SITE_URL}/" | head -20)
    if echo "$CONTENT" | grep -q "Web3 AI Search" || echo "$CONTENT" | grep -q "root"; then
        echo -e "${GREEN}✓ 页面内容正常${NC}"
    else
        echo -e "${YELLOW}⚠ 页面内容可能异常${NC}"
    fi
else
    echo -e "${RED}✗ 主页访问失败${NC}"
    echo -e "  HTTP 状态码: ${HTTP_CODE}"
fi
echo ""

# 测试 4: 静态资源
echo -e "${YELLOW}[4/5] 测试静态资源加载...${NC}"
# 尝试获取主页并检查资源引用
RESOURCES=$(curl -s "${SITE_URL}/" | grep -oE '(src|href)="[^"]*\.(js|css)"' | wc -l | xargs)
if [ "$RESOURCES" -gt "0" ]; then
    echo -e "${GREEN}✓ 发现 ${RESOURCES} 个静态资源引用${NC}"
else
    echo -e "${YELLOW}⚠ 未发现静态资源引用${NC}"
fi
echo ""

# 测试 5: API 代理
echo -e "${YELLOW}[5/5] 测试 API 代理...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_HEALTH}" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ API 代理工作正常${NC}"
    echo -e "  健康检查: ${API_HEALTH}"
    API_RESPONSE=$(curl -s "${API_HEALTH}" 2>/dev/null || echo "{}")
    echo -e "  响应: ${API_RESPONSE}"
else
    echo -e "${YELLOW}⚠ API 代理可能未配置或后端未响应${NC}"
    echo -e "  HTTP 状态码: ${HTTP_CODE}"
    echo -e "  这是正常的，如果后端未部署或 _redirects 未生效${NC}"
fi
echo ""

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}测试总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 综合评估
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ 部署状态: 正常${NC}"
    echo -e ""
    echo -e "您可以访问以下 URL:"
    echo -e "  主站: ${SITE_URL}/"
    echo -e "  测试页面: ${TEST_PAGE}"
    echo -e ""
else
    echo -e "${RED}✗ 部署状态: 异常${NC}"
    echo -e ""
    echo -e "问题排查建议:"
    echo -e "1. 检查 Cloudflare Dashboard 中的构建日志"
    echo -e "2. 确认构建配置正确："
    echo -e "   - Build command: cd frontend && npm ci && npm run build"
    echo -e "   - Build output: frontend/dist"
    echo -e "3. 查看详细文档: CLOUDFLARE_PAGES_SETUP.md"
    echo -e ""
    exit 1
fi

# 额外的诊断信息
echo -e "${BLUE}附加诊断信息:${NC}"
echo -e "1. 使用不同 DNS 测试解析:"
echo -e "   nslookup web3search.pages.dev 1.1.1.1"
echo -e ""
echo -e "2. 在浏览器中测试 (避免命令行网络问题):"
echo -e "   ${SITE_URL}/"
echo -e ""
echo -e "3. 查看浏览器控制台 (F12) 检查错误"
echo -e ""
echo -e "4. 检查 Cloudflare Dashboard:"
echo -e "   https://dash.cloudflare.com/"
echo -e ""
