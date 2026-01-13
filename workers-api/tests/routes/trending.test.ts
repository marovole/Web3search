/**
 * Tests for Trending Routes - Hotspots Endpoint
 * Tests response structure, scoring, caching, and error handling
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Env } from '../../src/types/env'

// Mock Supabase
vi.mock('../../src/lib/supabase', () => {
  const mockClient = vi.fn(() => ({
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
  }))

  return {
    createSupabaseClient: mockClient,
    getSupabaseClient: mockClient
  }
})

// Mock CoinGecko to avoid real API calls during tests
vi.mock('../../src/lib/coingecko', () => {
  const coinDataById = {
    bitcoin: {
      symbol: 'BTC',
      name: 'Bitcoin',
      price_usd: 30000,
      price_change_24h: 2.5,
      market_cap: 600_000_000,
      market_cap_rank: 1,
    },
    ethereum: {
      symbol: 'ETH',
      name: 'Ethereum',
      price_usd: 2000,
      price_change_24h: 1.2,
      market_cap: 300_000_000,
      market_cap_rank: 2,
    },
    solana: {
      symbol: 'SOL',
      name: 'Solana',
      price_usd: 120,
      price_change_24h: -0.8,
      market_cap: 40_000_000,
      market_cap_rank: 10,
    },
    cardano: {
      symbol: 'ADA',
      name: 'Cardano',
      price_usd: 0.5,
      price_change_24h: 0.4,
      market_cap: 18_000_000,
      market_cap_rank: 12,
    },
    polygon: {
      symbol: 'MATIC',
      name: 'Polygon',
      price_usd: 0.9,
      price_change_24h: 1.8,
      market_cap: 9_000_000,
      market_cap_rank: 15,
    },
    'avalanche-2': {
      symbol: 'AVAX',
      name: 'Avalanche',
      price_usd: 32,
      price_change_24h: 3.1,
      market_cap: 7_000_000,
      market_cap_rank: 18,
    },
    polkadot: {
      symbol: 'DOT',
      name: 'Polkadot',
      price_usd: 7,
      price_change_24h: -1.4,
      market_cap: 6_000_000,
      market_cap_rank: 20,
    },
    chainlink: {
      symbol: 'LINK',
      name: 'Chainlink',
      price_usd: 14,
      price_change_24h: 0.9,
      market_cap: 5_000_000,
      market_cap_rank: 22,
    },
    uniswap: {
      symbol: 'UNI',
      name: 'Uniswap',
      price_usd: 6,
      price_change_24h: -0.2,
      market_cap: 4_000_000,
      market_cap_rank: 25,
    },
  }

  const aliasMap: Record<string, string> = {
    btc: 'bitcoin',
    eth: 'ethereum',
    sol: 'solana',
    matic: 'polygon',
    avax: 'avalanche-2',
    dot: 'polkadot',
    link: 'chainlink',
    uni: 'uniswap',
  }

  const resolveCoinId = (symbol: string) => {
    const normalized = symbol.toLowerCase().trim()
    return aliasMap[normalized] ?? normalized
  }

  const getCoinPrice = vi.fn(async (coinId: string) => {
    const data = coinDataById[coinId as keyof typeof coinDataById]
    if (data) {
      return data
    }
    return { error: 'NOT_FOUND', message: 'Coin not found' }
  })

  return {
    createCoinGeckoClient: () => ({
      getBatchPrices: vi.fn().mockResolvedValue(new Map()),
      getCoinPrice,
      resolveCoinId: vi.fn((symbol: string) => resolveCoinId(symbol)),
    }),
    getCachedBatchPrices: vi.fn().mockResolvedValue(new Map()),
    getCachedCoinPrice: vi.fn().mockResolvedValue({ error: 'NOT_FOUND', message: 'Coin not found' }),
  }
})

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
      expect(hotspot).toHaveProperty('coin_id')
      expect(hotspot).toHaveProperty('symbol')
      expect(hotspot).toHaveProperty('name')
      expect(hotspot).toHaveProperty('market_cap_rank')
      expect(hotspot).toHaveProperty('total_score')
      expect(hotspot).toHaveProperty('scores_breakdown')
      expect(hotspot).toHaveProperty('timestamp')
      expect(hotspot.scores_breakdown).toHaveProperty('price')
      expect(hotspot.scores_breakdown).toHaveProperty('news')
      expect(body.count).toBe(body.hotspots.length)
    })
  })

  describe('Scoring and Ranking', () => {
    it('sorts hotspots by total_score in descending order', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      for (let i = 0; i < body.hotspots.length - 1; i++) {
        expect(body.hotspots[i].total_score).toBeGreaterThanOrEqual(
          body.hotspots[i + 1].total_score
        )
      }
    })

    it('returns numeric scores for hotspots', async () => {
      const response = await fetchTrendingHotspots()
      const body = await response.json()

      const hotspot = body.hotspots[0]
      expect(typeof hotspot.total_score).toBe('number')
      expect(typeof hotspot.scores_breakdown.price).toBe('number')
      expect(typeof hotspot.scores_breakdown.news).toBe('number')
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

    it('falls back to default coins when message list is empty', async () => {
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
      expect(body.hotspots.length).toBeGreaterThan(0)
      expect(body.count).toBe(body.hotspots.length)
      expect(body.hotspots.some((hotspot: { coin_id: string }) => hotspot.coin_id === 'bitcoin')).toBe(true)
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
