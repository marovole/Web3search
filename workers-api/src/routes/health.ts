/**
 * Health Check API Routes
 * GET /api/v1/health
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import { testDatabaseConnection } from '../lib/supabase'

const health = new Hono<{ Bindings: Env }>()

/**
 * Health check endpoint
 * Returns service status, database connection status, and metadata
 */
health.get('/', async (c) => {
  const startTime = Date.now()
  const env = c.env

  try {
    // Test database connection
    const isDatabaseConnected = await testDatabaseConnection(env)

    const responseTime = Date.now() - startTime
    const status = isDatabaseConnected ? 'healthy' : 'degraded'

    return c.json(
      {
        status,
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        environment: env.ENVIRONMENT || 'unknown',
        database: {
          status: isDatabaseConnected ? 'connected' : 'disconnected',
          type: 'supabase-postgresql',
        },
        cache: {
          status: env.CACHE ? 'available' : 'unavailable',
          type: 'cloudflare-kv',
        },
        region: c.req.raw.cf?.colo || 'unknown', // Cloudflare edge location
        responseTime: `${responseTime}ms`,
      },
      isDatabaseConnected ? 200 : 503
    )
  } catch (error) {
    const responseTime = Date.now() - startTime

    return c.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        environment: env.ENVIRONMENT || 'unknown',
        error: error instanceof Error ? error.message : 'Unknown error',
        responseTime: `${responseTime}ms`,
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
