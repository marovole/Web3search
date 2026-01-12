import { describe, it, expect } from 'vitest'
import { getTaskRouter } from '../../../src/lib/multi-agent/coordinator/task-router'

describe('TaskRouter', () => {
  const router = getTaskRouter()

  describe('detectIntent', () => {
    it('should detect token_deep_dive intent for queries with addresses', () => {
      const query = 'Analyze this token 0x1234567890123456789012345678901234567890'
      const intent = router.detectIntent(query)
      const route = router.getRoute(intent)!
      expect(intent).toBe('token_deep_dive')
      expect(route.agents).toContain('risk')
      expect(route.agents).toContain('analyzer')
    })

    it('should detect news_synthesis intent for news related queries', () => {
      const queries = [
        'what is the latest news about btc',
        'recent news updates for ethereum'
      ]

      queries.forEach(query => {
        const intent = router.detectIntent(query)
        const route = router.getRoute(intent)!
        expect(intent).toBe('news_synthesis')
        expect(route.agents).toContain('news')
      })
    })

    it('should detect market_analysis intent for price related queries', () => {
      const query = 'what is the market analysis for solana'
      const intent = router.detectIntent(query)
      const route = router.getRoute(intent)!
      expect(intent).toBe('market_analysis')
      expect(route.agents).toContain('researcher')
      expect(route.agents).toContain('analyzer')
    })

    it('should detect portfolio_review intent for portfolio queries', () => {
      const queries = [
        'analyze my portfolio',
        'check my holdings'
      ]

      queries.forEach(query => {
        const intent = router.detectIntent(query)
        const route = router.getRoute(intent)!
        expect(intent).toBe('portfolio_review')
        expect(route.agents).toContain('risk')
      })
    })

    it('should fallback to comprehensive_research for general queries', () => {
      const query = 'tell me about the future of web3'
      const intent = router.detectIntent(query)
      const route = router.getRoute(intent)!
      expect(intent).toBe('comprehensive_research')
      expect(route.agents.length).toBeGreaterThan(3) // Uses most agents
    })
  })

  describe('getAgentIds', () => {
    it('returns correct agents for token_deep_dive', () => {
      const agents = router.getAgentIds('token_deep_dive')
      expect(agents).toContain('researcher')
      expect(agents).toContain('risk')
      expect(agents).toContain('analyzer')
    })

    it('returns correct agents for news_synthesis', () => {
      const agents = router.getAgentIds('news_synthesis')
      expect(agents).toContain('news')
      expect(agents).toContain('reporter')
    })
  })

  describe('adjustConfig', () => {
    it('sets depth to quick for news_synthesis', () => {
      const config = router.adjustConfig('news_synthesis', { depth: 'deep' })
      expect(config.depth).toBe('quick')
    })

    it('sets depth to deep for token_deep_dive', () => {
      const config = router.adjustConfig('token_deep_dive', { depth: 'quick' })
      expect(config.depth).toBe('deep')
    })
  })
})
