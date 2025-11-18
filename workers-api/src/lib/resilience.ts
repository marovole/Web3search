/**
 * Retry and Circuit Breaker Middleware
 * Implements exponential backoff and circuit breaker patterns for resilience
 *
 * @partof Week 2 T5: Retry/Circuit Breaker Middleware
 */

import type { Env } from '../types/env'
import type { OpenRouterPayload } from './openrouter'
import type { ModelConfig } from './model-routing'

/**
 * Retry configuration
 */
export interface RetryConfig {
  maxAttempts: number
  initialDelayMs: number
  maxDelayMs: number
  backoffFactor: number
  timeoutMs: number
  retryableStatuses: number[]
  retryableErrors: string[]
}

/**
 * Default retry configuration
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  initialDelayMs: 100,
  maxDelayMs: 10000,
  backoffFactor: 2,
  timeoutMs: 30000,
  retryableStatuses: [408, 429, 502, 503, 504],
  retryableErrors: ['ECONNRESET', 'ETIMEDOUT', 'ENOTFOUND', 'ECONNREFUSED']
}

/**
 * Circuit breaker states
 */
export const CIRCUIT_STATE = {
  CLOSED: 'closed',
  OPEN: 'open',
  HALF_OPEN: 'half_open'
} as const

export type CircuitState = typeof CIRCUIT_STATE[keyof typeof CIRCUIT_STATE]

/**
 * Circuit breaker configuration
 */
export interface CircuitBreakerConfig {
  failureThreshold: number
  successThreshold: number
  timeoutMs: number
  halfOpenTimeoutMs: number
}

/**
 * Default circuit breaker configuration
 */
export const DEFAULT_CIRCUIT_CONFIG: CircuitBreakerConfig = {
  failureThreshold: 5,
  successThreshold: 3,
  timeoutMs: 30000,
  halfOpenTimeoutMs: 5000
}

/**
 * Circuit breaker state storage
 * Uses Cloudflare KV for persistence across requests
 */
export class CircuitBreaker {
  private state: CircuitState = CIRCUIT_STATE.CLOSED
  private failures = 0
  private successes = 0
  private nextAttempt = Date.now()

  constructor(
    private name: string,
    private config: CircuitBreakerConfig,
    private env: Env
  ) {}

  /**
   * Check if circuit breaker is closed (allow requests)
   */
  async isClosed(): Promise<boolean> {
    // Load state from KV on first check
    await this.loadState()

    if (this.state === CIRCUIT_STATE.CLOSED) {
      return true
    }

    if (this.state === CIRCUIT_STATE.OPEN) {
      if (Date.now() >= this.nextAttempt) {
        // Transition to half-open state
        this.state = CIRCUIT_STATE.HALF_OPEN
        await this.saveState()
        return true
      }
      return false
    }

    // HALF_OPEN state
    return true
  }

  /**
   * Record a successful request
   */
  async recordSuccess(): Promise<void> {
    this.successes++
    this.failures = 0

    if (this.state === CIRCUIT_STATE.HALF_OPEN) {
      if (this.successes >= this.config.successThreshold) {
        // Transition to closed state
        this.state = CIRCUIT_STATE.CLOSED
        this.successes = 0
      }
    }

    await this.saveState()
  }

  /**
   * Record a failed request
   */
  async recordFailure(): Promise<void> {
    this.failures++
    this.successes = 0

    if (this.state === CIRCUIT_STATE.HALF_OPEN) {
      // Immediately open circuit after failure in half-open state
      this.state = CIRCUIT_STATE.OPEN
      this.nextAttempt = Date.now() + this.config.halfOpenTimeoutMs
    } else if (this.failures >= this.config.failureThreshold) {
      // Open circuit after too many failures
      this.state = CIRCUIT_STATE.OPEN
      this.nextAttempt = Date.now() + this.config.halfOpenTimeoutMs
    }

    await this.saveState()
  }

  /**
   * Get current state for monitoring
   */
  getState(): { state: CircuitState; failures: number; successes: number } {
    return {
      state: this.state,
      failures: this.failures,
      successes: this.successes
    }
  }

  /**
   * Save state to KV storage
   */
  private async saveState(): Promise<void> {
    if (!this.env.OPENROUTER_CIRCUIT_STATE) return

    const key = `circuit:${this.name}`
    const value = JSON.stringify({
      state: this.state,
      failures: this.failures,
      successes: this.successes,
      nextAttempt: this.nextAttempt,
      updatedAt: Date.now()
    })

    await this.env.OPENROUTER_CIRCUIT_STATE.put(key, value, {
      expirationTtl: 86400 // 24 hours
    })
  }

