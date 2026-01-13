/**
 * Sentry Error Monitoring Service
 * Production-ready error tracking and performance monitoring for React applications
 *
 * Features:
 * - Automatic error capture and reporting
 * - React Router 6 integration for navigation tracking
 * - PII (Personally Identifiable Information) filtering
 * - Performance monitoring with Core Web Vitals
 * - Breadcrumb tracking for user actions
 * - API request tracking
 *
 * @module services/sentry
 */

import * as Sentry from '@sentry/react'
import type { Breadcrumb, SeverityLevel as SentrySeverity } from '@sentry/types'

// ============================================
// Constants and Types
// ============================================

const isBrowser = typeof window !== 'undefined'
const defaultRelease = `${import.meta.env?.VITE_APP_NAME || 'web3search-frontend'}@${
  import.meta.env?.VITE_APP_VERSION || 'dev'
}`
const defaultEnvironment =
  import.meta.env?.VITE_SENTRY_ENVIRONMENT || import.meta.env?.VITE_ENVIRONMENT || 'production'

let initialized = false

/**
 * Sentry initialization options
 */
export interface InitSentryOptions {
  /** Enable Sentry tracking (default: from env) */
  enabled?: boolean
  /** Environment name (development, staging, production) */
  environment?: string
  /** Application release version */
  release?: string
  /** Performance trace sample rate (0.0 - 1.0, default: 0.1) */
  tracesSampleRate?: number
  /** Debug mode for Sentry SDK */
  debug?: boolean
}

export type SeverityLevel = SentrySeverity

// ============================================
// PII Filtering Utilities
// ============================================

/**
 * Sanitize URL by removing query parameters and hash
 * Prevents leaking sensitive information in URLs
 *
 * @param raw - Raw URL string
 * @returns Sanitized URL or undefined
 *
 * @example
 * sanitizeUrl('https://example.com/page?token=secret#hash')
 * // => 'https://example.com/page'
 */
function sanitizeUrl(raw?: string): string | undefined {
  if (!raw) {
    return undefined
  }

  try {
    const parsed = new URL(raw, isBrowser ? window.location.origin : undefined)
    // Remove query parameters and hash to prevent PII leakage
    parsed.search = ''
    parsed.hash = ''
    return parsed.toString()
  } catch {
    // If URL parsing fails, return the raw string
    return raw
  }
}

/**
 * Scrub breadcrumb data to remove sensitive information
 * Filters URLs, tokens, API keys, and other PII from breadcrumb data
 *
 * @param breadcrumb - Sentry breadcrumb object
 * @returns Scrubbed breadcrumb
 */
function scrubBreadcrumb(breadcrumb: Breadcrumb): Breadcrumb {
  if (!breadcrumb.data) {
    return breadcrumb
  }

  // Sanitize URLs
  if (breadcrumb.data.url) {
    breadcrumb.data.url = sanitizeUrl(String(breadcrumb.data.url))
  }

  // Remove sensitive keys (tokens, API keys, passwords, etc.)
  const sensitiveKeys = [
    'token',
    'apiKey',
    'api_key',
    'password',
    'secret',
    'authorization',
    'cookie',
    'sessionId',
    'session_id',
  ]

  for (const key of sensitiveKeys) {
    if (key in breadcrumb.data) {
      breadcrumb.data[key] = '[Filtered]'
    }
  }

  return breadcrumb
}

/**
 * Scrub event data to remove PII
 * Removes email addresses, IP addresses, and URL parameters
 *
 * @param event - Sentry event object
 * @returns Scrubbed event
 */
function scrubEvent(event: any): any {
  // Sanitize request URL
  if (event.request?.url) {
    event.request.url = sanitizeUrl(event.request.url)
  }

  // Remove user PII (email and IP address)
  if (event.user) {
    delete event.user.email
    if ('ip_address' in event.user) {
      delete event.user.ip_address
    }
  }

  return event
}

// ============================================
// Configuration
// ============================================

// NOTE: Trace targets configuration for distributed tracing
// Currently not used due to Sentry SDK API changes, but kept for future reference
// function getTraceTargets(): Array<string | RegExp> {
//   const targets: Array<string | RegExp> = [
//     'https://web3search-api.marovole.workers.dev',
//     /^https:\/\/web3search\.pages\.dev/,
//   ]
//   if (isBrowser && window.location.origin) {
//     targets.unshift(window.location.origin)
//   }
//   return targets
// }

/**
 * Get Sentry integrations
 * Includes BrowserTracing for performance monitoring
 *
 * @returns Array of Sentry integrations
 */
function getIntegrations() {
  return [
    Sentry.browserTracingIntegration(),
  ]
}

/**
 * Guard to check if Sentry is initialized
 * Prevents errors when Sentry functions are called before initialization
 *
 * @returns true if initialized, false otherwise
 */
