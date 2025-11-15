/**
 * Tests for Resilience Library (Retry + Circuit Breaker)
 * Validates retry logic, circuit breaker state transitions, and fault tolerance
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  CircuitBreaker,
  withRetry,
  executeWithResilience,
  executeOpenRouterRequest,
  DEFAULT_RETRY_CONFIG,
  DEFAULT_CIRCUIT_CONFIG,
  CIRCUIT_STATE,
  type RetryConfig,
  type CircuitBreakerConfig,
} from '../../src/lib/resilience'
import type { Env } from '../../src/types/env'
import type { ModelConfig } from '../../src/lib/model-routing'

// ============================================
// Test Fixtures
// ============================================

const BASE_MODEL_CONFIG: ModelConfig = {
  model: 'test-model',
  provider: 'anthropic',
  weight: 1,
  costPer1M: {
    prompt: 1.0,
    completion: 1.0,
  },
  maxTokens: 4096,
  capabilities: {
    reasoning: true,
    code: true,
    longContext: true,
    streaming: true,
  },
}

// ============================================
// KV Mock for Circuit Breaker State
// ============================================

type KVStoreEntry = {
  value: string
  expiration?: number
}

function createCircuitStateNamespace(initial: Record<string, string> = {}) {
  const store = new Map<string, KVStoreEntry>()

  // Initialize with provided state
  Object.entries(initial).forEach(([key, value]) => {
    store.set(key, { value })
  })

  const kv: KVNamespace = {
    get: async (key: string) => {
      const entry = store.get(key)
      if (!entry) return null

      // Check expiration
      if (entry.expiration && entry.expiration <= Math.floor(Date.now() / 1000)) {
        store.delete(key)
        return null
      }

      return entry.value
    },

    put: async (key: string, value: string, opts?: { expirationTtl?: number }) => {
      const entry: KVStoreEntry = { value }
      if (opts?.expirationTtl) {
        entry.expiration = Math.floor(Date.now() / 1000) + opts.expirationTtl
      }
      store.set(key, entry)
    },

    delete: async (key: string) => {
      store.delete(key)
    },

    list: async () => ({
      keys: Array.from(store.entries()).map(([name, entry]) => ({
        name,
        expiration: entry.expiration ?? null,
        metadata: null,
      })),
      list_complete: true,
    }),
  } as KVNamespace

  return { kv, store }
}

function createMockEnv(overrides: Partial<Env> = {}): Env {
  const { kv } = createCircuitStateNamespace()

  return {
    ENVIRONMENT: 'production',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'anon-key',
    OPENROUTER_API_KEY: 'test-key',
    CACHE: {} as KVNamespace,
    OPENROUTER_CIRCUIT_STATE: kv,
    ...overrides,
  }
}

// ============================================
// Circuit Breaker Tests
// ============================================

describe('CircuitBreaker', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(0)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  describe('State Transitions', () => {
    it('starts in CLOSED state', async () => {
      const env = createMockEnv()
      const breaker = new CircuitBreaker('test-model', DEFAULT_CIRCUIT_CONFIG, env)

      expect(await breaker.isClosed()).toBe(true)
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.CLOSED)
    })

    it('opens after reaching failure threshold', async () => {
      const env = createMockEnv()
      const config: CircuitBreakerConfig = {
        ...DEFAULT_CIRCUIT_CONFIG,
        failureThreshold: 3,
      }
      const breaker = new CircuitBreaker('test-model', config, env)

      // Record failures up to threshold
      await breaker.recordFailure()
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.CLOSED)

      await breaker.recordFailure()
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.CLOSED)

      await breaker.recordFailure()
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.OPEN)

      // Circuit should reject requests
      expect(await breaker.isClosed()).toBe(false)
    })

    it('transitions from OPEN to HALF_OPEN after timeout', async () => {
      const env = createMockEnv()
      const config: CircuitBreakerConfig = {
        ...DEFAULT_CIRCUIT_CONFIG,
        failureThreshold: 1,
        halfOpenTimeoutMs: 5000,
      }
      const breaker = new CircuitBreaker('test-model', config, env)

      // Open the circuit
      await breaker.recordFailure()
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.OPEN)
      expect(await breaker.isClosed()).toBe(false)

      // Advance time past the timeout
      vi.setSystemTime(6000)

      // Should transition to HALF_OPEN
      expect(await breaker.isClosed()).toBe(true)
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.HALF_OPEN)
    })

    it('closes from HALF_OPEN after success threshold', async () => {
      const env = createMockEnv()
      const config: CircuitBreakerConfig = {
        ...DEFAULT_CIRCUIT_CONFIG,
        failureThreshold: 1,
        successThreshold: 2,
        halfOpenTimeoutMs: 1000,
      }
      const breaker = new CircuitBreaker('test-model', config, env)

      // Open and transition to HALF_OPEN
      await breaker.recordFailure()
      vi.setSystemTime(2000)
      await breaker.isClosed() // Triggers transition to HALF_OPEN

      expect(breaker.getState().state).toBe(CIRCUIT_STATE.HALF_OPEN)

      // Record successes
      await breaker.recordSuccess()
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.HALF_OPEN)

      await breaker.recordSuccess()
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.CLOSED)
    })

    it('reopens from HALF_OPEN on failure', async () => {
      const env = createMockEnv()
      const config: CircuitBreakerConfig = {
        ...DEFAULT_CIRCUIT_CONFIG,
        failureThreshold: 1,
        halfOpenTimeoutMs: 1000,
      }
      const breaker = new CircuitBreaker('test-model', config, env)

      // Open and transition to HALF_OPEN
      await breaker.recordFailure()
      vi.setSystemTime(2000)
      await breaker.isClosed()

      expect(breaker.getState().state).toBe(CIRCUIT_STATE.HALF_OPEN)

      // Failure in HALF_OPEN should immediately reopen
      await breaker.recordFailure()
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.OPEN)
    })
  })

  describe('State Persistence', () => {
    it('persists state to KV on failure', async () => {
      const { kv, store } = createCircuitStateNamespace()
      const env = createMockEnv({ OPENROUTER_CIRCUIT_STATE: kv })
      const breaker = new CircuitBreaker(
        'persist-test',
        { ...DEFAULT_CIRCUIT_CONFIG, failureThreshold: 2 },
        env
      )

      await breaker.recordFailure()
      await breaker.recordFailure()

      const key = 'circuit:persist-test'
      expect(store.has(key)).toBe(true)

      const saved = JSON.parse(store.get(key)!.value)
      expect(saved.state).toBe(CIRCUIT_STATE.OPEN)
      expect(saved.failures).toBe(2)
    })

    it('loads state from KV on isClosed check', async () => {
      const initialState = {
        'circuit:load-test': JSON.stringify({
          state: CIRCUIT_STATE.OPEN,
          failures: 5,
          successes: 0,
          nextAttempt: Date.now() + 10000,
          updatedAt: Date.now(),
        }),
      }

      const { kv } = createCircuitStateNamespace(initialState)
      const env = createMockEnv({ OPENROUTER_CIRCUIT_STATE: kv })
      const breaker = new CircuitBreaker('load-test', DEFAULT_CIRCUIT_CONFIG, env)

      // Should load OPEN state from KV
      expect(await breaker.isClosed()).toBe(false)
      expect(breaker.getState().state).toBe(CIRCUIT_STATE.OPEN)
      expect(breaker.getState().failures).toBe(5)
    })

    it('handles missing KV namespace gracefully', async () => {
      const env = createMockEnv()
      // @ts-expect-error - Intentionally testing missing KV
      env.OPENROUTER_CIRCUIT_STATE = undefined

      const breaker = new CircuitBreaker('no-kv', DEFAULT_CIRCUIT_CONFIG, env)

      // Should still work without KV
      await expect(breaker.recordFailure()).resolves.not.toThrow()
      await expect(breaker.isClosed()).resolves.toBeDefined()
    })
  })

  describe('Counter Management', () => {
    it('resets failures on success', async () => {
      const env = createMockEnv()
      const breaker = new CircuitBreaker('test-model', DEFAULT_CIRCUIT_CONFIG, env)

      await breaker.recordFailure()
      await breaker.recordFailure()
      expect(breaker.getState().failures).toBe(2)

      await breaker.recordSuccess()
      expect(breaker.getState().failures).toBe(0)
    })

    it('resets successes on failure', async () => {
      const env = createMockEnv()
      const config: CircuitBreakerConfig = {
        ...DEFAULT_CIRCUIT_CONFIG,
        failureThreshold: 10,
      }
      const breaker = new CircuitBreaker('test-model', config, env)

      await breaker.recordSuccess()
      await breaker.recordSuccess()
      expect(breaker.getState().successes).toBe(2)

      await breaker.recordFailure()
      expect(breaker.getState().successes).toBe(0)
    })
  })
})

// ============================================
// Retry Logic Tests
// ============================================

describe('withRetry', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('returns result without retries when operation succeeds', async () => {
    const operation = vi.fn(async () => 'success')
    const config: RetryConfig = {
      ...DEFAULT_RETRY_CONFIG,
      maxAttempts: 3,
    }

    const result = await withRetry(operation, config)

    expect(result).toBe('success')
    expect(operation).toHaveBeenCalledOnce()
  })

  it('retries on retryable errors', async () => {
    const error = Object.assign(new Error('Connection reset'), {
      name: 'ECONNRESET',
    })

    const operation = vi
      .fn()
      .mockRejectedValueOnce(error)
      .mockResolvedValue('recovered')

    const config: RetryConfig = {
      ...DEFAULT_RETRY_CONFIG,
      maxAttempts: 3,
      initialDelayMs: 100,
      retryableErrors: ['ECONNRESET'],
    }

    const promise = withRetry(operation, config)

    // Advance timers asynchronously to trigger retry
    await vi.advanceTimersByTimeAsync(100)

    await expect(promise).resolves.toBe('recovered')
    expect(operation).toHaveBeenCalledTimes(2)
  })

  it('uses exponential backoff for retries', async () => {
    const error = Object.assign(new Error('Timeout'), { name: 'ETIMEDOUT' })

    const operation = vi
      .fn()
      .mockRejectedValueOnce(error)
      .mockRejectedValueOnce(error)
      .mockResolvedValue('success')

    const config: RetryConfig = {
      maxAttempts: 3,
      initialDelayMs: 100,
      maxDelayMs: 10000,
      backoffFactor: 2,
      retryableStatuses: [],
      retryableErrors: ['ETIMEDOUT'],
    }

    const promise = withRetry(operation, config)

    // First retry: 100ms delay
    await vi.advanceTimersByTimeAsync(100)
    // Second retry: 200ms delay (100 * 2^1)
    await vi.advanceTimersByTimeAsync(200)

    await expect(promise).resolves.toBe('success')
    expect(operation).toHaveBeenCalledTimes(3)
  })

  it('respects maximum delay cap', async () => {
    const error = Object.assign(new Error('Error'), { name: 'ECONNRESET' })

    const operation = vi.fn().mockRejectedValue(error)

    const config: RetryConfig = {
      maxAttempts: 5,
      initialDelayMs: 1000,
      maxDelayMs: 2000, // Cap at 2 seconds
      backoffFactor: 10,
      retryableStatuses: [],
      retryableErrors: ['ECONNRESET'],
    }

    const promise = withRetry(operation, config)

    // Delays would be: 1000, 10000 (capped to 2000), 100000 (capped to 2000), ...
    await vi.advanceTimersByTimeAsync(1000)
    await vi.advanceTimersByTimeAsync(2000)
    await vi.advanceTimersByTimeAsync(2000)
    await vi.advanceTimersByTimeAsync(2000)

    await expect(promise).rejects.toThrow('Error')
    expect(operation).toHaveBeenCalledTimes(5)
  })

  it('does not retry non-retryable errors', async () => {
    const operation = vi.fn(async () => {
      throw new Error('Fatal error')
    })

    const config: RetryConfig = {
      ...DEFAULT_RETRY_CONFIG,
      maxAttempts: 3,
      retryableErrors: ['ECONNRESET'], // Fatal error not in list
    }

    await expect(withRetry(operation, config)).rejects.toThrow('Fatal error')
    expect(operation).toHaveBeenCalledOnce()
  })

  it('stops retrying after max attempts', async () => {
    const error = Object.assign(new Error('Persistent error'), {
      name: 'ECONNRESET',
    })

    const operation = vi.fn().mockRejectedValue(error)

    const config: RetryConfig = {
      maxAttempts: 3,
      initialDelayMs: 50,
      maxDelayMs: 1000,
      backoffFactor: 2,
      retryableStatuses: [],
      retryableErrors: ['ECONNRESET'],
    }

    const promise = withRetry(operation, config)

    await vi.advanceTimersByTimeAsync(50) // Retry 1
    await vi.advanceTimersByTimeAsync(100) // Retry 2

    await expect(promise).rejects.toThrow('Persistent error')
    expect(operation).toHaveBeenCalledTimes(3)
  })
})

// ============================================
// executeWithResilience Tests
// ============================================

describe('executeWithResilience', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(0)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('returns success result with metadata', async () => {
    const env = createMockEnv()
    const operation = vi.fn(async () => ({ data: 'response' }))

    const result = await executeWithResilience(operation, {
      modelId: 'test-model',
      modelConfig: BASE_MODEL_CONFIG,
      env,
      retryConfig: DEFAULT_RETRY_CONFIG,
    })

    expect(result.success).toBe(true)
    expect(result.data).toEqual({ data: 'response' })
    expect(result.attempts).toBe(1)
    expect(result.latencyMs).toBeGreaterThanOrEqual(0)
  })

  it('short-circuits when circuit breaker is open', async () => {
    const initialState = {
      'circuit:blocked-model': JSON.stringify({
        state: CIRCUIT_STATE.OPEN,
        failures: 10,
        successes: 0,
        nextAttempt: Date.now() + 100000,
        updatedAt: Date.now(),
      }),
    }

    const { kv } = createCircuitStateNamespace(initialState)
    const env = createMockEnv({ OPENROUTER_CIRCUIT_STATE: kv })
    const operation = vi.fn(async () => 'should-not-run')

    const result = await executeWithResilience(operation, {
      modelId: 'blocked-model',
      modelConfig: BASE_MODEL_CONFIG,
      env,
    })

    expect(result.success).toBe(false)
    expect(result.attempts).toBe(0)
    expect(result.error?.message).toContain('Circuit breaker open')
    expect(operation).not.toHaveBeenCalled()
  })

  it('records failure and updates circuit state on error', async () => {
    const env = createMockEnv()
    const operation = vi.fn(async () => {
      throw new Error('Service unavailable')
    })

    const result = await executeWithResilience(operation, {
      modelId: 'failing-model',
      modelConfig: BASE_MODEL_CONFIG,
      env,
      retryConfig: {
        ...DEFAULT_RETRY_CONFIG,
        maxAttempts: 1,
        retryableErrors: [],
      },
    })

    expect(result.success).toBe(false)
    expect(result.error?.message).toBe('Service unavailable')
    expect(result.attempts).toBe(1)
  })

  it('includes accurate latency measurement', async () => {
    const env = createMockEnv()
    const operation = vi.fn(async () => {
      vi.advanceTimersByTime(150)
      return 'delayed-response'
    })

    const result = await executeWithResilience(operation, {
      modelId: 'test-model',
      modelConfig: BASE_MODEL_CONFIG,
      env,
    })

    expect(result.latencyMs).toBeGreaterThanOrEqual(150)
  })
})

// ============================================
// executeOpenRouterRequest Tests
// ============================================

describe('executeOpenRouterRequest', () => {
  it('wraps OpenRouter client with resilience', async () => {
    const env = createMockEnv()
    const mockResponse = new Response('{"result": "ok"}', { status: 200 })
    const mockClient = {
      request: vi.fn(async () => mockResponse),
    }

    const payload = {
      model: 'anthropic/claude-3.5-sonnet',
      messages: [{ role: 'user' as const, content: 'Hello' }],
    }

    const result = await executeOpenRouterRequest(payload, mockClient, {
      modelId: 'claude-3-5-sonnet',
      modelConfig: BASE_MODEL_CONFIG,
      env,
    })

    expect(result.success).toBe(true)
    expect(result.data).toBe(mockResponse)
    expect(mockClient.request).toHaveBeenCalledWith(payload)
  })
})
