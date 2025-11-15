/**
 * Tests for Trending Routes - Hotspots Endpoint
 * Tests keyword extraction, caching, and category classification
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Env } from '../../src/types/env'

// Mock Supabase
vi.mock('../../src/lib/supabase', () => ({
  createSupabaseClient: vi.fn(() => ({
    from: vi.fn((table: string) => {
      if (table === 'messages') {
        return {
          select: vi.fn(() => ({
            eq: vi.fn(() => ({
              order: vi.fn(() => ({
                limit: vi.fn(async () => ({
                  data: [
                    { content: 'What is the Bitcoin price today?' },
                    { content: 'Ethereum gas fees are high' },
                    { content: 'Solana network performance' },
                    { content: 'DeFi protocols comparison' },
                    { content: 'NFT market trends' },
                    { content: 'Bitcoin halving event' },
                    { content: 'Ethereum staking rewards' },
                    { content: 'Uniswap liquidity pools' },
                    { content: 'Polygon scalability features' },
                    { content: 'Web3 development tools' },
                    { content: 'Polygon layer 2 network' },
                    { content: 'Web3 infrastructure' },
                    { content: 'Polygon MATIC token' },
                    { content: 'Web3 ecosystem growth' },
                    { content: 'Uniswap V3 features' },
                    { content: 'DeFi yield farming strategies' },
                    { content: 'Uniswap UNI token governance' },
                    { content: 'NFT collections gaining popularity' },
                    { content: 'NFT art and gaming' },
                    { content: 'Solana transaction speed analysis' },
                    { content: 'SOL token price prediction' },
                    { content: 'DeFi security best practices' },
                    { content: 'Solana ecosystem growth' },
                  ],
                  error: null,
                })),
              })),
            })),
          })),
        }
      }
      return {
        upsert: vi.fn(async () => ({ error: null })),
      }
    }),
  })),
}))

import { Hono } from 'hono'
import trending from '../../src/routes/trending'

// Create a test app that mimics production routing structure
const trendingApp = new Hono<{ Bindings: Env }>()
trendingApp.route('/api/v1/trending', trending)

const BASE_URL = 'https://example.com/api/v1/trending/hotspots'

async function fetchTrendingHotspots({
  queryParams = '',
  env,
}: {
  queryParams?: string
  env?: Env
} = {}) {
  const url = queryParams ? `${BASE_URL}?${queryParams}` : BASE_URL

  const request = new Request(url, {
    method: 'GET',
    headers: {
      'cf-connecting-ip': '203.0.113.42',
    },
  })

  return trendingApp.fetch(request, env ?? createMockEnv())
}

describe('Trending - Hotspots Endpoint', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Response Structure', () => {
    it('returns 200 and correct response structure', async () => {
      const response = await fetchTrendingHotspots()
      expect(response.status).toBe(200)

      const body = await response.json()
      expect(body).toHaveProperty('hotspots')
      expect(body).toHaveProperty('count')
      expect(body).toHaveProperty('updated_at')
      expect(Array.isArray(body.hotspots)).toBe(true)
    })

    it('returns hotspots with required fields', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      expect(body.hotspots.length).toBeGreaterThan(0)

      const hotspot = body.hotspots[0]
      expect(hotspot).toHaveProperty('id')
      expect(hotspot).toHaveProperty('keyword')
      expect(hotspot).toHaveProperty('count')
      expect(hotspot).toHaveProperty('trend')
      expect(hotspot).toHaveProperty('category')
      expect(hotspot.trend).toBe('up')
    })
  })

  describe('Keyword Extraction and Counting', () => {
    it('correctly counts keyword frequencies', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      // Bitcoin appears twice in test data
      const bitcoinHotspot = body.hotspots.find((h: any) => h.keyword === 'bitcoin')
      expect(bitcoinHotspot).toBeDefined()
      expect(bitcoinHotspot.count).toBe(2)

      // Ethereum appears twice
      const ethHotspot = body.hotspots.find((h: any) => h.keyword === 'ethereum')
      expect(ethHotspot).toBeDefined()
      expect(ethHotspot.count).toBe(2)
    })

    it('performs case-insensitive keyword matching', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      // Should match regardless of case in content
      const bitcoinHotspot = body.hotspots.find((h: any) => h.keyword === 'bitcoin')
      expect(bitcoinHotspot).toBeDefined()
    })

    it('sorts hotspots by count in descending order', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      for (let i = 0; i < body.hotspots.length - 1; i++) {
        expect(body.hotspots[i].count).toBeGreaterThanOrEqual(body.hotspots[i + 1].count)
      }
    })
  })

  describe('Category Classification', () => {
    it('classifies Layer 1 keywords correctly', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      const bitcoinHotspot = body.hotspots.find((h: any) => h.keyword === 'bitcoin')
      expect(bitcoinHotspot?.category).toBe('Layer 1')

      const ethHotspot = body.hotspots.find((h: any) => h.keyword === 'ethereum')
      expect(ethHotspot?.category).toBe('Layer 1')

      const solHotspot = body.hotspots.find((h: any) => h.keyword === 'solana')
      expect(solHotspot?.category).toBe('Layer 1')
    })

    it('classifies DeFi keywords correctly', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      const defiHotspot = body.hotspots.find((h: any) => h.keyword === 'defi')
      expect(defiHotspot?.category).toBe('DeFi')

      const uniHotspot = body.hotspots.find((h: any) => h.keyword === 'uniswap')
      expect(uniHotspot?.category).toBe('DeFi')
    })

    it('classifies Infrastructure keywords correctly', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      const polygonHotspot = body.hotspots.find((h: any) => h.keyword === 'polygon')
      expect(polygonHotspot?.category).toBe('Infrastructure')
    })

    it('classifies Trends keywords correctly', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      const nftHotspot = body.hotspots.find((h: any) => h.keyword === 'nft')
      expect(nftHotspot?.category).toBe('Trends')

      const web3Hotspot = body.hotspots.find((h: any) => h.keyword === 'web3')
      expect(web3Hotspot?.category).toBe('Trends')
    })
  })

  describe('Parameter Handling', () => {
    it('uses default limit of 10 when not specified', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      expect(body.hotspots.length).toBeLessThanOrEqual(10)
    })

    it('respects custom limit parameter', async () => {
      const response = await fetchTrendingHotspots({
        queryParams: 'limit=5',
      })
      const body = await response.json()

      expect(body.hotspots.length).toBeLessThanOrEqual(5)
      expect(body.count).toBeLessThanOrEqual(5)
    })

    it('handles large limit values', async () => {
      const response = await fetchTrendingHotspots({
        queryParams: 'limit=20',
      })
      const body = await response.json()

      expect(body.hotspots.length).toBeLessThanOrEqual(20)
    })
  })

  describe('Caching Behavior', () => {
    it('caches results on first request', async () => {
      const env = createMockEnv()
      const response = await fetchTrendingHotspots({ env })

      expect(response.status).toBe(200)

      // Check that cache was populated
      const cacheKey = 'trending:hotspots:10'
      const cached = await env.CACHE!.get(cacheKey)
      expect(cached).not.toBeNull()
    })

    it('returns cached data on second request', async () => {
      const env = createMockEnv()

      // First request
      await fetchTrendingHotspots({ env })

      // Second request should use cache
      const response2 = await fetchTrendingHotspots({ env })
      expect(response2.status).toBe(200)

      const body = await response2.json()
      expect(body.hotspots).toBeDefined()
    })

    it('bypasses cache when force_refresh is true', async () => {
      const env = createMockEnv()

      // First request to populate cache
      await fetchTrendingHotspots({ env })

      // Second request with force_refresh
      const response = await fetchTrendingHotspots({
        queryParams: 'force_refresh=true',
        env,
      })

      expect(response.status).toBe(200)
      // Should still return valid data
      const body = await response.json()
      expect(body.hotspots).toBeDefined()
    })

    it('uses different cache keys for different limits', async () => {
      const env = createMockEnv()

      await fetchTrendingHotspots({ env, queryParams: 'limit=5' })
      await fetchTrendingHotspots({ env, queryParams: 'limit=10' })

      const cache5 = await env.CACHE!.get('trending:hotspots:5')
      const cache10 = await env.CACHE!.get('trending:hotspots:10')

      expect(cache5).not.toBeNull()
      expect(cache10).not.toBeNull()
      expect(cache5).not.toBe(cache10)
    })
  })

  describe('Error Handling', () => {
    it('handles Supabase query errors gracefully', async () => {
      const { createSupabaseClient } = await import('../../src/lib/supabase')
      vi.mocked(createSupabaseClient).mockReturnValueOnce({
        from: vi.fn(() => ({
          select: vi.fn(() => ({
            eq: vi.fn(() => ({
              order: vi.fn(() => ({
                limit: vi.fn(async () => ({
                  data: null,
                  error: { message: 'Database connection failed' },
                })),
              })),
            })),
          })),
        })),
      } as any)

      const response = await fetchTrendingHotspots()
      expect(response.status).toBe(500)

      const body = await response.json()
      expect(body.error.code).toBe('DATABASE_ERROR')
    })

    it('handles empty message list gracefully', async () => {
      const { createSupabaseClient } = await import('../../src/lib/supabase')
      vi.mocked(createSupabaseClient).mockReturnValueOnce({
        from: vi.fn(() => ({
          select: vi.fn(() => ({
            eq: vi.fn(() => ({
              order: vi.fn(() => ({
                limit: vi.fn(async () => ({
                  data: [],
                  error: null,
                })),
              })),
            })),
          })),
        })),
      } as any)

      const response = await fetchTrendingHotspots()
      expect(response.status).toBe(200)

      const body = await response.json()
      expect(body.hotspots).toEqual([])
      expect(body.count).toBe(0)
    })

    it('handles malformed cache data gracefully', async () => {
      const env = createMockEnv()

      // Manually inject malformed JSON into cache
      await env.CACHE!.put('trending:hotspots:10', '{invalid json}')

      // Should fall back to database query
      const response = await fetchTrendingHotspots({ env })
      expect(response.status).toBe(200)

      const body = await response.json()
      expect(body.hotspots).toBeDefined()
      expect(Array.isArray(body.hotspots)).toBe(true)
    })
  })
})

function createMockEnv(overrides: Partial<Env> = {}): Env {
  return {
    ENVIRONMENT: 'test',
    SUPABASE_URL: 'https://example.supabase.co',
    SUPABASE_ANON_KEY: 'anon-key',
    OPENROUTER_API_KEY: 'test-key',
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
