/**
 * Health Check API Routes
 * GET /api/v1/health - Cached health check (60s TTL)
 * GET /api/v1/health/ready - Readiness probe (no cache)
 * GET /api/v1/health/live - Liveness probe (instant)
 * GET /api/v1/health/ping - Lightweight ping for external cron (no DB call)
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import { testDatabaseConnection } from '../lib/supabase'

// Health check response type
interface _HealthCheckPayload {
  status: string
  timestamp: string
  database: {
    status: string
    type: string
  }
  responseTime: string
  statusCode: number
}

// Health check cache configuration
const CACHE_KEY_PREFIX = 'health:check'
const CACHE_TTL_MS = 60 * 1000 // 60 seconds (aligned with documentation)
const CACHE_TTL_SECONDS = 60

const health = new Hono<{ Bindings: Env }>()

/**
 * Lightweight ping endpoint for external cron/monitoring
 * Returns minimal response without DB call - fastest possible response
 * Ideal for external uptime monitors and cron job keep-alive
 */
health.get('/ping', (c) => {
  return c.json({
    pong: true,
    timestamp: new Date().toISOString(),
    region: c.req.raw.cf?.colo || 'unknown',
    url: c.req.url,
  }, 200)
})

/**
 * Health check endpoint with KV caching
 * Returns service status, database connection status, and metadata
 * Caches successful health checks for 60 seconds to improve response time
 *
 * Performance targets:
 * - Cached response: < 50ms (P95)
 * - Fresh check: < 300ms (P95)
 */
health.get('/', async (c) => {
  const startTime = Date.now()
  const env = c.env
  const cache = env.CACHE

  // Build environment-specific cache key to avoid cross-environment data pollution
  const cacheKey = `${CACHE_KEY_PREFIX}:${env.ENVIRONMENT || 'unknown'}`

  /**
   * Cached health check result interface
   */
  interface CachedHealthResult {
    status: string
    timestamp: string
    database: { status: string; type: string }
    responseTime: string
    statusCode: number
  }

  /**
   * Attempt to retrieve cached health check result
   * Returns null if cache is unavailable, expired, or invalid
   */
  const tryGetCached = async (): Promise<CachedHealthResult | null> => {
    if (!cache) return null

    try {
      const cached = await cache.get(cacheKey, 'json') as CachedHealthResult | null
      if (!cached || typeof cached.timestamp !== 'string') return null

      // Validate timestamp and check expiration
      const cachedAt = new Date(cached.timestamp).getTime()
      if (Number.isNaN(cachedAt)) return null
      const cacheAgeMs = Date.now() - cachedAt
      if (cacheAgeMs > CACHE_TTL_MS) {
        console.debug('[Health] Cache expired', { cacheKey, ageMs: cacheAgeMs, ttlMs: CACHE_TTL_MS })
        return null
      }

      return cached
    } catch (error) {
      // Cache read failure - degrade gracefully
      console.warn('[Health] Cache read failed:', error)
      return null
    }
  }

  // Try to serve from cache first
  const cacheStartTime = Date.now()
  const cachedEntry = await tryGetCached()
  const cacheLatencyMs = Date.now() - cacheStartTime

  if (cachedEntry) {
    // Log cache hit metrics
    console.log('[CACHE HIT]', JSON.stringify({
      route: '/api/v1/health',
      cacheKey,
      latencyMs: cacheLatencyMs,
      age: Date.now() - new Date(cachedEntry.timestamp).getTime()
    }))

    return c.json(
      {
        status: cachedEntry.status,
        timestamp: cachedEntry.timestamp,
        version: '1.0.0',
        environment: env.ENVIRONMENT || 'unknown',
        database: cachedEntry.database,
        cache: {
          status: cache ? 'available' : 'unavailable',
          type: 'cloudflare-kv',
          hit: true,
          latencyMs: cacheLatencyMs
        },
        region: c.req.raw.cf?.colo || 'unknown',
        responseTime: cachedEntry.responseTime,
        cached: true, // Indicate this is a cached response
      },
      { status: cachedEntry.statusCode as 200 | 503 }
    )
  }

  // Log cache miss
  console.log('[CACHE MISS]', JSON.stringify({
    route: '/api/v1/health',
    cacheKey,
    latencyMs: cacheLatencyMs
  }))

  // Cache miss or expired - perform fresh health check
  try {
    const isDatabaseConnected = await testDatabaseConnection(env)

    const responseTime = `${Date.now() - startTime}ms`
    const status = isDatabaseConnected ? 'healthy' : 'degraded'
    const statusCode = isDatabaseConnected ? 200 : 503
    const timestamp = new Date().toISOString()
    const databaseStatus = {
      status: isDatabaseConnected ? 'connected' : 'disconnected',
      type: 'convex',
    }

    // Prepare cache payload (only cache successful checks)
    const cachePayload = {
      status,
      timestamp,
      database: databaseStatus,
      responseTime,
      statusCode,
    }

    // Asynchronously write to cache (don't block response)
    // executionCtx is only available in Cloudflare Workers runtime
    if (cache && isDatabaseConnected) {
      const cacheWritePromise = cache
        .put(cacheKey, JSON.stringify(cachePayload), {
          expirationTtl: CACHE_TTL_SECONDS,
        })
        .then(() => {
          console.debug('[Health] Cache write success', { cacheKey, ttl: CACHE_TTL_SECONDS })
        })
        .catch((err) => {
          // Cache write failure - log but don't fail the request
          console.warn('[Health] Cache write failed:', err)
        })

      // Try to defer cache write using executionCtx if available
      try {
        c.executionCtx.waitUntil(cacheWritePromise)
      } catch {
        // executionCtx not available (test environment)
        // The promise is still executing, just not deferred
        // This allows cache to work in tests
      }
    }

    return c.json(
      {
        status,
        timestamp,
        version: '1.0.0',
        environment: env.ENVIRONMENT || 'unknown',
        database: databaseStatus,
        cache: {
          status: cache ? 'available' : 'unavailable',
          type: 'cloudflare-kv',
          hit: false,
          latencyMs: cacheLatencyMs
        },
        region: c.req.raw.cf?.colo || 'unknown',
        responseTime,
        cached: false, // Fresh response, not from cache
      },
      { status: statusCode as 200 | 503 }
    )
  } catch (error) {
    const responseTime = `${Date.now() - startTime}ms`

    return c.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        environment: env.ENVIRONMENT || 'unknown',
        error: error instanceof Error ? error.message : 'Unknown error',
        responseTime,
      },
      503
    )
  }
})

/**
 * Readiness probe (for load balancers)
 */
health.get('/ready', async (c) => {
  const isDatabaseConnected = await testDatabaseConnection(c.env)

  if (isDatabaseConnected) {
    return c.json({ ready: true }, 200)
  } else {
    return c.json({ ready: false }, 503)
  }
})

/**
 * Liveness probe (for monitoring)
 */
health.get('/live', (c) => {
  return c.json({ alive: true }, 200)
})

export default health
