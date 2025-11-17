/**
 * Performance Tests for Search API
 * Validates response time targets for search endpoints
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { Hono } from 'hono'
import searchRoutes from '../../src/routes/search'
import type { Env } from '../../src/types/env'
import {
  calculateP95,
  calculateAverage,
  runPerformanceTest,
} from '../utils/performance'

// Mock Supabase with fast responses
vi.mock('../../src/lib/supabase', () => {
  const mockResults = [
    {
      id: 1,
      symbol: 'BTC',
      name: 'Bitcoin',
      coingecko_id: 'bitcoin',
      description: 'Digital currency',
      blockchain: 'Bitcoin',
      categories: ['Currency'],
      tags: ['payments'],
    },
    {
      id: 2,
      symbol: 'ETH',
      name: 'Ethereum',
      coingecko_id: 'ethereum',
      description: 'Smart contract platform',
      blockchain: 'Ethereum',
      categories: ['Smart Contract'],
      tags: ['defi'],
    },
  ]

  return {
    getSupabaseClient: vi.fn(() => ({
      from: vi.fn(() => ({
        select: vi.fn(() => ({
          or: vi.fn(() => ({
            order: vi.fn(() => ({
              limit: vi.fn(() => Promise.resolve({ data: mockResults, error: null })),
            })),
          })),
        })),
      })),
    })),
    createSupabaseClient: vi.fn(),
    testDatabaseConnection: vi.fn(async () => true),
  }
})

/**
 * Performance targets
 */
const PERF_TARGETS = {
  AUTOCOMPLETE_P95: 500, // < 500ms for autocomplete
  ITERATIONS: 20,
}

describe('Search API Performance', () => {
  let app: Hono<{ Bindings: Env }>
  let mockEnv: Env

  beforeEach(() => {
    app = new Hono<{ Bindings: Env }>()
    app.route('/api/v1', searchRoutes)

    mockEnv = {
      ENVIRONMENT: 'test',
      SUPABASE_URL: 'https://test.supabase.co',
      SUPABASE_ANON_KEY: 'test-key',
      OPENROUTER_API_KEY: 'test-key',
    }
  })

  it('autocomplete should respond in < 500ms (P95)', async () => {
    const durations = await runPerformanceTest(async () => {
      const response = await app.fetch(
        new Request('https://example.com/api/v1/autocomplete?q=bitcoin'),
        mockEnv
      )
      expect(response.status).toBe(200)
    }, PERF_TARGETS.ITERATIONS)

    const p95 = calculateP95(durations)
    const avg = calculateAverage(durations)

    console.log(`[Autocomplete Performance]`, {
      p95: `${p95.toFixed(2)}ms`,
      avg: `${avg.toFixed(2)}ms`,
      target: `${PERF_TARGETS.AUTOCOMPLETE_P95}ms`,
    })

    // P95 should be under 500ms
    expect(p95).toBeLessThan(PERF_TARGETS.AUTOCOMPLETE_P95)
  })

  it('should handle various query lengths efficiently', async () => {
    const queries = ['a', 'bi', 'bit', 'bitcoin', 'bitcoin price today']

    for (const query of queries) {
      const durations = await runPerformanceTest(async () => {
        const response = await app.fetch(
          new Request(
            `https://example.com/api/v1/autocomplete?q=${encodeURIComponent(query)}`
          ),
          mockEnv
        )
        expect(response.status).toBe(200)
      }, 10)

      const p95 = calculateP95(durations)

      console.log(`[Query Length: ${query.length}]`, {
        query: query.substring(0, 20),
        p95: `${p95.toFixed(2)}ms`,
      })

      expect(p95).toBeLessThan(PERF_TARGETS.AUTOCOMPLETE_P95)
    }
  })

  it('should maintain performance under load', async () => {
    const concurrentRequests = 20
    const start = performance.now()

    // Fire concurrent autocomplete requests
    await Promise.all(
      Array(concurrentRequests)
        .fill(null)
        .map((_, i) =>
          app.fetch(
            new Request(
              `https://example.com/api/v1/autocomplete?q=query${i}`
            ),
            mockEnv
          )
        )
    )

    const duration = performance.now() - start

    console.log(`[Load Test]`, {
      concurrentRequests,
      totalDuration: `${duration.toFixed(2)}ms`,
      avgPerRequest: `${(duration / concurrentRequests).toFixed(2)}ms`,
    })

    // Total time should be reasonable even under load
    expect(duration).toBeLessThan(2000) // Total < 2s for 20 concurrent requests
  })
})
