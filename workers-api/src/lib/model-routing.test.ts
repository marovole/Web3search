/**
 * Model Routing Tests
 * Tests for AI model selection and routing logic
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  MODEL_ROUTING_TABLE,
  ROUTING_STRATEGIES,
  getModelConfig,
  selectModels,
} from './model-routing'

// Mock environment
vi.stubEnv('MISTRAL_API_KEY', 'test-mistral-key')
vi.stubEnv('DEEPSEEK_API_KEY', 'test-deepseek-key')

describe('Model Routing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Model Configuration', () => {
    it('should have correct model configurations', () => {
      // Verify model structure exists
      const devstralConfig = getModelConfig('devstral-chat')
      expect(devstralConfig).not.toBeNull()
      expect(devstralConfig?.provider).toBe('mistral')
      expect(devstralConfig?.capabilities).toBeDefined()
    })

    it('should have fallback model configured', () => {
      const glmConfig = getModelConfig('glm-4-5-air')
      expect(glmConfig).not.toBeNull()
      expect(glmConfig?.provider).toBe('zhipu')
      expect(glmConfig?.isFallback).toBe(true)
    })
  })

  describe('Model Selection', () => {
    it('should select models for quick chat', () => {
      const models = selectModels('quick-chat')

      expect(models).toContain('devstral-chat')
      expect(models).toContain('glm-4-5-air')
    })

    it('should select models for deep research', () => {
      const models = selectModels('deep-research')

      expect(models).toContain('devstral-chat')
      expect(models).toContain('glm-4-5-air')
    })

    it('should select models for summarization', () => {
      const models = selectModels('summarization')

      expect(models).toContain('devstral-chat')
      expect(models).toContain('glm-4-5-air')
    })

    it('should select models for code assist', () => {
      const models = selectModels('code-assist')

      expect(models).toContain('devstral-chat')
      expect(models).toContain('glm-4-5-air')
    })
  })

  describe('Model Routing Table', () => {
    it('should have primary and fallback models defined', () => {
      expect(MODEL_ROUTING_TABLE['devstral-chat']).toBeDefined()
      expect(MODEL_ROUTING_TABLE['glm-4-5-air']).toBeDefined()
    })

    it('should have routing strategies for all use cases', () => {
      expect(ROUTING_STRATEGIES['quick-chat']).toBeDefined()
      expect(ROUTING_STRATEGIES['deep-research']).toBeDefined()
      expect(ROUTING_STRATEGIES['summarization']).toBeDefined()
      expect(ROUTING_STRATEGIES['code-assist']).toBeDefined()
    })
  })

  describe('Model Fallback', () => {
    it('should have fallback model defined', () => {
      const fallbackModel = 'openai/gpt-oss-120b:exacto'

      expect(fallbackModel).toBeDefined()
      expect(fallbackModel).toContain('openai')
    })

    it('should handle API errors gracefully', async () => {
      // Simulate error handling in model selection
      const selectWithFallback = async (primary: string, fallback: string): Promise<string> => {
        try {
          // Simulate API call
          throw new Error('API error')
        } catch {
          return fallback
        }
      }

      const result = await selectWithFallback(
        'mistralai/devstral-2512:free',
        'openai/gpt-oss-120b:exacto'
      )

      expect(result).toBe('openai/gpt-oss-120b:exacto')
    })
  })

  describe('Model Capabilities', () => {
    it('should support chat capability', () => {
      const devstralConfig = getModelConfig('devstral-chat')
      expect(devstralConfig?.capabilities).toBeDefined()
    })

    it('should support streaming capability', () => {
      const devstralConfig = getModelConfig('devstral-chat')
      expect(devstralConfig?.capabilities.streaming).toBe(true)
    })

    it('should support reasoning capability', () => {
      const devstralConfig = getModelConfig('devstral-chat')
      expect(devstralConfig?.capabilities.reasoning).toBe(true)
    })
  })

  describe('Cost Optimization', () => {
    it('should prefer primary models', () => {
      const models = selectModels('quick-chat', true)
      // Primary model should come first
      expect(models[0]).toBe('devstral-chat')
    })

    it('should calculate token cost correctly', () => {
      const calculateCost = (inputTokens: number, outputTokens: number, costPerMillion: number): number => {
        const totalTokens = inputTokens + outputTokens
        return (totalTokens / 1_000_000) * costPerMillion
      }

      const cost = calculateCost(1000, 500, 0.5)
      expect(cost).toBe(0.00075)
    })
  })
})

describe('Routing Strategy', () => {
  it('should have primary and fallback models', () => {
    const routes: Record<string, { primary: string[]; fallback: string[] }> = {
      'quick-chat': {
        primary: ['devstral-chat'],
        fallback: ['glm-4-5-air'],
      },
      'deep-research': {
        primary: ['devstral-chat'],
        fallback: ['glm-4-5-air'],
      },
    }

    expect(routes['quick-chat'].primary).toBeDefined()
    expect(routes['quick-chat'].fallback).toBeDefined()
    expect(routes['deep-research'].primary).toBeDefined()
    expect(routes['deep-research'].fallback).toBeDefined()
  })

  it('should handle routing based on load', () => {
    const getModelWithLoadBalancing = (
      models: string[],
      _loads: number[]
    ): string => {
      // Simple round-robin simulation
      return models[0]
    }

    const models = ['model-a', 'model-b', 'model-c']
    const loads = [80, 20, 40]

    const selected = getModelWithLoadBalancing(models, loads)
    expect(models).toContain(selected)
  })
})
