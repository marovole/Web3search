#!/bin/bash

# ================================
# Railway一键部署脚本
# ================================

set -e

echo "🚀 开始部署Web3搜索引擎到Railway..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI未安装${NC}"
    echo "请运行: npm install -g @railway/cli"
    exit 1
fi

echo -e "${GREEN}✅ Railway CLI已安装 ($(railway --version))${NC}"
echo ""

# 检查登录状态
echo "🔐 检查Railway登录状态..."
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  未登录Railway${NC}"
    echo "请在新终端窗口运行: railway login"
    echo ""
    read -p "完成登录后按回车继续..."

    # 再次检查
    if ! railway whoami &> /dev/null; then
        echo -e "${RED}❌ 仍未登录，部署中止${NC}"
        exit 1
    fi
fi

RAILWAY_USER=$(railway whoami 2>/dev/null || echo "Unknown")
echo -e "${GREEN}✅ 已登录为: $RAILWAY_USER${NC}"
echo ""

# 检查Git状态
echo "📦 检查Git仓库..."
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${GREEN}✅ 工作目录干净${NC}"
else
    echo -e "${YELLOW}⚠️  有未提交的更改${NC}"
    read -p "是否提交所有更改? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "chore: 部署前更新

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
        echo -e "${GREEN}✅ 更改已提交${NC}"
    fi
fi
echo ""

# 检查是否已有项目
echo "🔍 检查Railway项目..."
if railway status &> /dev/null; then
    echo -e "${YELLOW}⚠️  检测到已有项目:${NC}"
    railway status
    echo ""
    read -p "是否使用现有项目? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "创建新项目..."
        railway init
    fi
else
    echo "创建新Railway项目..."
    railway init
fi
echo ""

# 检查并添加PostgreSQL
echo "🗄️  配置PostgreSQL..."
if railway variables get DATABASE_URL &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL已配置${NC}"
else
    echo "添加PostgreSQL数据库..."
    railway add --database postgres
    echo -e "${GREEN}✅ PostgreSQL已添加${NC}"
fi
echo ""

# 检查并添加Redis
echo "🔴 配置Redis..."
if railway variables get REDIS_URL &> /dev/null; then
    echo -e "${GREEN}✅ Redis已配置${NC}"
else
    echo "添加Redis数据库..."
    railway add --database redis
    echo -e "${GREEN}✅ Redis已添加${NC}"
fi
echo ""

# 配置环境变量
echo "⚙️  配置环境变量..."

# 检查OPENROUTER_API_KEY
CURRENT_KEY=$(railway variables get OPENROUTER_API_KEY 2>/dev/null || echo "")
if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" == "your_openrouter_api_key_here" ]; then
    echo -e "${RED}⚠️  OPENROUTER_API_KEY未配置或使用默认值${NC}"
    echo ""
    echo "请访问 https://openrouter.ai 获取免费API Key"
    echo ""
    read -p "请输入您的OpenRouter API Key: " API_KEY

    if [ -z "$API_KEY" ]; then
        echo -e "${RED}❌ API Key不能为空${NC}"
        exit 1
    fi

    railway variables set OPENROUTER_API_KEY="$API_KEY"
    echo -e "${GREEN}✅ OPENROUTER_API_KEY已设置${NC}"
else
    echo -e "${GREEN}✅ OPENROUTER_API_KEY已配置 (${CURRENT_KEY:0:10}...)${NC}"
fi

# 设置其他环境变量
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set LOG_LEVEL=INFO

# CORS配置
CURRENT_CORS=$(railway variables get CORS_ORIGINS 2>/dev/null || echo "")
if [ -z "$CURRENT_CORS" ]; then
    echo ""
    read -p "是否配置CORS域名? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入前端域名 (例: https://your-app.vercel.app): " CORS_DOMAIN
        if [ ! -z "$CORS_DOMAIN" ]; then
            railway variables set CORS_ORIGINS="$CORS_DOMAIN"
            echo -e "${GREEN}✅ CORS已配置${NC}"
        fi
    else
        railway variables set CORS_ORIGINS="*"
        echo -e "${YELLOW}⚠️  CORS设置为允许所有域名 (仅用于开发)${NC}"
    fi
else
    echo -e "${GREEN}✅ CORS已配置: $CURRENT_CORS${NC}"
fi

echo ""
echo -e "${GREEN}✅ 环境变量配置完成${NC}"
echo ""

# 显示当前配置
echo "📋 当前配置:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
railway variables | grep -E "ENVIRONMENT|DATABASE_URL|REDIS_URL|OPENROUTER|CORS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 部署
echo "🚢 开始部署..."
read -p "确认开始部署? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}部署已取消${NC}"
    exit 0
fi

echo ""
echo "正在部署到Railway..."
railway up

echo ""
echo -e "${GREEN}✅ 代码已上传到Railway${NC}"
echo ""
echo "⏳ 等待构建和部署完成..."
echo "   (通常需要2-3分钟)"
echo ""

# 生成域名（如果还没有）
echo "🌐 配置域名..."
if railway domain 2>&1 | grep -q "https://"; then
    DOMAIN=$(railway domain)
    echo -e "${GREEN}✅ 域名已配置${NC}"
else
    echo "生成Railway域名..."
    DOMAIN=$(railway domain)
    echo -e "${GREEN}✅ 域名已生成${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 部署地址: $DOMAIN"
echo ""
echo "🔗 快速链接:"
echo "   - API文档:    $DOMAIN/docs"
echo "   - 健康检查:   $DOMAIN/health"
echo "   - Railway控制台: https://railway.app/dashboard"
echo ""
echo "📊 查看日志:"
echo "   railway logs"
echo ""
echo "🧪 测试API:"
echo "   curl $DOMAIN/health"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 自动测试健康检查
echo "🧪 运行健康检查..."
sleep 10  # 等待服务启动

if curl -s -f "$DOMAIN/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康检查通过！${NC}"
    echo ""
    curl -s "$DOMAIN/health" | python3 -m json.tool
else
    echo -e "${YELLOW}⚠️  健康检查失败（服务可能仍在启动中）${NC}"
    echo "请稍后访问: $DOMAIN/health"
fi

echo ""
echo "🎯 下一步:"
echo "   1. 访问 $DOMAIN/docs 查看API文档"
echo "   2. 使用 'railway logs' 监控日志"
echo "   3. 开发前端应用连接此API"
echo ""
echo -e "${GREEN}部署成功完成！${NC}"
