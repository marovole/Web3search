#!/bin/bash
# Web3search Keep-Alive Script
# 使用外部 Cron 服务（如 EasyCron、Cronitor、Healthchecks.io）定时执行此脚本
# 或添加到系统 crontab: */10 * * * * /path/to/keep-alive.sh

set -e

API_BASE_URL="${WEB3SEARCH_API_URL:-https://web3search-api.marovole.workers.dev}"
LOG_FILE="${KEEP_ALIVE_LOG:-./keep-alive.log}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 主函数
main() {
    log "🚀 Starting keep-alive ping..."
    
    local failed=0
    
    # 1. 轻量级 ping（最快，不调用数据库）
    log "📡 Pinging /health/ping..."
    if curl -s -o /dev/null -w "%{http_code}" "${API_BASE_URL}/api/v1/health/ping" | grep -q "200"; then
        log "✅ Ping successful"
    else
        log "❌ Ping failed"
        ((failed++))
    fi
    
    # 2. 完整健康检查（调用数据库）
    log "🏥 Pinging /health..."
    if curl -s "${API_BASE_URL}/api/v1/health" | grep -q '"status":"healthy"'; then
        log "✅ Health check passed"
    else
        log "⚠️ Health check returned non-healthy status"
        ((failed++))
    fi
    
    # 3. 激活 Supabase 连接（调用一个需要数据库的端点）
    log "🗄️ Activating Supabase connection..."
    # 使用短超时，避免长时间等待
    if timeout 10 curl -s -o /dev/null -w "%{http_code}" \
        "${API_BASE_URL}/api/v1/trending/hotspots?limit=1" | grep -qE "^[23]"; then
        log "✅ Supabase activated"
    else
        log "⚠️ Supabase activation timed out or failed (this may be normal during maintenance)"
    fi
    
    # 4. 检查 KV 缓存
    log "💾 Checking KV cache..."
    if curl -s "${API_BASE_URL}/api/v1/health" | grep -q '"cache":{"status":"available"}'; then
        log "✅ KV cache available"
    else
        log "⚠️ KV cache may be unavailable"
    fi
    
    # 总结
    log "📊 Keep-alive ping completed. Failures: $failed"
    
    if [ $failed -gt 0 ]; then
        log "⚠️ Some checks failed, but service may still be functional"
        exit 0  # 不返回错误，避免 cron 服务停止调度
    fi
    
    log "✅ All keep-alive checks passed!"
    exit 0
}

main "$@"