  /**
   * Load state from KV storage
   */
  private async loadState(): Promise<void> {
    if (!this.env.OPENROUTER_CIRCUIT_STATE) return

    const key = `circuit:${this.name}`
    const value = await this.env.OPENROUTER_CIRCUIT_STATE.get(key)

    if (value) {
      try {
        const data = JSON.parse(value)
        this.state = data.state || CIRCUIT_STATE.CLOSED
        this.failures = data.failures || 0
        this.successes = data.successes || 0
        this.nextAttempt = data.nextAttempt || Date.now()
      } catch (error) {
        console.error('Failed to load circuit breaker state:', error)
      }
    }
  }
}

/**
 * Retry with exponential backoff
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG,
  attempt = 1
): Promise<T> {
  const timeoutMs = config.timeoutMs ?? 30000
  let timeoutId: ReturnType<typeof setTimeout> | undefined
  const operationPromise = operation()
  const timeoutPromise = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => reject(new Error('Operation timeout')), timeoutMs)
  })

  const clearTimer = () => {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId)
      timeoutId = undefined
    }
  }

  try {
    const result = await Promise.race([operationPromise, timeoutPromise])
    return result
  } catch (error) {
    const isRetryable =
      error instanceof Error &&
      (config.retryableErrors.includes(error.name) ||
        config.retryableErrors.some(err => error.message.includes(err)))

    if (attempt < config.maxAttempts && isRetryable) {
      const delay = Math.min(
        config.initialDelayMs * Math.pow(config.backoffFactor, attempt - 1),
        config.maxDelayMs
      )

      console.log(`Retry attempt ${attempt}/${config.maxAttempts} after ${delay}ms`)
      await sleep(delay)
      return withRetry(operation, config, attempt + 1)
    }

    throw error
  } finally {
    clearTimer()
    // Suppress unhandled rejection from the "loser" promise in the race.
    // When timeout wins, the operation promise may still reject later.
    // This catch handler prevents Node from throwing an UnhandledPromiseRejectionWarning.
    // The actual error (if needed) was already caught and handled above.
    void operationPromise.catch(() => {})
  }
}

/**
 * Sleep helper
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Request result type
 */
export interface RequestResult<T> {
  success: boolean
  data?: T
  error?: Error
  attempts: number
  latencyMs: number
}

/**
 * Execute request with retry and circuit breaker
 */
export async function executeWithResilience<T>(
  operation: () => Promise<T>,
  options: {
    modelId: string
    modelConfig: ModelConfig
    env: Env
    retryConfig?: RetryConfig
    circuitConfig?: CircuitBreakerConfig
  }
): Promise<RequestResult<T>> {
  const {
    modelId,
    modelConfig,
    env,
    retryConfig = DEFAULT_RETRY_CONFIG,
    circuitConfig = DEFAULT_CIRCUIT_CONFIG
  } = options

  // Create circuit breaker for this model
  const circuitBreaker = new CircuitBreaker(modelId, circuitConfig, env)

  // Check if circuit is open
  const isCircuitClosed = await circuitBreaker.isClosed()
  if (!isCircuitClosed) {
    return {
      success: false,
      error: new Error(`Circuit breaker open for model: ${modelId}`),
      attempts: 0,
      latencyMs: 0
    }
  }

  const startTime = Date.now()
  let attempts = 0
  let lastError: Error | undefined

  try {
    const result = await withRetry(
      async () => {
        attempts++
        return await operation()
      },
      retryConfig,
      1
    )

    const latencyMs = Date.now() - startTime

    // Record success
    await circuitBreaker.recordSuccess()

    return {
      success: true,
      data: result,
      attempts,
      latencyMs
    }
  } catch (error) {
    const latencyMs = Date.now() - startTime
    lastError = error instanceof Error ? error : new Error(String(error))

    // Record failure
    await circuitBreaker.recordFailure()

    return {
      success: false,
      error: lastError,
      attempts,
      latencyMs
    }
  }
}

/**
 * Execute OpenRouter request with resilience
 */
export async function executeOpenRouterRequest(
  payload: OpenRouterPayload,
  openRouterClient: { request: (payload: OpenRouterPayload) => Promise<Response> },
  options: {
    modelId: string
    modelConfig: ModelConfig
    env: Env
    retryConfig?: RetryConfig
    circuitConfig?: CircuitBreakerConfig
  }
): Promise<RequestResult<Response>> {
  return executeWithResilience(
    () => openRouterClient.request(payload),
    options
  )
}

// Export for tests
export default {
  CircuitBreaker,
  withRetry,
  executeWithResilience,
  executeOpenRouterRequest,
  DEFAULT_RETRY_CONFIG,
  DEFAULT_CIRCUIT_CONFIG,
  CIRCUIT_STATE
}
