/**
 * Web3search API - Cloudflare Workers Entry Point
 * Main application file
 */

import { Hono } from 'hono'
import type { Env } from './types/env'
import { loggerMiddleware } from './middlewares/logger'
import { sentryMiddleware, getSentry, createToucanForScheduled } from './lib/sentry'
import { corsMiddleware } from './middlewares/cors'
import healthRoutes from './routes/health'
import searchRoutes from './routes/search'
import chatRoutes from './routes/chat'
import chatV2Routes from './routes/chat-v2'
import deepResearchRoutes from './routes/deep-research'
import reportRoutes from './routes/reports'
import trendingRoutes from './routes/trending'

// Create main Hono app
const app = new Hono<{ Bindings: Env }>()

// ============================================
// Global Middlewares
// ============================================
app.use('*', loggerMiddleware)
app.use('*', sentryMiddleware) // Must be after logger (for requestId) and before cors
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
      chat: '/api/v1/chat/quick-chat (Uses v2 implementation with resilience)',
      chatV2: '/api/v2/chat/quick-chat (Same as v1, enhanced with model routing)',
      deepResearch: '/api/v1/deep-research (Async research tasks)',
      reports: '/api/v1/reports/generate',
      trending: '/api/v1/trending/hotspots',
    },
  })
})

// ============================================
// API Routes
// ============================================
app.route('/api/v1/health', healthRoutes)
app.route('/api/v1/search', searchRoutes)
// V1 chat now uses V2 implementation for better stability
app.route('/api/v1/chat', chatV2Routes)
app.route('/api/v2/chat', chatV2Routes)
app.route('/api/v1/deep-research', deepResearchRoutes)
app.route('/api/v1/reports', reportRoutes)
app.route('/api/v1/trending', trendingRoutes)

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

  // Create Sentry instance for scheduled tasks
  const sentry = createToucanForScheduled(env, event)

  try {
    switch (event.cron) {
      case '*/5 * * * *': // Every 5 minutes - Health checks
        await runHealthChecks(env, ctx)
        break
      case '0 * * * *': // Every hour - KV cache cleanup
        await runKvCacheCleanup(env, ctx)
        break
      case '*/10 * * * *': // Every 10 minutes - Supabase keep-alive
        await runSupabaseKeepAlive(env)
        break
      default:
        console.log(`[Scheduled] Unknown cron schedule: ${event.cron}`)
    }
  } catch (error) {
    // Capture cron job errors to Sentry
    sentry?.captureException(error as Error)
    console.error(`[Scheduled] Error executing cron job ${event.cron}:`, error)
  }
}

/**
 * Run health checks for all services
 */
async function runHealthChecks(env: Env, ctx: ExecutionContext) {
  const { getSupabaseClient } = await import('./lib/supabase')
  const { createOpenRouterClient } = await import('./lib/openrouter')

  const results = []

  // Check Supabase
  try {
    const supabase = getSupabaseClient(env)
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
  if (!env.CACHE) {
    results.push({
      check_name: 'kv_cache',
      status: 'down',
      latency_ms: 0,
      error_message: 'CACHE namespace not bound',
      details: { type: 'not_configured' }
    })
  } else {
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
  }

  // Save results to Supabase if possible
  try {
    const supabase = getSupabaseClient(env)
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
 * Keep Supabase warm to avoid automatic hibernation
 */
async function runSupabaseKeepAlive(env: Env) {
  const { getSupabaseClient } = await import('./lib/supabase')
  const startTime = Date.now()

  try {
    const supabase = getSupabaseClient(env)

    const { error } = await supabase
      .from('conversations')
      .select('id', { count: 'exact', head: true })
      .limit(1)

    const latency = Date.now() - startTime

    if (error && !['PGRST116', 'PGRST301', '42P01'].includes(error.code || '')) {
      console.warn('[KeepAlive] Supabase ping degraded', {
        code: error.code,
        message: error.message,
        latency_ms: latency,
      })
      return
    }

    console.log('[KeepAlive] Supabase warm-up completed', {
      latency_ms: latency,
      table: 'conversations',
      status: error ? 'ok-with-limited-table' : 'ok'
    })
  } catch (error) {
    console.error('[KeepAlive] Supabase warm-up failed', {
      message: error instanceof Error ? error.message : String(error),
    })
  }
}

/**
 * Clean up expired KV cache entries
 */
async function runKvCacheCleanup(env: Env, ctx: ExecutionContext) {
  if (!env.CACHE) {
    console.warn('[Scheduled] CACHE not bound, skipping KV cache cleanup')
    return
  }

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
  // Capture exception to Sentry
  const sentry = getSentry(c)
  sentry?.captureException(err)

  console.error('Unhandled error:', err)

  // Use Sentry event ID as trace_id if available, otherwise use requestId
  const eventId = sentry?.lastEventId()
  const traceId = eventId || c.get('requestId') || 'unknown'

  return c.json(
    {
      error: {
        code: 'INTERNAL_ERROR',
        message: 'An internal error occurred',
        trace_id: traceId,
        status: 500,
      },
    },
    500
  )
})

// Export for Cloudflare Workers (fetch + scheduled for cron triggers)
export default {
  fetch: app.fetch,
  scheduled,
}
