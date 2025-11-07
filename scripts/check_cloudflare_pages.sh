#!/bin/bash

# Cloudflare Pages 部署状态检查脚本

set -e

echo "🔍 检查 Cloudflare Pages 部署状态..."
echo ""

# 检查网站是否可访问
echo "1. 检查网站可访问性..."
if curl -s -o /dev/null -w "%{http_code}" https://web3search.pages.dev | grep -q "200\|301\|302"; then
    echo "   ✅ 网站可访问"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://web3search.pages.dev)
    echo "   HTTP 状态码: $HTTP_CODE"
else
    echo "   ❌ 网站无法访问"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://web3search.pages.dev)
    echo "   HTTP 状态码: $HTTP_CODE"
fi

echo ""
echo "2. 检查首页内容..."
RESPONSE=$(curl -s https://web3search.pages.dev | head -20)
if echo "$RESPONSE" | grep -q "html\|<!DOCTYPE"; then
    echo "   ✅ 返回 HTML 内容"
    echo "   前20行内容:"
    echo "$RESPONSE" | head -5
else
    echo "   ❌ 未返回 HTML 内容"
    echo "   响应内容: $RESPONSE"
fi

echo ""
echo "3. 检查 API 代理..."
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://web3search.pages.dev/api/health 2>/dev/null || echo "000")
if [ "$API_RESPONSE" = "200" ] || [ "$API_RESPONSE" = "301" ] || [ "$API_RESPONSE" = "302" ]; then
    echo "   ✅ API 代理工作正常"
else
    echo "   ⚠️  API 代理可能有问题 (HTTP $API_RESPONSE)"
fi

echo ""
echo "4. 检查构建输出目录..."
if [ -d "frontend/dist" ]; then
    echo "   ✅ frontend/dist 目录存在"
    FILE_COUNT=$(find frontend/dist -type f | wc -l)
    echo "   文件数量: $FILE_COUNT"
    
    if [ -f "frontend/dist/index.html" ]; then
        echo "   ✅ index.html 存在"
    else
        echo "   ❌ index.html 不存在"
    fi
    
    if [ -f "frontend/dist/_redirects" ]; then
        echo "   ✅ _redirects 文件存在于构建输出"
    else
        echo "   ⚠️  _redirects 文件不存在于构建输出"
    fi
else
    echo "   ❌ frontend/dist 目录不存在"
    echo "   请先运行: cd frontend && npm run build"
fi

echo ""
echo "5. 检查 Cloudflare Pages 配置文件..."
if [ -f "frontend/public/_redirects" ]; then
    echo "   ✅ _redirects 文件存在"
else
    echo "   ❌ _redirects 文件不存在"
fi

if [ -f "frontend/public/_headers" ]; then
    echo "   ✅ _headers 文件存在"
else
    echo "   ⚠️  _headers 文件不存在（可选）"
fi

echo ""
echo "📋 建议的检查步骤:"
echo "1. 登录 Cloudflare Dashboard: https://dash.cloudflare.com/"
echo "2. 进入 Pages → web3search 项目"
echo "3. 查看最新的部署日志"
echo "4. 检查构建配置:"
echo "   - 构建命令: cd frontend && npm install && npm run build"
echo "   - 输出目录: frontend/dist"
echo "   - 根目录: (留空)"
echo ""
echo "5. 如果部署失败，检查:"
echo "   - Node.js 版本是否为 18"
echo "   - 环境变量是否配置正确"
echo "   - 构建日志中的错误信息"


