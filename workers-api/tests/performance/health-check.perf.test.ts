/**
 * Performance Tests for Health Check Endpoint
 * Validates response time targets and cache hit rates
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { Hono } from 'hono'
import health from '../../src/routes/health'
import type { Env } from '../../src/types/env'
import {
  calculateP95,
  calculateAverage,
  KVMetricsTracker,
  createInstrumentedKV,
  runPerformanceTest,
} from '../utils/performance'

// Mock Supabase
vi.mock('../../src/lib/supabase', () => {
  return {
    testDatabaseConnection: vi.fn(async () => true),
    getSupabaseClient: vi.fn(),
    createSupabaseClient: vi.fn(),
  }
})

/**
 * Performance targets
 */
const PERF_TARGETS = {
  CACHE_HIT_P95: 50, // < 50ms for cache hits
  CACHE_MISS_P95: 300, // < 300ms for cache misses
  CACHE_HIT_RATE: 0.8, // > 80% hit rate
  ITERATIONS: 25, // Test iterations (5 cold + 20 warm)
}

describe('Health Check Performance', () => {
  let app: Hono<{ Bindings: Env }>
  let kvTracker: KVMetricsTracker
  let mockEnv: Env

  beforeEach(() => {
    // Create fresh app instance
    app = new Hono<{ Bindings: Env }>()
    app.route('/api/v1/health', health)

    // Create instrumented KV namespace
    kvTracker = new KVMetricsTracker()
    const instrumentedKV = createInstrumentedKV(kvTracker)

    mockEnv = {
      ENVIRONMENT: 'test',
      SUPABASE_URL: 'https://test.supabase.co',
      SUPABASE_ANON_KEY: 'test-key',
      OPENROUTER_API_KEY: 'test-key',
      CACHE: instrumentedKV,
    }
  })

  it('should respond in < 300ms (P95) with cache enabled', async () => {
    const durations = await runPerformanceTest(async () => {
      await app.fetch(
        new Request('https://example.com/api/v1/health'),
        mockEnv
      )
    }, PERF_TARGETS.ITERATIONS)

    const p95 = calculateP95(durations)
    const avg = calculateAverage(durations)

    console.log(`[Health Check Performance]`, {
      p95: `${p95.toFixed(2)}ms`,
      avg: `${avg.toFixed(2)}ms`,
      target: `${PERF_TARGETS.CACHE_MISS_P95}ms`,
      ...kvTracker.getMetrics(),
    })

    // P95 should be under 300ms
    expect(p95).toBeLessThan(PERF_TARGETS.CACHE_MISS_P95)
  })

  it('should achieve > 80% cache hit rate after warm-up', async () => {
    // Cold start (first request populates cache)
    await app.fetch(
      new Request('https://example.com/api/v1/health'),
      mockEnv
    )

    // Wait for cache write (async)
    await new Promise((resolve) => setTimeout(resolve, 50))

    // Reset tracker to only count warm requests
    kvTracker.reset()

    // Warm requests (should hit cache)
    const warmRequests = 20
    for (let i = 0; i < warmRequests; i++) {
      await app.fetch(
        new Request('https://example.com/api/v1/health'),
        mockEnv
      )
    }

    const metrics = kvTracker.getMetrics()
    console.log(`[Cache Hit Rate]`, metrics)

    // Hit rate should be > 80%
    expect(metrics.hitRate).toBeGreaterThan(PERF_TARGETS.CACHE_HIT_RATE)
    expect(metrics.hits).toBeGreaterThan(0)
  })

  it('cache hits should be < 50ms (P95)', async () => {
    // Warm up cache
    await app.fetch(
      new Request('https://example.com/api/v1/health'),
      mockEnv
    )
    await new Promise((resolve) => setTimeout(resolve, 50))

    // Test cache hit performance
    const cacheDurations = await runPerformanceTest(async () => {
      await app.fetch(
        new Request('https://example.com/api/v1/health'),
        mockEnv
      )
    }, 20)

    const p95 = calculateP95(cacheDurations)
    const avg = calculateAverage(cacheDurations)

    console.log(`[Cache Hit Performance]`, {
      p95: `${p95.toFixed(2)}ms`,
      avg: `${avg.toFixed(2)}ms`,
      target: `${PERF_TARGETS.CACHE_HIT_P95}ms`,
    })

    // Cache hits should be very fast
    expect(p95).toBeLessThan(PERF_TARGETS.CACHE_HIT_P95)
  })

  it('should handle concurrent requests efficiently', async () => {
    const concurrentRequests = 10
    const start = performance.now()

    // Fire concurrent requests
    await Promise.all(
      Array(concurrentRequests)
        .fill(null)
        .map(() =>
          app.fetch(
            new Request('https://example.com/api/v1/health'),
            mockEnv
          )
        )
    )

    const duration = performance.now() - start

    console.log(`[Concurrent Requests]`, {
      count: concurrentRequests,
      totalDuration: `${duration.toFixed(2)}ms`,
      avgPerRequest: `${(duration / concurrentRequests).toFixed(2)}ms`,
    })

    // All concurrent requests should complete quickly
    // (not strictly enforced, but logged for monitoring)
    expect(duration).toBeLessThan(1000) // Total time < 1s
  })
})
