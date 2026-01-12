import { describe, it, expect, beforeEach } from 'vitest'
import { getTaskRouter } from '../../../src/lib/multi-agent/coordinator/task-router'

describe('TaskRouter', () => {
  const router = getTaskRouter()

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
