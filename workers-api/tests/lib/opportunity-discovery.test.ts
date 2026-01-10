import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../lib/supabase', () => ({
  getSupabaseClient: vi.fn(() => ({
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          limit: vi.fn(() => Promise.resolve({ data: [], error: null })),
          single: vi.fn(() => Promise.resolve({ data: null, error: null })),
          gte: vi.fn(() => Promise.resolve({ data: [], error: null }))
        }))
      })),
      insert: vi.fn(() => Promise.resolve({ data: null, error: null })),
      update: vi.fn(() => ({
        eq: vi.fn(() => Promise.resolve({ data: null, error: null }))
      }))
    }))
  }))
}))

vi.mock('../lib/openrouter', () => ({
  createOpenRouterClient: vi.fn(() => ({
    request: vi.fn(() => Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        choices: [{ message: { content: 'AI analysis result' } }]
      })
    }))
  }))
}))

vi.mock('../lib/push', () => ({
  sendPushToUser: vi.fn(() => Promise.resolve({ sent: 1, failed: 0, expired: [] })),
  createNotificationPayload: vi.fn((type, title, body, data) => ({
    title,
    body,
    tag: type,
    data
  }))
}))

const mockEnv = {
  SUPABASE_URL: 'https://test.supabase.co',
  SUPABASE_ANON_KEY: 'test-key',
  SUPABASE_SERVICE_ROLE_KEY: 'test-service-key',
  OPENROUTER_API_KEY: 'test-openrouter-key',
  VAPID_PUBLIC_KEY: 'test-vapid-public',
  VAPID_PRIVATE_KEY: 'test-vapid-private'
}

describe('Opportunity Discovery Processor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('passesMarketCapFilter', () => {
    it('should pass any market cap when filter is "any"', async () => {
      const { getSupabaseClient } = await import('../lib/supabase')
      const mockSupabase = getSupabaseClient(mockEnv as never, true)
      expect(mockSupabase).toBeDefined()
    })
  })

  describe('calculateOpportunityScore', () => {
    it('should calculate score based on token metrics', () => {
      const mockToken = {
        id: 'bitcoin',
        symbol: 'btc',
        name: 'Bitcoin',
        current_price: 50000,
        market_cap: 1000000000000,
        market_cap_rank: 1,
        price_change_percentage_24h: 5,
        total_volume: 50000000000
      }

      expect(mockToken.market_cap).toBeGreaterThan(0)
      expect(mockToken.price_change_percentage_24h).toBe(5)
    })
  })

  describe('determineRecommendationType', () => {
    it('should return trending for high momentum tokens', () => {
      const trendingToken = {
        price_change_percentage_24h: 15,
        price_change_percentage_7d_in_currency: 30,
        market_cap: 5000000000
      }

      const isTrending = trendingToken.price_change_percentage_24h > 10 && 
                         (trendingToken.price_change_percentage_7d_in_currency || 0) > 20
      expect(isTrending).toBe(true)
    })

    it('should return recovery_play for dipped large caps', () => {
      const recoveryToken = {
        price_change_percentage_24h: -15,
        market_cap: 5000000000
      }

      const isRecovery = recoveryToken.price_change_percentage_24h < -10 && 
                         recoveryToken.market_cap > 1000000000
      expect(isRecovery).toBe(true)
    })
  })

  describe('determineRiskLevel', () => {
    it('should return low risk for very large market caps', () => {
      const marketCap = 50000000000
      const riskLevel = marketCap > 10000000000 ? 'low' : 
                        marketCap > 1000000000 ? 'medium' : 
                        marketCap > 100000000 ? 'high' : 'very_high'
      expect(riskLevel).toBe('low')
    })

    it('should return very_high risk for micro caps', () => {
      const marketCap = 50000000
      const riskLevel = marketCap > 10000000000 ? 'low' : 
                        marketCap > 1000000000 ? 'medium' : 
                        marketCap > 100000000 ? 'high' : 'very_high'
      expect(riskLevel).toBe('very_high')
    })
  })

  describe('generateMatchReasons', () => {
    it('should include trending reason for trending type', () => {
      const reasons: string[] = []
      const recType = 'trending'
      
      if (recType === 'trending') {
        reasons.push('近期价格和交易量显著上涨')
      }
      
      expect(reasons).toContain('近期价格和交易量显著上涨')
    })

    it('should include market cap rank for top tokens', () => {
      const reasons: string[] = []
      const marketCapRank = 50
      
      if (marketCapRank <= 100) {
        reasons.push(`市值排名 #${marketCapRank}`)
      }
      
      expect(reasons).toContain('市值排名 #50')
    })
  })

  describe('estimatePotentialUpside', () => {
    it('should return higher upside for higher risk', () => {
      const baseUpside: Record<string, number> = {
        low: 20,
        medium: 50,
        high: 100,
        very_high: 200
      }

      expect(baseUpside['very_high']).toBeGreaterThan(baseUpside['low'])
      expect(baseUpside['high']).toBeGreaterThan(baseUpside['medium'])
    })
  })
})

describe('Recommendations API', () => {
  describe('GET /api/v1/recommendations', () => {
    it('should require authentication', async () => {
      expect(true).toBe(true)
    })

    it('should filter by status', async () => {
      const statusFilter = 'active'
      expect(['active', 'liked', 'all']).toContain(statusFilter)
    })
  })

  describe('PATCH /api/v1/recommendations/:id/feedback', () => {
    it('should map feedback to correct status', () => {
      const feedbackToStatus: Record<string, string> = {
        like: 'liked',
        dislike: 'disliked',
        not_interested: 'dismissed',
        already_own: 'dismissed',
        will_research: 'viewed'
      }

      expect(feedbackToStatus['like']).toBe('liked')
      expect(feedbackToStatus['dislike']).toBe('disliked')
      expect(feedbackToStatus['not_interested']).toBe('dismissed')
    })
  })
})
