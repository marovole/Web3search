#!/bin/bash

# 生产环境部署验证脚本
# 验证环境变量配置、监控服务连接、安全头部部署和告警通知配置

set -e

echo "🔍 开始生产环境部署验证..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 错误计数
ERROR_COUNT=0
WARNING_COUNT=0

# 检查函数
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ERROR_COUNT=$((ERROR_COUNT + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNING_COUNT=$((WARNING_COUNT + 1))
}

# 1. 验证环境变量配置
echo "📋 1. 验证环境变量配置..."
echo ""

# 检查必需的环境变量
REQUIRED_VARS=(
    "VITE_APP_URL"
    "VITE_API_URL"
)

OPTIONAL_VARS=(
    "VITE_GA_MEASUREMENT_ID"
    "VITE_SENTRY_DSN"
    "VITE_ENABLE_SENTRY"
    "VITE_ENABLE_ANALYTICS"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        check_fail "必需环境变量未设置: $var"
    else
        check_pass "环境变量已设置: $var"
    fi
done

for var in "${OPTIONAL_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        check_warn "可选环境变量未设置: $var (可能影响功能)"
    else
        check_pass "环境变量已设置: $var"
    fi
done

echo ""

# 2. 验证监控服务连接
echo "📊 2. 验证监控服务连接..."
echo ""

# 检查 Google Analytics
if [ -n "$VITE_GA_MEASUREMENT_ID" ]; then
    if [[ "$VITE_GA_MEASUREMENT_ID" =~ ^G-[A-Z0-9]+$ ]]; then
        check_pass "Google Analytics Measurement ID 格式正确"
    else
        check_fail "Google Analytics Measurement ID 格式不正确: $VITE_GA_MEASUREMENT_ID"
    fi
else
    check_warn "Google Analytics 未配置（可选）"
fi

# 检查 Sentry
if [ -n "$VITE_SENTRY_DSN" ]; then
    if [[ "$VITE_SENTRY_DSN" =~ ^https://.*@.*\.ingest\.sentry\.io/.*$ ]]; then
        check_pass "Sentry DSN 格式正确"
        
        # 尝试连接 Sentry（可选）
        SENTRY_HOST=$(echo "$VITE_SENTRY_DSN" | sed -E 's|https://([^@]+)@([^/]+)/.*|\2|')
        if command -v curl &> /dev/null; then
            if curl -s --connect-timeout 5 "https://$SENTRY_HOST" > /dev/null 2>&1; then
                check_pass "Sentry 服务可访问"
            else
                check_warn "Sentry 服务连接超时（可能是网络问题）"
            fi
        fi
    else
        check_fail "Sentry DSN 格式不正确: $VITE_SENTRY_DSN"
    fi
else
    check_warn "Sentry 未配置（可选）"
fi

echo ""

# 3. 验证安全头部部署
echo "🛡️  3. 验证安全头部部署..."
echo ""

# 检查应用 URL
if [ -z "$VITE_APP_URL" ]; then
    check_fail "VITE_APP_URL 未设置，无法验证安全头部"
else
    APP_URL="$VITE_APP_URL"
    check_pass "应用 URL: $APP_URL"
    
    # 使用 curl 检查响应头（如果可用）
    if command -v curl &> /dev/null; then
        echo "检查响应头..."
        
        HEADERS=$(curl -sI "$APP_URL" 2>&1)
        
        # 检查关键安全头部
        SECURITY_HEADERS=(
            "Content-Security-Policy"
            "X-Frame-Options"
            "X-Content-Type-Options"
            "Strict-Transport-Security"
            "Referrer-Policy"
            "Permissions-Policy"
        )
        
        for header in "${SECURITY_HEADERS[@]}"; do
            if echo "$HEADERS" | grep -qi "^$header:"; then
                check_pass "安全头部已设置: $header"
            else
                check_warn "安全头部未设置: $header（可能由 CDN/托管平台设置）"
            fi
        done
        
        # 检查 HTTPS
        if [[ "$APP_URL" =~ ^https:// ]]; then
            check_pass "使用 HTTPS"
        else
            check_warn "未使用 HTTPS（开发环境可能使用 HTTP）"
        fi
    else
        check_warn "curl 不可用，跳过响应头检查"
    fi
fi

echo ""

# 4. 验证告警通知配置
echo "🚨 4. 验证告警通知配置..."
echo ""

# 检查 Sentry 告警配置
if [ -n "$VITE_SENTRY_DSN" ] && [ "$VITE_ENABLE_SENTRY" = "true" ]; then
    check_pass "Sentry 告警已启用"
    
    # 检查是否配置了 Sentry 项目（通过 DSN）
    SENTRY_PROJECT_ID=$(echo "$VITE_SENTRY_DSN" | sed -E 's|https://[^@]+@[^/]+/([0-9]+)|1|')
    if [ -n "$SENTRY_PROJECT_ID" ]; then
        check_pass "Sentry 项目 ID: $SENTRY_PROJECT_ID"
    fi
else
    check_warn "Sentry 告警未启用"
fi

# 检查环境变量中是否有告警配置
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    check_pass "Slack Webhook 已配置"
elif [ -n "$ALERT_EMAIL" ]; then
    check_pass "告警邮件已配置"
else
    check_warn "告警通知渠道未配置（可选）"
fi

echo ""

# 5. 验证构建配置
echo "🏗️  5. 验证构建配置..."
echo ""

# 检查是否在生产模式
if [ "$NODE_ENV" = "production" ] || [ "$VITE_ENVIRONMENT" = "production" ]; then
    check_pass "构建环境: production"
else
    check_warn "构建环境不是 production: ${NODE_ENV:-$VITE_ENVIRONMENT}"
fi

# 检查构建输出目录
if [ -d "dist" ]; then
    check_pass "构建输出目录存在: dist/"
    
    # 检查关键文件
    if [ -f "dist/index.html" ]; then
        check_pass "index.html 存在"
    else
        check_fail "index.html 不存在"
    fi
    
    if [ -d "dist/assets" ]; then
        check_pass "assets 目录存在"
    else
        check_warn "assets 目录不存在"
    fi
else
    check_warn "构建输出目录不存在，可能需要先运行构建"
fi

echo ""

# 6. 验证依赖安全性
echo "📦 6. 验证依赖安全性..."
echo ""

if command -v npm &> /dev/null; then
    # 检查是否有安全审计脚本
    if [ -f "package.json" ] && grep -q "security:audit" package.json; then
        check_pass "安全审计脚本已配置"
        
        # 可选：运行安全审计（可能需要时间）
        if [ "$1" = "--full-audit" ]; then
            echo "运行完整安全审计..."
            npm run security:audit 2>&1 | tail -20 || check_warn "安全审计发现问题"
        else
            check_warn "跳过完整安全审计（使用 --full-audit 运行）"
        fi
    else
        check_warn "未找到安全审计脚本"
    fi
else
    check_warn "npm 不可用，跳过依赖检查"
fi

echo ""

# 7. 总结
echo "📊 验证总结"
echo "=================================="
echo -e "${GREEN}通过: $((ERROR_COUNT + WARNING_COUNT - ERROR_COUNT))${NC}"
echo -e "${YELLOW}警告: $WARNING_COUNT${NC}"
echo -e "${RED}错误: $ERROR_COUNT${NC}"
echo ""

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ 生产环境验证通过！${NC}"
    exit 0
else
    echo -e "${RED}❌ 生产环境验证失败，发现 $ERROR_COUNT 个错误${NC}"
    exit 1
fi

