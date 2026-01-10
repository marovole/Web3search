/**
 * Intent Parser Unit Tests
 * Tests for the conversational agent intent parsing system
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  validateIntentConditions,
  buildTaskConfig,
  getIntentTaskType,
  generateConfirmationMessage,
} from '../../src/lib/intent-parser'
import type { ParsedIntent, IntentType } from '../../src/types/agent-intent'

// Helper to create a mock intent
function createMockIntent(overrides: Partial<ParsedIntent> = {}): ParsedIntent {
  return {
    type: 'unknown',
    confidence: 0.9,
    entities: {},
    originalText: 'test message',
    requiresConfirmation: false,
    ...overrides,
  }
}

describe('intent-parser', () => {
  describe('validateIntentConditions', () => {
    it('should validate price alert with all required fields', () => {
      const intent = createMockIntent({
        type: 'create_price_alert',
        entities: {
          tokens: [{ symbol: 'BTC', confidence: 0.95 }],
          priceCondition: { type: 'below', value: 50000, currency: 'usd' },
        },
      })

      const result = validateIntentConditions(intent)
      expect(result.valid).toBe(true)
      expect(result.errors).toHaveLength(0)
    })

    it('should reject price alert without token', () => {
      const intent = createMockIntent({
        type: 'create_price_alert',
        entities: {
          priceCondition: { type: 'below', value: 50000, currency: 'usd' },
        },
      })

      const result = validateIntentConditions(intent)
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('请指定要监控的代币')
    })

    it('should reject price alert without price condition', () => {
      const intent = createMockIntent({
        type: 'create_price_alert',
        entities: {
          tokens: [{ symbol: 'BTC', confidence: 0.95 }],
        },
      })

      const result = validateIntentConditions(intent)
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('请指定价格条件（涨到/跌破多少）')
    })

    it('should reject price alert missing both token and condition', () => {
      const intent = createMockIntent({
        type: 'create_price_alert',
        entities: {},
      })

      const result = validateIntentConditions(intent)
      expect(result.valid).toBe(false)
      expect(result.errors).toHaveLength(2)
    })

    it('should validate risk monitor with token', () => {
      const intent = createMockIntent({
        type: 'create_risk_monitor',
        entities: {
          tokens: [{ symbol: 'ETH', confidence: 0.9 }],
        },
      })

      const result = validateIntentConditions(intent)
      expect(result.valid).toBe(true)
    })

    it('should reject risk monitor without token', () => {
      const intent = createMockIntent({
        type: 'create_risk_monitor',
        entities: {},
      })

      const result = validateIntentConditions(intent)
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('请指定要监控风险的代币')
    })

    it('should validate check_price with token', () => {
      const intent = createMockIntent({
        type: 'check_price',
        entities: {
          tokens: [{ symbol: 'SOL', confidence: 0.95 }],
        },
      })

      const result = validateIntentConditions(intent)
      expect(result.valid).toBe(true)
    })

    it('should reject check_price without token', () => {
      const intent = createMockIntent({
        type: 'check_price',
        entities: {},
      })

      const result = validateIntentConditions(intent)
      expect(result.valid).toBe(false)
      expect(result.errors).toContain('请指定要查询的代币')
    })

    it('should allow pause/resume/delete tasks without task_id (handled elsewhere)', () => {
      const intentTypes: IntentType[] = ['pause_task', 'resume_task', 'delete_task']
      
      for (const type of intentTypes) {
        const intent = createMockIntent({ type, entities: {} })
        const result = validateIntentConditions(intent)
        expect(result.valid).toBe(true)
      }
    })

    it('should allow list_tasks, check_portfolio, get_recommendations without entities', () => {
      const intentTypes: IntentType[] = ['list_tasks', 'check_portfolio', 'get_recommendations']
      
      for (const type of intentTypes) {
        const intent = createMockIntent({ type, entities: {} })
        const result = validateIntentConditions(intent)
        expect(result.valid).toBe(true)
      }
    })
  })

  describe('buildTaskConfig', () => {
    it('should build price alert config', () => {
      const intent = createMockIntent({
        type: 'create_price_alert',
        entities: {
          tokens: [{ symbol: 'BTC', confidence: 0.95 }],
          priceCondition: { type: 'below', value: 50000, currency: 'usd' },
        },
      })

      const config = buildTaskConfig(intent)
      expect(config).toEqual({
        token_id: 'btc',
        symbol: 'BTC',
        condition: {
          type: 'below',
          value: 50000,
          currency: 'usd',
        },
        enabled: true,
      })
    })

    it('should build risk monitor config with default threshold', () => {
      const intent = createMockIntent({
        type: 'create_risk_monitor',
        entities: {
          tokens: [
            { symbol: 'ETH', confidence: 0.9 },
            { symbol: 'SOL', confidence: 0.85 },
          ],
        },
      })

      const config = buildTaskConfig(intent)
      expect(config).toEqual({
        tokens: [
          { token_id: 'eth', symbol: 'ETH' },
          { token_id: 'sol', symbol: 'SOL' },
        ],
        threshold: 70,
        enabled: true,
      })
    })

    it('should build risk monitor config with custom threshold', () => {
      const intent = createMockIntent({
        type: 'create_risk_monitor',
        entities: {
          tokens: [{ symbol: 'LUNA', confidence: 0.9 }],
          riskThreshold: 50,
        },
      })

      const config = buildTaskConfig(intent)
      expect(config.threshold).toBe(50)
    })

    it('should build news brief config with default frequency', () => {
      const intent = createMockIntent({
        type: 'create_news_brief',
        entities: {},
      })

      const config = buildTaskConfig(intent)
      expect(config).toEqual({
        enabled: true,
        frequency: 'daily',
        include_watchlist: true,
        max_articles: 10,
        language: 'zh',
      })
    })

    it('should build news brief config with custom frequency', () => {
      const intent = createMockIntent({
        type: 'create_news_brief',
        entities: { frequency: 'hourly' },
      })

      const config = buildTaskConfig(intent)
      expect(config.frequency).toBe('hourly')
    })

    it('should build portfolio diagnosis config', () => {
      const intent = createMockIntent({
        type: 'create_portfolio_diagnosis',
        entities: {},
      })

      const config = buildTaskConfig(intent)
      expect(config).toEqual({
        enabled: true,
        frequency: 'weekly',
      })
    })

    it('should build opportunity finder config', () => {
      const intent = createMockIntent({
        type: 'create_opportunity_finder',
        entities: {},
      })

      const config = buildTaskConfig(intent)
      expect(config).toEqual({
        enabled: true,
        frequency: 'weekly',
        max_recommendations: 5,
        include_trending: true,
        include_sector_match: true,
        include_similar: true,
      })
    })

    it('should return empty config for unknown intent', () => {
      const intent = createMockIntent({
        type: 'unknown',
        entities: {},
      })

      const config = buildTaskConfig(intent)
      expect(config).toEqual({})
    })
  })

  describe('getIntentTaskType', () => {
    it('should map create intents to task types', () => {
      const mappings: Array<[IntentType, string | null]> = [
        ['create_price_alert', 'price_alert'],
        ['create_risk_monitor', 'risk_monitor'],
        ['create_news_brief', 'news_brief'],
        ['create_portfolio_diagnosis', 'portfolio_health'],
        ['create_opportunity_finder', 'opportunity_finder'],
      ]

      for (const [intentType, expectedTaskType] of mappings) {
        expect(getIntentTaskType(intentType)).toBe(expectedTaskType)
      }
    })

    it('should return null for non-create intents', () => {
      const nonCreateIntents: IntentType[] = [
        'list_tasks',
        'pause_task',
        'resume_task',
        'delete_task',
        'check_price',
        'check_portfolio',
        'get_recommendations',
        'update_preferences',
        'unknown',
      ]

      for (const intentType of nonCreateIntents) {
        expect(getIntentTaskType(intentType)).toBeNull()
      }
    })
  })

  describe('generateConfirmationMessage', () => {
    it('should generate price alert confirmation (below)', () => {
      const intent = createMockIntent({
        type: 'create_price_alert',
        entities: {
          tokens: [{ symbol: 'BTC', confidence: 0.95 }],
          priceCondition: { type: 'below', value: 50000, currency: 'usd' },
        },
      })

      const message = generateConfirmationMessage(intent)
      expect(message).toContain('BTC')
      expect(message).toContain('跌破')
      expect(message).toContain('50000')
    })

    it('should generate price alert confirmation (above)', () => {
      const intent = createMockIntent({
        type: 'create_price_alert',
        entities: {
          tokens: [{ symbol: 'ETH', confidence: 0.9 }],
          priceCondition: { type: 'above', value: 4000, currency: 'usd' },
        },
      })

      const message = generateConfirmationMessage(intent)
      expect(message).toContain('ETH')
      expect(message).toContain('涨到')
      expect(message).toContain('4000')
    })

    it('should generate risk monitor confirmation', () => {
      const intent = createMockIntent({
        type: 'create_risk_monitor',
        entities: {
          tokens: [
            { symbol: 'SOL', confidence: 0.9 },
            { symbol: 'AVAX', confidence: 0.85 },
          ],
        },
      })

      const message = generateConfirmationMessage(intent)
      expect(message).toContain('SOL')
      expect(message).toContain('AVAX')
      expect(message).toContain('风险评分')
    })

    it('should generate news brief confirmation for different frequencies', () => {
      const frequencies: Array<['hourly' | 'daily' | 'weekly', string]> = [
        ['hourly', '每小时'],
        ['daily', '每天'],
        ['weekly', '每周'],
      ]

      for (const [frequency, expectedText] of frequencies) {
        const intent = createMockIntent({
          type: 'create_news_brief',
          entities: { frequency },
        })

        const message = generateConfirmationMessage(intent)
        expect(message).toContain(expectedText)
        expect(message).toContain('新闻速报')
      }
    })

    it('should generate delete task confirmation', () => {
      const intent = createMockIntent({
        type: 'delete_task',
        entities: {},
      })

      const message = generateConfirmationMessage(intent)
      expect(message).toContain('删除')
      expect(message).toContain('不可恢复')
    })

    it('should generate pause task confirmation', () => {
      const intent = createMockIntent({
        type: 'pause_task',
        entities: {},
      })

      const message = generateConfirmationMessage(intent)
      expect(message).toContain('暂停')
    })

    it('should generate default confirmation for other intents', () => {
      const intent = createMockIntent({
        type: 'unknown',
        entities: {},
      })

      const message = generateConfirmationMessage(intent)
      expect(message).toContain('确认执行')
    })
  })
})
