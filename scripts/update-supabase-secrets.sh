#!/bin/bash
# 更新 Supabase 密钥脚本
# 用法: ./update-supabase-secrets.sh <SUPABASE_URL> <SUPABASE_ANON_KEY> [SERVICE_ROLE_KEY]

set -e

SUPABASE_URL="${1:-$SUPABASE_URL}"
SUPABASE_ANON_KEY="${2:-$SUPABASE_ANON_KEY}"
SUPABASE_SERVICE_ROLE_KEY="${3:-$SUPABASE_SERVICE_ROLE_KEY}"

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "用法: $0 <SUPABASE_URL> <SUPABASE_ANON_KEY> [SERVICE_ROLE_KEY]"
    echo ""
    echo "环境变量方式:"
    echo "  SUPABASE_URL=https://xxxx.supabase.co SUPABASE_ANON_KEY=eyJ... $0"
    exit 1
fi

echo "🚀 更新 Supabase 密钥..."
echo "  URL: $SUPABASE_URL"
echo ""

# 更新 Workers Secrets
echo "📦 更新 Cloudflare Workers secrets..."

cd "$(dirname "$0")/../workers-api"

npx wrangler secret put SUPABASE_URL <<< "$SUPABASE_URL" || echo "  ⚠️  SUPABASE_URL 更新失败，请手动运行: npx wrangler secret put SUPABASE_URL"
npx wrangler secret put SUPABASE_ANON_KEY <<< "$SUPABASE_ANON_KEY" || echo "  ⚠️  SUPABASE_ANON_KEY 更新失败，请手动运行: npx wrangler secret put SUPABASE_ANON_KEY"

if [ -n "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    npx wrangler secret put SUPABASE_SERVICE_ROLE_KEY <<< "$SUPABASE_SERVICE_ROLE_KEY" || echo "  ⚠️  SERVICE_ROLE_KEY 更新失败，请手动运行: npx wrangler secret put SUPABASE_SERVICE_ROLE_KEY"
fi

echo ""
echo "✅ 密钥更新完成！"
echo ""
echo "下一步:"
echo "  1. 重新部署: cd workers-api && npx wrangler deploy --env production"
echo "  2. 验证: curl https://web3search-api.marovole.workers.dev/api/v1/health"
