/**
 * Unified Logger for Workers API
 * Replaces raw console.log/warn/error with structured, environment-aware logging
 *
 * Features:
 * - Environment-based log levels (production filters debug/info)
 * - Structured JSON output for easy parsing
 * - Sentry integration for errors
 * - Request context preservation
 *
 * @partof Clean Code Refactor - P0
 */

import type { Context } from 'hono'
import type { Env } from '../types/env'
import type { Toucan } from 'toucan-js'

/**
 * Log levels in order of severity
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

/**
 * Log entry structure
 */
export interface LogEntry {
  level: LogLevel
  message: string
  timestamp: string
  context?: string
  requestId?: string
  data?: Record<string, unknown>
  error?: {
    name: string
    message: string
    stack?: string
  }
}

/**
 * Logger configuration
 */
interface LoggerConfig {
  environment: string
  minLevel: LogLevel
  enableConsole: boolean
  sentry?: Toucan
  requestId?: string
  context?: string
}

/**
 * Log level priorities (higher = more severe)
 */
const LOG_LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
}

/**
 * Get minimum log level based on environment
 */
function getMinLogLevel(environment: string): LogLevel {
  switch (environment) {
    case 'production':
      return 'info' // Filter out debug in production
    case 'staging':
      return 'debug'
    default:
      return 'debug' // Development - show all
  }
}

/**
 * Format log entry as JSON string
 */
function formatLogEntry(entry: LogEntry): string {
  return JSON.stringify(entry)
}

/**
 * Create a logger instance
 */
function createLoggerInstance(config: LoggerConfig) {
  const shouldLog = (level: LogLevel): boolean => {
    return LOG_LEVEL_PRIORITY[level] >= LOG_LEVEL_PRIORITY[config.minLevel]
  }

  const createEntry = (
    level: LogLevel,
    message: string,
    data?: Record<string, unknown>,
    error?: Error
  ): LogEntry => {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
    }

    if (config.context) {
      entry.context = config.context
    }

    if (config.requestId) {
      entry.requestId = config.requestId
    }

    if (data && Object.keys(data).length > 0) {
      entry.data = data
    }

    if (error) {
      entry.error = {
        name: error.name,
        message: error.message,
        stack: config.environment !== 'production' ? error.stack : undefined,
      }
    }

    return entry
  }

  const log = (
    level: LogLevel,
    message: string,
    data?: Record<string, unknown>,
    error?: Error
  ): void => {
    if (!shouldLog(level)) return

    const entry = createEntry(level, message, data, error)
    const formatted = formatLogEntry(entry)

    if (config.enableConsole) {
      switch (level) {
        case 'debug':
          console.debug(`[DEBUG]`, formatted)
          break
        case 'info':
          console.log(`[INFO]`, formatted)
          break
        case 'warn':
          console.warn(`[WARN]`, formatted)
          break
        case 'error':
          console.error(`[ERROR]`, formatted)
          break
      }
    }

    // Send errors to Sentry
    if (level === 'error' && config.sentry && error) {
      config.sentry.setTag('context', config.context || 'unknown')
      config.sentry.setTag('requestId', config.requestId || 'unknown')
      if (data) {
        config.sentry.setExtra('data', data)
      }
      config.sentry.captureException(error)
    }
  }

  return {
    debug: (message: string, data?: Record<string, unknown>) => log('debug', message, data),
    info: (message: string, data?: Record<string, unknown>) => log('info', message, data),
    warn: (message: string, data?: Record<string, unknown>) => log('warn', message, data),
    error: (message: string, error?: Error, data?: Record<string, unknown>) =>
      log('error', message, data, error),

    /**
     * Create a child logger with additional context
     */
    child: (childContext: string) =>
      createLoggerInstance({
        ...config,
        context: config.context ? `${config.context}:${childContext}` : childContext,
      }),

    /**
     * Set request ID for correlation
     */
    withRequestId: (requestId: string) =>
      createLoggerInstance({
        ...config,
        requestId,
      }),

    /**
     * Attach Sentry instance
     */
    withSentry: (sentry: Toucan) =>
      createLoggerInstance({
        ...config,
        sentry,
      }),
  }
}

/**
 * Logger type definition
 */
export type Logger = ReturnType<typeof createLoggerInstance>

/**
 * Create logger from Hono context
 * Automatically extracts environment, requestId, and Sentry instance
 */
export function createLogger(c: Context<{ Bindings: Env }>): Logger {
  const environment = c.env.ENVIRONMENT || 'development'
  const requestId = c.get('requestId') as string | undefined
  const sentry = c.get('sentry') as Toucan | undefined

  return createLoggerInstance({
    environment,
    minLevel: getMinLogLevel(environment),
    enableConsole: true,
    sentry,
    requestId,
  })
}

/**
 * Create standalone logger (for scheduled tasks, etc.)
 */
export function createStandaloneLogger(
  environment: string = 'development',
  context?: string,
  sentry?: Toucan
): Logger {
  return createLoggerInstance({
    environment,
    minLevel: getMinLogLevel(environment),
    enableConsole: true,
    sentry,
    context,
  })
}

/**
 * Default logger for quick usage (development mode)
 * Prefer createLogger(c) in route handlers for full context
 */
export const logger = createLoggerInstance({
  environment: 'development',
  minLevel: 'debug',
  enableConsole: true,
})

export default logger
