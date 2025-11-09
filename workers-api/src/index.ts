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
    },
  })
})

// ============================================
// API Routes
// ============================================
app.route('/api/v1/health', healthRoutes)
app.route('/api/v1/search', searchRoutes)

// Future routes (to be implemented in Week 2):
// app.route('/api/v1/chat', chatRoutes)
// app.route('/api/v1/reports', reportRoutes)

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
