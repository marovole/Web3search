#!/bin/bash

# Web3search 快速配置脚本
# 用于快速配置生产环境所需的API密钥

set -e

echo "🚀 Web3search 快速配置向导"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在workers-api目录
if [ ! -f "wrangler.toml" ]; then
    echo -e "${RED}❌ 错误: 请在 workers-api 目录下运行此脚本${NC}"
    echo "执行: cd workers-api && ../scripts/quick-setup.sh"
    exit 1
fi

echo "📋 当前需要配置的API密钥:"
echo "--------------------------------"
echo "1. Supabase 数据库 (已有)"
echo "2. OpenRouter AI服务 (已有)"
echo "3. 搜索提供商 (至少1个) ❌"
echo ""

echo -e "${YELLOW}⚠️  注意: 你需要至少配置一个搜索提供商API密钥${NC}"
echo ""
echo "推荐的搜索提供商（按优先级）:"
echo "  1. Brave Search - 免费，每月2000次查询"
echo "     注册: https://brave.com/search/api/"
echo ""
echo "  2. Tavily - 免费，每月1000次查询"
echo "     注册: https://tavily.com/"
echo ""
echo "  3. Serper (Google) - 免费，每月2500次查询"
echo "     注册: https://serper.dev/"
echo ""

read -p "是否现在配置搜索API密钥? (y/n): " configure_now

if [ "$configure_now" != "y" ]; then
    echo ""
    echo "⏭️  跳过配置。稍后可以使用以下命令手动配置:"
    echo ""
    echo "  cd workers-api"
    echo "  wrangler secret put BRAVE_SEARCH_API_KEY"
    echo "  wrangler secret put TAVILY_API_KEY"
    echo "  wrangler secret put SERPER_API_KEY"
    echo ""
    exit 0
fi

echo ""
echo "🔐 开始配置API密钥..."
echo "--------------------------------"

# 配置 Supabase（从.dev.vars读取）
echo ""
echo "1️⃣  配置 Supabase 数据库..."
if [ -f ".dev.vars" ]; then
    SUPABASE_URL=$(grep SUPABASE_URL .dev.vars | cut -d '=' -f2)
    SUPABASE_KEY=$(grep SUPABASE_ANON_KEY .dev.vars | cut -d '=' -f2)

    echo "$SUPABASE_URL" | wrangler secret put SUPABASE_URL
    echo "$SUPABASE_KEY" | wrangler secret put SUPABASE_ANON_KEY
    echo -e "${GREEN}✅ Supabase 配置完成${NC}"
else
    echo -e "${YELLOW}⚠️  .dev.vars 文件不存在，请手动配置${NC}"
fi

# 配置 OpenRouter
echo ""
echo "2️⃣  配置 OpenRouter API..."
if [ -f ".dev.vars" ]; then
    OPENROUTER_KEY=$(grep OPENROUTER_API_KEY .dev.vars | cut -d '=' -f2)
    echo "$OPENROUTER_KEY" | wrangler secret put OPENROUTER_API_KEY
    echo -e "${GREEN}✅ OpenRouter 配置完成${NC}"
else
    echo -e "${YELLOW}⚠️  请手动配置 OpenRouter API Key${NC}"
fi

# 配置搜索提供商
echo ""
echo "3️⃣  配置搜索提供商..."
echo ""

# Brave Search
read -p "是否配置 Brave Search API Key? (y/n): " config_brave
if [ "$config_brave" = "y" ]; then
    echo "请输入 Brave Search API Key:"
    wrangler secret put BRAVE_SEARCH_API_KEY
    echo -e "${GREEN}✅ Brave Search 配置完成${NC}"
fi

echo ""
# Tavily
read -p "是否配置 Tavily API Key? (y/n): " config_tavily
if [ "$config_tavily" = "y" ]; then
    echo "请输入 Tavily API Key:"
    wrangler secret put TAVILY_API_KEY
    echo -e "${GREEN}✅ Tavily 配置完成${NC}"
fi

echo ""
# Serper
read -p "是否配置 Serper API Key? (y/n): " config_serper
if [ "$config_serper" = "y" ]; then
    echo "请输入 Serper API Key:"
    wrangler secret put SERPER_API_KEY
    echo -e "${GREEN}✅ Serper 配置完成${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}🎉 配置完成！${NC}"
echo ""
echo "📝 下一步:"
echo "  1. 部署到生产环境: npm run deploy"
echo "  2. 验证部署状态: ../scripts/test-production.sh"
echo "  3. 访问前端: https://web3search.pages.dev"
echo ""
echo "如果遇到问题，查看文档: ../docs/DEPLOYMENT.md"
echo ""