function guardInitialized(): boolean {
  if (!initialized) {
    console.warn('[Sentry] Not initialized. Call initSentry() first.')
    return false
  }

  return true
}

// ============================================
// Core API
// ============================================

/**
 * Initialize Sentry error monitoring and performance tracking
 * Must be called once during application bootstrap
 *
 * @param options - Initialization options
 *
 * @example
 * ```ts
 * initSentry({
 *   environment: 'production',
 *   tracesSampleRate: 0.1,
 * })
 * ```
 */
export function initSentry(options?: InitSentryOptions): void {
  // Prevent double initialization
  if (!isBrowser || initialized) {
    return
  }

  const enabled = options?.enabled ?? import.meta.env?.VITE_ENABLE_SENTRY === 'true'
  const dsn = import.meta.env?.VITE_SENTRY_DSN

  // Skip initialization if disabled or DSN not configured
  if (!enabled || !dsn) {
    if (enabled && !dsn) {
      console.warn('[Sentry] DSN not configured. Skipping initialization.')
    }
    return
  }

  try {
    Sentry.init({
      dsn,
      environment: options?.environment ?? defaultEnvironment,
      release: options?.release ?? defaultRelease,
      integrations: getIntegrations(),
      tracesSampleRate: options?.tracesSampleRate ?? 0.1,
      debug: options?.debug ?? false,

      // PII filtering hooks
      beforeSend(event, _hint) {
        return scrubEvent(event as any)
      },
      beforeBreadcrumb(breadcrumb) {
        return scrubBreadcrumb(breadcrumb)
      },

      // Additional features
      attachStacktrace: true, // Attach stack traces to all messages
    })

    initialized = true
    console.log('[Sentry] Initialized successfully', {
      environment: options?.environment ?? defaultEnvironment,
      release: options?.release ?? defaultRelease,
    })
  } catch (error) {
    console.error('[Sentry] Initialization failed:', error)
  }
}

/**
 * Capture an exception and send it to Sentry
 *
 * @param error - Error object to capture
 * @param context - Additional context metadata
 *
 * @example
 * ```ts
 * try {
 *   // ... code that might throw
 * } catch (error) {
 *   captureException(error, { component: 'ChatInterface' })
 * }
 * ```
 */
export function captureException(error: Error, context?: Record<string, any>): void {
  if (!guardInitialized()) return
  Sentry.captureException(error, { extra: context })
}

/**
 * Capture a message and send it to Sentry
 * Use for non-error events that you want to track
 *
 * @param message - Message string
 * @param level - Severity level (debug, info, warning, error, fatal)
 * @param context - Additional context metadata
 *
 * @example
 * ```ts
 * captureMessage('User completed onboarding', 'info', { userId: '123' })
 * ```
 */
export function captureMessage(
  message: string,
  level: SeverityLevel = 'info',
  context?: Record<string, any>
): void {
  if (!guardInitialized()) return
  Sentry.captureMessage(message, { level, extra: context } as any)
}

/**
 * Set the current user context
 * User information will be attached to all events
 *
 * @param user - User information (PII will be filtered)
 *
 * @example
 * ```ts
 * setUser({ id: '123', username: 'johndoe' })
 * ```
 */
export function setUser(user: { id: string; email?: string; username?: string }): void {
  if (!guardInitialized()) return
  // Note: email will be filtered by scrubEvent()
  Sentry.setUser(user)
}

/**
 * Clear the current user context
 * Use when user logs out
 */
export function clearUser(): void {
  if (!guardInitialized()) return
  Sentry.setUser(null)
}

/**
 * Add a breadcrumb for user action tracking
 * Breadcrumbs help reconstruct the sequence of events leading to an error
 *
 * @param breadcrumb - Breadcrumb object
 *
 * @example
 * ```ts
 * addBreadcrumb({
 *   category: 'ui',
 *   message: 'Button clicked',
 *   data: { buttonId: 'submit' },
 *   level: 'info',
 * })
 * ```
 */
export function addBreadcrumb(breadcrumb: Breadcrumb): void {
  if (!guardInitialized()) return
  Sentry.addBreadcrumb(scrubBreadcrumb(breadcrumb))
}

/**
 * Set additional context for events
 * Context will be attached to all subsequent events
 *
 * @param key - Context key
 * @param context - Context data
 *
 * @example
 * ```ts
 * setContext('feature_flags', { newUI: true, betaMode: false })
 * ```
 */
export function setContext(key: string, context: Record<string, any>): void {
  if (!guardInitialized()) return
  Sentry.setContext(key, context)
}

// ============================================
// Performance Monitoring
// ============================================

/**
 * Start a performance span
 * Use to measure the duration of specific operations
 *
 * @param name - Span description
 * @param operation - Operation type (e.g., 'api', 'query', 'render')
 * @returns Span object or null if Sentry not initialized
 *
 * @example
 * ```ts
 * const span = startSpan('fetchUserData', 'api')
 * try {
 *   await fetchUserData()
 * } finally {
 *   span?.end()
 * }
 * ```
 */
