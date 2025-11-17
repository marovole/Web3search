/**
 * Logging Middleware
 * Log all incoming requests and responses with performance metrics
 */

import { Context, Next } from 'hono'
import type { Env } from '../types/env'

/**
 * Performance thresholds (milliseconds) - defaults
 */
const DEFAULT_SLOW_REQUEST_THRESHOLD = 1000 // 1 second
const DEFAULT_WARN_REQUEST_THRESHOLD = 2000 // 2 seconds

/**
 * Parse threshold from environment variable with fallback
 */
function parseThreshold(raw: string | undefined, fallback: number): number {
  const parsed = Number(raw)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

/**
 * Mask IP address to protect PII
 * IPv4: keeps first two octets (e.g., 203.0.xxx.xxx)
 * IPv6: keeps first four segments, always outputs 8 segments
 */
function maskIp(value: string): string {
  if (value === 'unknown') return value

  // IPv4
  if (value.includes('.')) {
    const segments = value.split('.')
    if (segments.length === 4) {
      segments[2] = '0'
      segments[3] = '0'
      return segments.join('.')
    }
  }

  // IPv6 (handles compressed format like 2001:db8::1)
  if (value.includes(':')) {
    const compact = value.split(':').filter(Boolean)
    const visible = compact.slice(0, 4)
    // Pad to 4 segments if needed
    while (visible.length < 4) visible.push('0')
    // Always output 8 segments total
    return [...visible, ...Array(4).fill('xxxx')].join(':')
  }

  return value
}

export async function loggerMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const startTime = Date.now()

  // Generate request ID
  const requestId = crypto.randomUUID()
  c.set('requestId', requestId)

  // Extract request information
  const method = c.req.method
  const path = c.req.path
  const rawIp = c.req.header('cf-connecting-ip') || c.req.header('x-real-ip') || 'unknown'
  const ip = maskIp(rawIp)
  const colo = c.req.raw.cf?.colo || 'unknown' // Cloudflare edge location

  // Execute request
  await next()

  // Calculate response time
  const responseTime = Date.now() - startTime
  const status = c.res.status

  // Parse thresholds from environment or use defaults
  const slowThreshold = parseThreshold(c.env.REQUEST_SLOW_THRESHOLD_MS, DEFAULT_SLOW_REQUEST_THRESHOLD)
  const warnThreshold = Math.max(
    parseThreshold(c.env.REQUEST_WARN_THRESHOLD_MS, DEFAULT_WARN_REQUEST_THRESHOLD),
    slowThreshold // Ensure warn threshold is never lower than slow threshold
  )

  // Performance metrics (JSON format for easy parsing)
  const metrics = {
    requestId,
    method,
    path,
    status,
    durationMs: responseTime,
    colo,
    ip,
    timestamp: new Date().toISOString(),
    slow: responseTime > slowThreshold
  }

  // Log with appropriate level based on performance
  if (responseTime > warnThreshold) {
    console.warn('[SLOW REQUEST]', JSON.stringify(metrics))
  } else if (responseTime > slowThreshold) {
    console.log('[PERFORMANCE]', JSON.stringify(metrics))
  } else {
    console.log('[REQUEST]', JSON.stringify(metrics))
  }

  // Add custom headers
  c.res.headers.set('x-request-id', requestId)
  c.res.headers.set('x-response-time', `${responseTime}ms`)
}
