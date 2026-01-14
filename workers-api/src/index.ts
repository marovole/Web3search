/**
 * Web3search API - Cloudflare Workers Entry Point
 * Main application file
 */

import { Hono } from 'hono'
import type { Env } from './types/env'
import { loggerMiddleware } from './middlewares/logger'
import { sentryMiddleware, getSentry, createToucanForScheduled } from './lib/sentry'
import { corsMiddleware } from './middlewares/cors'
import { createStandaloneLogger } from './lib/logger'
import {
  runHealthChecks,
  runSupabaseKeepAlive,
  runKvCacheCleanup,
  runDailyQuotaReset,
  runMonthlyQuotaReset,
  runAgentTasks,
} from './jobs'
import healthRoutes from './routes/health'
import searchRoutes from './routes/search'
import _chatRoutes from './routes/chat'
import chatV2Routes from './routes/chat-v2'
import deepResearchRoutes from './routes/deep-research'
import reportRoutes from './routes/reports'
import trendingRoutes from './routes/trending'
import githubRoutes from './routes/github'
import authRoutes from './routes/auth'
import usersRoutes from './routes/users'
import billingRoutes from './routes/billing'
import watchlistRoutes from './routes/watchlist'
import agentsRoutes from './routes/agents'
import multiAgentRoutes from './routes/multi-agent'
import notificationsRoutes from './routes/notifications'
import pushRoutes from './routes/push'
import holdingsRoutes from './routes/holdings'
import diagnosesRoutes from './routes/diagnoses'
import recommendationsRoutes from './routes/recommendations'
import conversationRoutes from './routes/conversation'
import activityRoutes from './routes/activity'

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
      multiAgent: '/api/v1/multi-agent/research (New Multi-Agent framework)',
      reports: '/api/v1/reports/generate',
      trending: '/api/v1/trending/hotspots',
      auth: '/api/v1/auth/me (Requires auth)',
      users: '/api/v1/users/profile (Requires auth)',
      notifications: '/api/v1/notifications (Requires auth)',
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
app.route('/api/v1/github', githubRoutes)
app.route('/api/v1/auth', authRoutes)
app.route('/api/v1/users', usersRoutes)
app.route('/api/v1/billing', billingRoutes)
app.route('/api/v1/watchlist', watchlistRoutes)
app.route('/api/v1/agents', agentsRoutes)
app.route('/api/v1/multi-agent', multiAgentRoutes)
app.route('/api/v1/notifications', notificationsRoutes)
app.route('/api/v1/push', pushRoutes)
app.route('/api/v1/holdings', holdingsRoutes)
app.route('/api/v1/diagnoses', diagnosesRoutes)
app.route('/api/v1/recommendations', recommendationsRoutes)
app.route('/api/v1/agents/conversation', conversationRoutes)
app.route('/api/v1/agents/activity', activityRoutes)

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
  const logger = createStandaloneLogger(env.ENVIRONMENT || 'development', 'scheduler')
  logger.info(`Cron job triggered: ${event.cron}`)

  const sentry = createToucanForScheduled(env, event)

  try {
    switch (event.cron) {
      case '*/5 * * * *':
        await runAgentTasks(env, 'price_alert')
        await runHealthChecks(env, ctx)
        break
      case '0 * * * *':
        await runAgentTasks(env, 'risk_monitor')
        await runAgentTasks(env, 'news_brief')
        await runKvCacheCleanup(env, ctx)
        break
      case '*/10 * * * *':
        await runSupabaseKeepAlive(env)
        break
      case '0 0 * * *':
        await runDailyQuotaReset(env)
        break
      case '0 0 1 * *':
        await runMonthlyQuotaReset(env)
        break
      case '0 9 * * 1':
        await runAgentTasks(env, 'portfolio_health')
        break
      case '0 10 * * 3':
        await runAgentTasks(env, 'opportunity_finder')
        break
      default:
        logger.warn(`Unknown cron schedule: ${event.cron}`)
    }
  } catch (error) {
    sentry?.captureException(error as Error)
    logger.error(`Error executing cron job ${event.cron}`, error instanceof Error ? error : undefined)
  }
}

// ============================================
// Error Handler
// ============================================
app.onError((err, c) => {
  const sentry = getSentry(c)
  sentry?.captureException(err)

  const logger = createStandaloneLogger(c.env.ENVIRONMENT || 'development', 'error-handler')
  logger.error('Unhandled error', err)

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

export default {
  fetch: app.fetch,
  scheduled,
}
