#!/bin/bash
# 监控配置脚本 - 交互式配置 Sentry 和 Google Analytics

set -e

echo "================================================"
echo "  Web3Search 监控配置工具"
echo "================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 配置文件路径
FRONTEND_ENV="frontend/.env.production"
BACKEND_DIR="workers-api"

echo "📋 配置清单："
echo "  1. Sentry 后端项目 DSN"
echo "  2. Sentry 前端项目 DSN"
echo "  3. Google Analytics Measurement ID"
echo ""

# 函数：读取用户输入
read_input() {
    local prompt="$1"
    local var_name="$2"
    local current_value="$3"

    if [ -n "$current_value" ]; then
        echo -e "${YELLOW}当前值: ${current_value}${NC}"
    fi

    read -p "$prompt: " value

    if [ -z "$value" ] && [ -n "$current_value" ]; then
        value="$current_value"
    fi

    eval "$var_name='$value'"
}

# 步骤 1: 配置 Sentry 后端
echo "================================================"
echo "1️⃣  配置 Sentry 后端（Cloudflare Workers）"
echo "================================================"
echo ""
echo "请先在 Sentry Dashboard 创建项目："
echo "  - Platform: Cloudflare Workers (或 Node.js)"
echo "  - Project Name: web3search-api"
echo "  - 访问: https://sentry.io/"
echo ""

read_input "请输入 Sentry 后端 DSN" BACKEND_SENTRY_DSN ""

if [ -n "$BACKEND_SENTRY_DSN" ]; then
    echo ""
    echo -e "${GREEN}✓${NC} 后端 DSN: $BACKEND_SENTRY_DSN"
    echo ""
    echo "请选择配置方式："
    echo "  1) 使用 wrangler CLI 配置 (推荐)"
    echo "  2) 手动配置（我会告诉你步骤）"
    read -p "选择 [1-2]: " method

    if [ "$method" = "1" ]; then
        echo ""
        echo "正在使用 wrangler 配置 secrets..."
        cd "$BACKEND_DIR"

        echo "$BACKEND_SENTRY_DSN" | wrangler secret put SENTRY_DSN
        echo "production" | wrangler secret put ENVIRONMENT
        echo "0.1" | wrangler secret put SENTRY_TRACES_SAMPLE_RATE

        cd ..
        echo -e "${GREEN}✓${NC} 后端 Sentry 配置完成！"
    else
        echo ""
        echo -e "${YELLOW}请在 Cloudflare Dashboard 手动配置：${NC}"
        echo "  1. 访问: https://dash.cloudflare.com"
        echo "  2. Workers & Pages > web3search-api"
        echo "  3. Settings > Variables and Secrets"
        echo "  4. 添加以下 secrets:"
        echo "     - SENTRY_DSN = $BACKEND_SENTRY_DSN"
        echo "     - ENVIRONMENT = production"
        echo "     - SENTRY_TRACES_SAMPLE_RATE = 0.1"
        echo ""
        read -p "完成后按 Enter 继续..."
    fi
fi

# 步骤 2: 配置 Sentry 前端
echo ""
echo "================================================"
echo "2️⃣  配置 Sentry 前端（React）"
echo "================================================"
echo ""
echo "请在 Sentry Dashboard 创建前端项目："
echo "  - Platform: React"
echo "  - Project Name: web3search-frontend"
echo "  - 访问: https://sentry.io/"
echo ""

read_input "请输入 Sentry 前端 DSN" FRONTEND_SENTRY_DSN ""

# 步骤 3: 配置 Google Analytics
echo ""
echo "================================================"
echo "3️⃣  配置 Google Analytics 4"
echo "================================================"
echo ""
echo "请在 Google Analytics 创建 GA4 Property："
echo "  1. 访问: https://analytics.google.com"
echo "  2. Admin > Create Property"
echo "  3. Create Web Data Stream"
echo "  4. 复制 Measurement ID (格式: G-XXXXXXXXXX)"
echo ""

read_input "请输入 GA Measurement ID" GA_MEASUREMENT_ID ""

# 步骤 4: 更新前端配置文件
echo ""
echo "================================================"
echo "4️⃣  更新前端配置文件"
echo "================================================"
echo ""

if [ -f "$FRONTEND_ENV" ]; then
    echo "正在更新 $FRONTEND_ENV..."

    # 备份原文件
    cp "$FRONTEND_ENV" "$FRONTEND_ENV.backup"
    echo -e "${GREEN}✓${NC} 已备份原配置到 $FRONTEND_ENV.backup"

    # 更新 SENTRY_DSN
    if [ -n "$FRONTEND_SENTRY_DSN" ]; then
        sed -i.tmp "s|VITE_SENTRY_DSN=.*|VITE_SENTRY_DSN=$FRONTEND_SENTRY_DSN|g" "$FRONTEND_ENV"
        echo -e "${GREEN}✓${NC} 已更新 VITE_SENTRY_DSN"
    fi

    # 更新 GA_MEASUREMENT_ID
    if [ -n "$GA_MEASUREMENT_ID" ]; then
        sed -i.tmp "s|VITE_GA_MEASUREMENT_ID=.*|VITE_GA_MEASUREMENT_ID=$GA_MEASUREMENT_ID|g" "$FRONTEND_ENV"
        echo -e "${GREEN}✓${NC} 已更新 VITE_GA_MEASUREMENT_ID"
    fi

    # 清理临时文件
    rm -f "$FRONTEND_ENV.tmp"

    echo ""
    echo "当前配置："
    grep -E "VITE_(ENABLE_SENTRY|SENTRY_DSN|ENABLE_ANALYTICS|GA_MEASUREMENT_ID)" "$FRONTEND_ENV"
else
    echo -e "${RED}✗${NC} 配置文件不存在: $FRONTEND_ENV"
fi

# 步骤 5: 部署
echo ""
echo "================================================"
echo "5️⃣  部署"
echo "================================================"
echo ""
echo "配置完成！请执行以下步骤部署："
echo ""
echo "1. 构建前端："
echo "   cd frontend"
echo "   npm run build"
echo ""
echo "2. 提交配置（如果你想保存配置）："
echo "   git add frontend/.env.production"
echo "   git commit -m 'feat: configure Sentry and GA monitoring'"
echo "   git push origin main"
echo ""
echo "3. 验证部署："
echo "   - 前端: https://web3search.pages.dev"
echo "   - 后端: https://web3search-api.onrender.com/api/v1/health"
echo ""
echo "4. 检查监控："
echo "   - Sentry Backend: https://sentry.io/organizations/.../projects/web3search-api/"
echo "   - Sentry Frontend: https://sentry.io/organizations/.../projects/web3search-frontend/"
echo "   - Google Analytics: https://analytics.google.com"
echo ""
echo "详细验证步骤请查看: openspec/changes/fix-production-critical-issues/MONITORING-SETUP.md"
echo ""
echo -e "${GREEN}✓ 配置脚本执行完成！${NC}"