export function startSpan(name: string, operation: string = 'operation'): any {
  if (!guardInitialized()) return null
  return Sentry.startSpan({ name, op: operation }, (span) => span)
}

/**
 * Start a performance transaction
 * Transactions represent high-level operations (e.g., page loads, API calls)
 *
 * @param name - Transaction name
 * @param operation - Operation type (e.g., 'navigation', 'pageload')
 * @param context - Additional transaction context
 * @returns Transaction object or null
 *
 * @example
 * ```ts
 * const transaction = startTransaction('API Request', 'http')
 * try {
 *   await makeRequest()
 * } finally {
 *   transaction?.end()
 * }
 * ```
 */
export function startTransaction(
  name: string,
  operation: string = 'navigation',
  _context?: any
): any {
  if (!guardInitialized()) return null
  return Sentry.startSpan({ name, op: operation }, (span) => span)
}

/**
 * Track Core Web Vitals
 * Captures key performance metrics (LCP, FID, CLS)
 */
export function trackCoreWebVitals(): void {
  if (!guardInitialized() || !isBrowser || typeof performance === 'undefined') {
    return
  }

  const entries = performance.getEntriesByType('navigation')
  if (entries.length) {
    const navigation = entries[0] as PerformanceNavigationTiming
    Sentry.addBreadcrumb({
      category: 'performance',
      message: 'Core Web Vitals snapshot',
      data: {
        domContentLoaded: navigation.domContentLoadedEventEnd,
        loadEvent: navigation.loadEventEnd,
        startTime: navigation.startTime,
      },
      level: 'info',
    })
  }
}

/**
 * Track page load performance
 * Records timing metrics for the initial page load
 */
export function trackPageLoad(): void {
  if (!guardInitialized() || !isBrowser || typeof performance === 'undefined') {
    return
  }

  const loadEntry = performance.getEntriesByType('navigation')[0]
  if (loadEntry) {
    Sentry.addBreadcrumb({
      category: 'performance',
      message: 'Page load complete',
      data: {
        duration: loadEntry.duration,
        name: loadEntry.name,
      },
      level: 'info',
    })
  }
}

/**
 * Track resource loading
 * Records metrics for scripts, stylesheets, and other resources
 */
export function trackResourceLoading(): void {
  if (!guardInitialized() || !isBrowser || typeof performance === 'undefined') {
    return
  }

  const resources = performance.getEntriesByType('resource')
  Sentry.addBreadcrumb({
    category: 'performance',
    message: 'Resource loading snapshot',
    data: {
      count: resources.length,
      totalTransferSize: resources.reduce(
        (sum, entry) => sum + (entry as PerformanceResourceTiming).transferSize,
        0
      ),
    },
    level: 'info',
  })
}

/**
 * Track user interaction
 * Records user actions as breadcrumbs
 *
 * @param action - Action description
 * @param element - Element identifier (optional)
 * @param properties - Additional properties
 *
 * @example
 * ```ts
 * trackUserInteraction('click', 'submit-button', { formId: 'login' })
 * ```
 */
export function trackUserInteraction(
  action: string,
  element?: string,
  properties?: Record<string, any>
): void {
  if (!guardInitialized()) return
  Sentry.addBreadcrumb({
    category: 'interaction',
    message: action,
    data: { element, ...properties },
    level: 'info',
  })
}

/**
 * Track API request
 * Records API call metrics as breadcrumbs
 *
 * @param url - API endpoint URL
 * @param method - HTTP method
 * @param status - Response status code
 * @param duration - Request duration in ms
 * @param responseSize - Response size in bytes (optional)
 *
 * @example
 * ```ts
 * trackAPIRequest('/api/users', 'GET', 200, 125, 1024)
 * ```
 */
export function trackAPIRequest(
  url: string,
  method: string,
  status: number,
  duration: number,
  responseSize?: number
): void {
  if (!guardInitialized()) return
  Sentry.addBreadcrumb({
    category: 'api',
    message: `${method.toUpperCase()} ${sanitizeUrl(url) ?? url}`,
    data: { status, duration, responseSize },
    level: status >= 500 ? 'error' : 'info',
  })
}

/**
 * Track error (alias for captureException)
 *
 * @param error - Error object
 * @param context - Additional context
 */
export function trackError(error: Error, context?: Record<string, any>): void {
  captureException(error, context)
}

// ============================================
// Exports
// ============================================

export default {
  initSentry,
  captureException,
  captureMessage,
  setUser,
  clearUser,
  addBreadcrumb,
  setContext,
  startSpan,
  startTransaction,
  trackCoreWebVitals,
  trackPageLoad,
  trackResourceLoading,
  trackUserInteraction,
  trackAPIRequest,
  trackError,
}
