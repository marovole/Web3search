/**
 * Logging Middleware
 * Log all incoming requests and responses
 */

import { Context, Next } from 'hono'
import type { Env } from '../types/env'

export async function loggerMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const startTime = Date.now()

  // Generate request ID
  const requestId = crypto.randomUUID()
  c.set('requestId', requestId)

  // Extract request information
  const method = c.req.method
  const path = c.req.path
  const ip = c.req.header('cf-connecting-ip') || c.req.header('x-real-ip') || 'unknown'
  const userAgent = c.req.header('user-agent') || 'unknown'
  const colo = c.req.raw.cf?.colo || 'unknown' // Cloudflare edge location

  // Log request
  console.log(
    `[${requestId}] --> ${method} ${path} | IP: ${ip} | Colo: ${colo} | UA: ${userAgent.substring(
      0,
      50
    )}...`
  )

  // Execute request
  await next()

  // Calculate response time
  const responseTime = Date.now() - startTime
  const status = c.res.status

  // Log response
  console.log(`[${requestId}] <-- ${method} ${path} | Status: ${status} | Time: ${responseTime}ms`)

  // Add custom headers
  c.res.headers.set('x-request-id', requestId)
  c.res.headers.set('x-response-time', `${responseTime}ms`)
}
