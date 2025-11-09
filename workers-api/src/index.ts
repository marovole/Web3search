/**
 * Web3search API - Cloudflare Workers Entry Point
 * Main application file
 */

import { Hono } from 'hono'
import type { Env } from './types/env'
import { loggerMiddleware } from './middlewares/logger'
import { corsMiddleware } from './middlewares/cors'
import healthRoutes from './routes/health'
import searchRoutes from './routes/search'
import chatRoutes from './routes/chat'
import reportRoutes from './routes/reports'

// Create main Hono app
const app = new Hono<{ Bindings: Env }>()

// ============================================
// Global Middlewares
// ============================================
app.use('*', loggerMiddleware)
app.use('*', corsMiddleware)

// ============================================
// Root Route
// ============================================
app.get('/', (c) => {
  return c.json({
    name: 'Web3search API',
    version: '1.0.0',
    description: 'Cryptocurrency research and analysis API powered by AI',
    documentation: '/api/v1/docs',
    endpoints: {
      health: '/api/v1/health',
      search: '/api/v1/search/autocomplete',
      chat: '/api/v1/chat/quick-chat',
      reports: '/api/v1/reports/generate',
    },
  })
})

// ============================================
// API Routes
// ============================================
app.route('/api/v1/health', healthRoutes)
app.route('/api/v1/search', searchRoutes)
app.route('/api/v1/chat', chatRoutes)
app.route('/api/v1/reports', reportRoutes)

// ============================================
// 404 Handler
// ============================================
app.notFound((c) => {
  return c.json(
    {
      error: {
        code: 'NOT_FOUND',
        message: 'Endpoint not found',
        path: c.req.path,
        status: 404,
      },
    },
    404
  )
})

// ============================================
// Scheduled Event Handler (Cron Jobs)
// ============================================
export async function scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
  console.log(`[Scheduled] Cron job triggered: ${event.cron}`)

  try {
    switch (event.cron) {
      case '*/5 * * * *': // Every 5 minutes - Health checks
        await runHealthChecks(env, ctx)
        break
      case '0 * * * *': // Every hour - KV cache cleanup
        await runKvCacheCleanup(env, ctx)
        break
      default:
        console.log(`[Scheduled] Unknown cron schedule: ${event.cron}`)
    }
  } catch (error) {
    console.error(`[Scheduled] Error executing cron job ${event.cron}:`, error)
  }
}

/**
 * Run health checks for all services
 */
async function runHealthChecks(env: Env, ctx: ExecutionContext) {
  const { createSupabaseClient } = await import('./lib/supabase')
  const { createOpenRouterClient } = await import('./lib/openrouter')

  const results = []

  // Check Supabase
  try {
    const supabase = createSupabaseClient(env)
    const { error } = await supabase.from('conversations').select('id').limit(1)

    results.push({
      check_name: 'supabase_database',
      status: error ? 'down' : 'healthy',
      latency_ms: Date.now(),
      details: { error: error?.message }
    })
  } catch (error) {
    results.push({
      check_name: 'supabase_database',
      status: 'down',
      latency_ms: Date.now(),
      error_message: error instanceof Error ? error.message : 'Unknown error',
      details: { type: 'connection_error' }
    })
  }

  // Check OpenRouter API
  try {
    const openrouter = createOpenRouterClient(env)
    // This is a lightweight ping - we don't actually make a full API call
    // Just verify we can create the client
    results.push({
      check_name: 'openrouter_api',
      status: 'healthy',
      latency_ms: Date.now(),
      details: { type: 'client_init_success' }
    })
  } catch (error) {
    results.push({
      check_name: 'openrouter_api',
      status: 'down',
      latency_ms: Date.now(),
      error_message: error instanceof Error ? error.message : 'Unknown error',
      details: { type: 'client_init_error' }
    })
  }

  // Check KV Cache
  try {
    const testKey = 'health-check-test'
    await env.CACHE.put(testKey, 'test', { expirationTtl: 60 })
    const value = await env.CACHE.get(testKey)
    await env.CACHE.delete(testKey)

    results.push({
      check_name: 'kv_cache',
      status: value === 'test' ? 'healthy' : 'degraded',
      latency_ms: Date.now(),
      details: { operation: 'read_write_test', success: value === 'test' }
    })
  } catch (error) {
    results.push({
      check_name: 'kv_cache',
      status: 'down',
      latency_ms: Date.now(),
      error_message: error instanceof Error ? error.message : 'Unknown error',
      details: { type: 'kv_error' }
    })
  }

  // Save results to Supabase if possible
  try {
    const supabase = createSupabaseClient(env)
    await supabase.from('healthcheck_events').insert(
      results.map(check => ({
        ...check,
        observed_at: new Date().toISOString()
      }))
    )
  } catch (error) {
    console.error('[Scheduled] Failed to save health check results:', error)
  }

  console.log(`[Scheduled] Health check completed: ${results.length} services checked`)
}

/**
 * Clean up expired KV cache entries
 */
async function runKvCacheCleanup(env: Env, ctx: ExecutionContext) {
  try {
    const prefix = 'deep-research:'
    const cutoffTime = Date.now() - (24 * 60 * 60 * 1000) // 24 hours ago
    let cleanedCount = 0

    // List and delete expired entries
    const list = await env.CACHE.list({ prefix })
    for (const key of list.keys) {
      if (key.expiration && key.expiration * 1000 < cutoffTime) {
        await env.CACHE.delete(key.name)
        cleanedCount++
      }
    }

    console.log(`[Scheduled] KV cache cleanup completed: ${cleanedCount} entries removed`)
  } catch (error) {
    console.error('[Scheduled] KV cache cleanup failed:', error)
  }
}

// ============================================
// Error Handler
// ============================================
app.onError((err, c) => {
  console.error('Unhandled error:', err)

  return c.json(
    {
      error: {
        code: 'INTERNAL_ERROR',
        message: 'An internal error occurred',
        trace_id: c.get('requestId') || 'unknown',
        status: 500,
      },
    },
    500
  )
})

// Export for Cloudflare Workers
export default app
