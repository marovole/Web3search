/**
 * Quota System Unit Tests
 * Tests for quota limits and enforcement
 */

import { describe, it, expect } from 'vitest'
import {
  QUOTA_LIMITS,
  getQuotaLimit,
  isQuotaExceeded,
} from '../../src/lib/quota-limits'
import type { Plan, QuotaType } from '../../src/lib/quota-limits'

describe('quota-limits', () => {
  describe('QUOTA_LIMITS constants', () => {
    it('should define free plan limits', () => {
      expect(QUOTA_LIMITS.free).toBeDefined()
      expect(QUOTA_LIMITS.free.watchlist).toBe(5)
      expect(QUOTA_LIMITS.free.agents).toBe(2)
      expect(QUOTA_LIMITS.free.daily_alerts).toBe(10)
      expect(QUOTA_LIMITS.free.daily_deep_research).toBe(3)
      expect(QUOTA_LIMITS.free.daily_quick_chat).toBe(50)
      expect(QUOTA_LIMITS.free.monthly_reports).toBe(5)
    })

    it('should define pro plan limits', () => {
      expect(QUOTA_LIMITS.pro).toBeDefined()
      expect(QUOTA_LIMITS.pro.watchlist).toBe(50)
      expect(QUOTA_LIMITS.pro.agents).toBe(20)
      expect(QUOTA_LIMITS.pro.daily_alerts).toBe(100)
      expect(QUOTA_LIMITS.pro.daily_deep_research).toBe(30)
      expect(QUOTA_LIMITS.pro.daily_quick_chat).toBe(500)
      expect(QUOTA_LIMITS.pro.monthly_reports).toBe(50)
    })

    it('should define team plan limits', () => {
      expect(QUOTA_LIMITS.team).toBeDefined()
      expect(QUOTA_LIMITS.team.watchlist).toBe(1000)
      expect(QUOTA_LIMITS.team.agents).toBe(100)
      expect(QUOTA_LIMITS.team.daily_alerts).toBe(500)
      expect(QUOTA_LIMITS.team.daily_deep_research).toBe(100)
      expect(QUOTA_LIMITS.team.daily_quick_chat).toBe(2000)
      expect(QUOTA_LIMITS.team.monthly_reports).toBe(200)
    })

    it('should have progressively higher limits for higher plans', () => {
      const quotaTypes: QuotaType[] = [
        'watchlist',
        'agents',
        'daily_alerts',
        'daily_deep_research',
        'daily_quick_chat',
        'monthly_reports',
      ]

      for (const quotaType of quotaTypes) {
        expect(QUOTA_LIMITS.free[quotaType]).toBeLessThan(QUOTA_LIMITS.pro[quotaType])
        expect(QUOTA_LIMITS.pro[quotaType]).toBeLessThan(QUOTA_LIMITS.team[quotaType])
      }
    })
  })

  describe('getQuotaLimit', () => {
    it('should return correct limit for free plan', () => {
      expect(getQuotaLimit('free', 'watchlist')).toBe(5)
      expect(getQuotaLimit('free', 'agents')).toBe(2)
      expect(getQuotaLimit('free', 'daily_alerts')).toBe(10)
    })

    it('should return correct limit for pro plan', () => {
      expect(getQuotaLimit('pro', 'watchlist')).toBe(50)
      expect(getQuotaLimit('pro', 'agents')).toBe(20)
      expect(getQuotaLimit('pro', 'daily_alerts')).toBe(100)
    })

    it('should return correct limit for team plan', () => {
      expect(getQuotaLimit('team', 'watchlist')).toBe(1000)
      expect(getQuotaLimit('team', 'agents')).toBe(100)
      expect(getQuotaLimit('team', 'daily_alerts')).toBe(500)
    })

    it('should fallback to free plan for unknown plan', () => {
      // TypeScript prevents this normally, but testing runtime behavior
      const unknownPlan = 'enterprise' as Plan
      expect(getQuotaLimit(unknownPlan, 'watchlist')).toBe(5)
    })

    it('should return all quota types for each plan', () => {
      const plans: Plan[] = ['free', 'pro', 'team']
      const quotaTypes: QuotaType[] = [
        'watchlist',
        'agents',
        'daily_alerts',
        'daily_deep_research',
        'daily_quick_chat',
        'monthly_reports',
      ]

      for (const plan of plans) {
        for (const quotaType of quotaTypes) {
          const limit = getQuotaLimit(plan, quotaType)
          expect(typeof limit).toBe('number')
          expect(limit).toBeGreaterThan(0)
        }
      }
    })
  })

  describe('isQuotaExceeded', () => {
    it('should return false when usage is below limit', () => {
      expect(isQuotaExceeded(0, 10)).toBe(false)
      expect(isQuotaExceeded(5, 10)).toBe(false)
      expect(isQuotaExceeded(9, 10)).toBe(false)
    })

    it('should return true when usage equals limit', () => {
      expect(isQuotaExceeded(10, 10)).toBe(true)
      expect(isQuotaExceeded(100, 100)).toBe(true)
      expect(isQuotaExceeded(1, 1)).toBe(true)
    })

    it('should return true when usage exceeds limit', () => {
      expect(isQuotaExceeded(11, 10)).toBe(true)
      expect(isQuotaExceeded(101, 100)).toBe(true)
      expect(isQuotaExceeded(1000, 50)).toBe(true)
    })

    it('should handle edge cases', () => {
      expect(isQuotaExceeded(0, 0)).toBe(true)
      expect(isQuotaExceeded(0, 1)).toBe(false)
    })

    it('should work with real quota values', () => {
      // Free plan watchlist limit is 5
      expect(isQuotaExceeded(4, QUOTA_LIMITS.free.watchlist)).toBe(false)
      expect(isQuotaExceeded(5, QUOTA_LIMITS.free.watchlist)).toBe(true)
      expect(isQuotaExceeded(6, QUOTA_LIMITS.free.watchlist)).toBe(true)

      // Pro plan agents limit is 20
      expect(isQuotaExceeded(19, QUOTA_LIMITS.pro.agents)).toBe(false)
      expect(isQuotaExceeded(20, QUOTA_LIMITS.pro.agents)).toBe(true)
    })
  })

  describe('Type Safety', () => {
    it('Plan type should include all plans', () => {
      const plans: Plan[] = ['free', 'pro', 'team']
      expect(plans).toHaveLength(3)
    })

    it('QuotaType should include all quota types', () => {
      const quotaTypes: QuotaType[] = [
        'watchlist',
        'agents',
        'daily_alerts',
        'daily_deep_research',
        'daily_quick_chat',
        'monthly_reports',
      ]
      expect(quotaTypes).toHaveLength(6)
    })
  })
})
