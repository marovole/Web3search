/**
 * Sentry Error Monitoring Integration
 * Using Toucan (Cloudflare Workers optimized SDK)
 */

import { Toucan } from 'toucan-js'
import type { Context, Next } from 'hono'
import type { Env } from '../types/env'

/**
 * Parse numeric configuration value with fallback
 */
const parseNumber = (value: string | undefined, fallback: number): number => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

/**
 * Create Toucan instance for a request
 * Automatically attaches request context, tags, and configuration
 *
 * @param c - Hono context
 * @returns Toucan instance or undefined if SENTRY_DSN is not configured
 */
export const createToucan = (c: Context<{ Bindings: Env }>): Toucan | undefined => {
  if (!c.env.SENTRY_DSN) {
    return undefined
  }

  // Parse trace sample rate (default: 10% in production, 0% in dev)
  const defaultSampleRate = c.env.ENVIRONMENT === 'production' ? 0.1 : 0
  const traceSampleRate = parseNumber(c.env.SENTRY_TRACES_SAMPLE_RATE, defaultSampleRate)

  return new Toucan({
    dsn: c.env.SENTRY_DSN,
    environment: c.env.ENVIRONMENT || 'unknown',
    request: c.req.raw,
    context: {
      tags: {
        requestId: c.get('requestId') ?? 'unknown',
        colo: c.req.raw.cf?.colo ?? 'unknown',
      },
    },
    // Automatically capture unhandled rejections and exceptions
    captureUnhandledRejections: true,
    captureUnhandledExceptions: true,
    // Performance monitoring (APM)
    tracesSampleRate: traceSampleRate,
  })
}

/**
 * Create Toucan instance for scheduled/cron tasks
 * Since there's no real Request, we create a dummy one
 *
 * @param env - Environment bindings
 * @param event - Scheduled event
 * @returns Toucan instance or undefined if SENTRY_DSN is not configured
 */
export const createToucanForScheduled = (
  env: Env,
  event: ScheduledEvent
): Toucan | undefined => {
  if (!env.SENTRY_DSN) {
    return undefined
  }

  // Create a dummy request for scheduled context
  const dummyRequest = new Request('https://web3search-api.onrender.com/scheduled')

  const defaultSampleRate = env.ENVIRONMENT === 'production' ? 0.1 : 0
  const traceSampleRate = parseNumber(env.SENTRY_TRACES_SAMPLE_RATE, defaultSampleRate)

  return new Toucan({
    dsn: env.SENTRY_DSN,
    environment: env.ENVIRONMENT || 'unknown',
    request: dummyRequest,
    context: {
      tags: {
        cron: event.cron,
        scheduledTime: new Date(event.scheduledTime).toISOString(),
      },
    },
    captureUnhandledRejections: true,
    captureUnhandledExceptions: true,
    tracesSampleRate: traceSampleRate,
  })
}

/**
 * Get Sentry instance from context
 * Helper function to retrieve Toucan from Hono context
 *
 * @param c - Hono context
 * @returns Toucan instance or undefined
 */
export const getSentry = (c: Context<{ Bindings: Env }>): Toucan | undefined => {
  return c.get('sentry') as Toucan | undefined
}

// Track initialization status
let initLogShown = false

/**
 * Sentry middleware
 * Creates Toucan instance for each request and attaches it to context
 * Should be placed after loggerMiddleware (to get requestId) and before other middlewares
 */
export const sentryMiddleware = async (c: Context<{ Bindings: Env }>, next: Next) => {
  const sentry = createToucan(c)

  // Show initialization status only once
  if (!initLogShown) {
    if (sentry) {
      console.log('[Sentry] Initialized successfully')
    } else {
      console.log('[Sentry] Disabled (SENTRY_DSN not configured)')
    }
    initLogShown = true
  }

  if (sentry) {
    c.set('sentry', sentry)

    // Attach user information if available (from auth middleware)
    const currentUser = c.get('currentUser')
    if (currentUser) {
      sentry.setUser(currentUser)
    }
  }

  await next()
}
