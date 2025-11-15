/**
 * Tests for Search Providers Module
 * Tests Tavily, Serper integrations, failover logic, and telemetry
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Env } from '../../src/types/env'
import {
  fetchSearchResultsForQueries,
  type NormalizedSearchResult,
} from '../../src/lib/search-providers'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch as any

describe('Search Providers Module', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
    // Clear console spies
    vi.spyOn(console, 'info').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  // ============================================================================
  // Helper Functions
  // ============================================================================

  function createMockEnv(overrides: Partial<Env> = {}): Env {
    return {
      ENVIRONMENT: 'test',
      SUPABASE_URL: 'https://example.supabase.co',
      SUPABASE_ANON_KEY: 'anon-key',
      BRAVE_SEARCH_API_KEY: 'brave-test-key',
      TAVILY_API_KEY: 'tavily-test-key',
      SERPER_API_KEY: 'serper-test-key',
      OPENROUTER_API_KEY: 'openrouter-test-key',
      CACHE: createInMemoryKV(),
      ...overrides,
    } as Env
  }

  function createInMemoryKV(): KVNamespace {
    const store = new Map<string, string>()
    return {
      get: async (key: string) => (store.has(key) ? store.get(key)! : null),
      put: async (key: string, value: string) => {
        store.set(key, value)
      },
      delete: async (key: string) => {
        store.delete(key)
      },
      list: async () => ({
        keys: [],
        list_complete: true,
      }),
    } as unknown as KVNamespace
  }

  function createBraveResponse(count = 3) {
    return {
      web: {
        results: Array.from({ length: count }, (_, i) => ({
          title: `Brave Result ${i + 1}`,
          description: `Brave snippet ${i + 1}`,
          url: `https://brave.example.com/result/${i + 1}`,
        })),
      },
    }
  }

  function createTavilyResponse(count = 3) {
    return {
      results: Array.from({ length: count }, (_, i) => ({
        title: `Tavily Result ${i + 1}`,
        snippet: `Tavily snippet ${i + 1}`,
        url: `https://tavily.example.com/result/${i + 1}`,
        score: 0.9 - i * 0.1,
      })),
    }
  }

  function createSerperResponse(count = 3) {
    return {
      organic: Array.from({ length: count }, (_, i) => ({
        title: `Serper Result ${i + 1}`,
        snippet: `Serper snippet ${i + 1}`,
        link: `https://serper.example.com/result/${i + 1}`,
      })),
    }
  }

  // ============================================================================
  // Brave Search Provider Tests
  // ============================================================================

  describe('Brave Search Provider', () => {
    it('successfully fetches and normalizes results', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(3),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(3)
      expect(results[0]).toMatchObject({
        provider: 'brave',
        title: 'Brave Result 1',
        snippet: 'Brave snippet 1',
        url: 'https://brave.example.com/result/1',
      })
      expect(results[0].relevance_score).toBeGreaterThan(0.5)
    })

    it('handles missing API key gracefully', async () => {
      const env = createMockEnv({
        BRAVE_SEARCH_API_KEY: undefined,
        TAVILY_API_KEY: undefined,
        SERPER_API_KEY: undefined,
      })
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toEqual([])
      expect(console.warn).toHaveBeenCalledWith(
        'No search API keys configured, cannot fetch results'
      )
    })

    it('handles HTTP 429 rate limit error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests',
      })

      // Mock Tavily to succeed as fallback
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createTavilyResponse(2),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      // Should have Tavily results (failover succeeded)
      expect(results).toHaveLength(2)
      expect(results[0].provider).toBe('tavily')
    })

    it('handles HTTP 500 server error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      })

      // Mock Tavily to succeed
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createTavilyResponse(1),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(1)
      expect(results[0].provider).toBe('tavily')
    })

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network failure'))

      // Mock Tavily to succeed
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createTavilyResponse(1),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(1)
      expect(results[0].provider).toBe('tavily')
    })
  })

  // ============================================================================
  // Tavily Search Provider Tests
  // ============================================================================

  describe('Tavily Search Provider', () => {
    it('successfully fetches and normalizes results', async () => {
      // Mock Brave to fail
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      })

      // Mock Tavily to succeed
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createTavilyResponse(3),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['blockchain'], env)

      expect(results).toHaveLength(3)
      expect(results[0]).toMatchObject({
        provider: 'tavily',
        title: 'Tavily Result 1',
        snippet: 'Tavily snippet 1',
        url: 'https://tavily.example.com/result/1',
      })
      // Tavily result 1 has score 0.9
      expect(results[0].relevance_score).toBe(0.9)
    })

    it('normalizes Tavily scores correctly (0-1 range)', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          results: [
            { title: 'T1', snippet: 'S1', url: 'https://t.com/1', score: 0.95 },
            { title: 'T2', snippet: 'S2', url: 'https://t.com/2', score: 0.75 },
          ],
        }),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['test'], env)

      expect(results[0].relevance_score).toBe(0.95)
      expect(results[1].relevance_score).toBe(0.75)
    })

    it('normalizes Tavily scores correctly (0-100 range)', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          results: [
            { title: 'T1', snippet: 'S1', url: 'https://t.com/1', score: 95 },
            { title: 'T2', snippet: 'S2', url: 'https://t.com/2', score: 75 },
          ],
        }),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['test'], env)

      expect(results[0].relevance_score).toBe(0.95) // 95/100
      expect(results[1].relevance_score).toBe(0.75) // 75/100
    })

    it('falls back to position-based scoring when score is missing', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          results: [
            { title: 'T1', snippet: 'S1', url: 'https://t.com/1' }, // No score
            { title: 'T2', snippet: 'S2', url: 'https://t.com/2' }, // No score
          ],
        }),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['test'], env)

      // Position-based: 1.0 for index 0, 0.95 for index 1
      expect(results[0].relevance_score).toBe(1.0)
      expect(results[1].relevance_score).toBe(0.95)
    })

    it('handles missing API key gracefully', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails

      const env = createMockEnv({
        TAVILY_API_KEY: undefined,
        SERPER_API_KEY: undefined,
      })
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toEqual([])
    })

    it('handles rate limit (429) error', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests',
      })

      // Mock Serper to succeed
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createSerperResponse(1),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(1)
      expect(results[0].provider).toBe('serper')
    })

    it('handles network errors', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails
      mockFetch.mockRejectedValueOnce(new Error('Network failure'))

      // Mock Serper to succeed
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createSerperResponse(1),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(1)
      expect(results[0].provider).toBe('serper')
    })
  })

  // ============================================================================
  // Serper Search Provider Tests
  // ============================================================================

  describe('Serper Search Provider', () => {
    it('successfully fetches and normalizes results', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Tavily fails

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createSerperResponse(3),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['defi'], env)

      expect(results).toHaveLength(3)
      expect(results[0]).toMatchObject({
        provider: 'serper',
        title: 'Serper Result 1',
        snippet: 'Serper snippet 1',
        url: 'https://serper.example.com/result/1',
      })
      expect(results[0].relevance_score).toBe(1.0) // Position 0
      expect(results[1].relevance_score).toBe(0.95) // Position 1
    })

    it('handles missing API key gracefully', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Tavily fails

      const env = createMockEnv({ SERPER_API_KEY: undefined })
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toEqual([])
    })

    it('handles rate limit (429) error', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Tavily fails

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests',
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      // All providers failed
      expect(results).toEqual([])
    })

    it('handles network errors', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Tavily fails
      mockFetch.mockRejectedValueOnce(new Error('Network failure'))

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toEqual([])
    })
  })

  // ============================================================================
  // Provider Failover Logic Tests
  // ============================================================================

  describe('Provider Failover Logic', () => {
    it('returns Brave results when Brave succeeds (no failover)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(3),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(3)
      expect(results[0].provider).toBe('brave')
      // Should only call Brave (1 fetch call)
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    it('falls back to Tavily when Brave fails', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createTavilyResponse(2),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(2)
      expect(results[0].provider).toBe('tavily')
      // 2 calls: Brave + Tavily
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })

    it('falls back to Serper when Brave and Tavily fail', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails
      mockFetch.mockResolvedValueOnce({ ok: false, status: 429 }) // Tavily fails

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createSerperResponse(1),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(1)
      expect(results[0].provider).toBe('serper')
      // 3 calls: Brave + Tavily + Serper
      expect(mockFetch).toHaveBeenCalledTimes(3)
    })

    it('returns empty array when all providers fail', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails
      mockFetch.mockResolvedValueOnce({ ok: false, status: 429 }) // Tavily fails
      mockFetch.mockResolvedValueOnce({ ok: false, status: 503 }) // Serper fails

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toEqual([])
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('All providers failed'),
        expect.any(Object)
      )
    })

    it('treats empty results as failure and triggers failover', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ web: { results: [] } }), // Brave returns empty
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createTavilyResponse(2),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(2)
      expect(results[0].provider).toBe('tavily')
    })
  })

  // ============================================================================
  // Caching Tests
  // ============================================================================

  describe('Caching Behavior', () => {
    it('caches successful results with provider-specific keys', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(2),
      })

      const env = createMockEnv()
      await fetchSearchResultsForQueries(['web3'], env)

      // Check cache was populated
      const cacheKey = 'search:brave:web3'
      const cached = await env.CACHE!.get(cacheKey)
      expect(cached).not.toBeNull()

      const parsedCache = JSON.parse(cached!) as NormalizedSearchResult[]
      expect(parsedCache).toHaveLength(2)
      expect(parsedCache[0].provider).toBe('brave')
    })

    it('returns cached results on second request (no API call)', async () => {
      const env = createMockEnv()

      // First request
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(2),
      })
      const results1 = await fetchSearchResultsForQueries(['web3'], env)

      // Second request (should use cache)
      const results2 = await fetchSearchResultsForQueries(['web3'], env)

      expect(results1).toEqual(results2)
      // Only 1 fetch call (first request)
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    it('uses different cache keys for different providers', async () => {
      const env = createMockEnv()

      // Request 1: Brave succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(2),
      })
      await fetchSearchResultsForQueries(['bitcoin'], env)

      // Clear mock and disable Brave for next test
      mockFetch.mockClear()

      // Request 2: Brave disabled, Tavily succeeds
      const env2 = createMockEnv({ BRAVE_SEARCH_API_KEY: undefined })
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createTavilyResponse(3),
      })
      await fetchSearchResultsForQueries(['bitcoin'], env2)

      // Check both caches exist with different keys
      const braveCache = await env.CACHE!.get('search:brave:bitcoin')
      const tavilyCache = await env2.CACHE!.get('search:tavily:bitcoin')

      expect(braveCache).not.toBeNull()
      expect(tavilyCache).not.toBeNull()
      expect(braveCache).not.toEqual(tavilyCache)
    })

    it('handles corrupted cache gracefully (falls back to API)', async () => {
      const env = createMockEnv()

      // Manually inject invalid JSON into cache
      await env.CACHE!.put('search:brave:web3', '{invalid json}')

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(2),
      })

      const results = await fetchSearchResultsForQueries(['web3'], env)

      expect(results).toHaveLength(2)
      // Should have called API due to corrupted cache
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
  })

  // ============================================================================
  // Deduplication and Sorting Tests
  // ============================================================================

  describe('Deduplication and Sorting', () => {
    it('deduplicates results by URL within single provider', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          web: {
            results: [
              {
                title: 'Result 1',
                description: 'Desc 1',
                url: 'https://example.com/page',
              },
              {
                title: 'Result 2',
                description: 'Desc 2',
                url: 'https://example.com/page', // Duplicate URL
              },
              {
                title: 'Result 3',
                description: 'Desc 3',
                url: 'https://example.com/other',
              },
            ],
          },
        }),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['test'], env)

      // Should have 2 results (duplicate removed)
      expect(results).toHaveLength(2)
      expect(results.find((r) => r.url === 'https://example.com/page')).toBeDefined()
      expect(results.find((r) => r.url === 'https://example.com/other')).toBeDefined()
    })

    it('keeps result with highest relevance score when deduplicating', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          web: {
            results: [
              {
                title: 'Low Score',
                description: 'First occurrence',
                url: 'https://example.com/page',
              },
              {
                title: 'High Score',
                description: 'Second occurrence',
                url: 'https://example.com/page',
              },
            ],
          },
        }),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['test'], env)

      expect(results).toHaveLength(1)
      // First result has higher position score (index 0 = 1.0 vs index 1 = 0.95)
      // So should keep the first one
      expect(results[0].snippet).toBe('First occurrence')
    })

    it('sorts results by relevance score descending', async () => {
      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 }) // Brave fails

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          results: [
            { title: 'T1', snippet: 'S1', url: 'https://t.com/1', score: 0.6 },
            { title: 'T2', snippet: 'S2', url: 'https://t.com/2', score: 0.9 },
            { title: 'T3', snippet: 'S3', url: 'https://t.com/3', score: 0.75 },
          ],
        }),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(['test'], env)

      expect(results[0].relevance_score).toBe(0.9) // Highest first
      expect(results[1].relevance_score).toBe(0.75)
      expect(results[2].relevance_score).toBe(0.6) // Lowest last
    })
  })

  // ============================================================================
  // Telemetry Tests
  // ============================================================================

  describe('Telemetry Logging', () => {
    it('logs telemetry for successful provider attempts', async () => {
      const consoleInfoSpy = vi.spyOn(console, 'info')

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(2),
      })

      const env = createMockEnv()
      await fetchSearchResultsForQueries(['web3'], env)

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        '[search-provider]',
        expect.objectContaining({
          provider: 'brave',
          query: 'web3',
          success: true,
          resultCount: 2,
          statusCode: 200,
        })
      )
    })

    it('logs telemetry for failed provider attempts', async () => {
      const consoleInfoSpy = vi.spyOn(console, 'info')

      mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })
      mockFetch.mockResolvedValueOnce({ ok: true, status: 200, json: async () => createTavilyResponse(1) })

      const env = createMockEnv()
      await fetchSearchResultsForQueries(['web3'], env)

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        '[search-provider]',
        expect.objectContaining({
          provider: 'brave',
          success: false,
          errorType: 'http',
          statusCode: 500,
        })
      )
    })

    it('includes cache hit information in telemetry', async () => {
      const consoleInfoSpy = vi.spyOn(console, 'info')
      const env = createMockEnv()

      // First request (cache miss)
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(1),
      })
      await fetchSearchResultsForQueries(['web3'], env)

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        '[search-provider]',
        expect.objectContaining({
          fromCache: false,
        })
      )

      consoleInfoSpy.mockClear()

      // Second request (cache hit)
      await fetchSearchResultsForQueries(['web3'], env)

      expect(consoleInfoSpy).toHaveBeenCalledWith(
        '[search-provider]',
        expect.objectContaining({
          fromCache: true,
          ttfbMs: 0, // Cache hits have 0 TTFB
        })
      )
    })
  })

  // ============================================================================
  // Multiple Query Tests
  // ============================================================================

  describe('Multiple Query Handling', () => {
    it('fetches results for multiple queries in parallel', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(1),
      })

      const env = createMockEnv()
      const results = await fetchSearchResultsForQueries(
        ['web3', 'blockchain', 'defi'],
        env
      )

      // Should have results from all 3 queries
      expect(results.length).toBeGreaterThan(0)
      // Should make 3 fetch calls (one per query)
      expect(mockFetch).toHaveBeenCalledTimes(3)
    })

    it('limits queries to maximum of 10', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => createBraveResponse(1),
      })

      const env = createMockEnv()
      const manyQueries = Array.from({ length: 15 }, (_, i) => `query${i}`)
      await fetchSearchResultsForQueries(manyQueries, env)

      // Should only call 10 times
      expect(mockFetch).toHaveBeenCalledTimes(10)
    })
  })
})
