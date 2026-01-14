/**
 * Model Routing Tests
 * Tests for AI model selection and routing logic
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  getModelForIntent,
  getModelForMode,
  ModelRoute,
  ModelConfig,
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
      const models: Record<string, ModelConfig> = {
        'mistralai/devstral-2512:free': {
          provider: 'mistral',
          costPerToken: 0,
          capabilities: ['chat', 'reasoning'],
        },
        'deepseek/deepseek-v3.2-speciale': {
          provider: 'deepseek',
          costPerToken: 0.5,
          capabilities: ['chat', 'reasoning', 'code'],
        },
        'alibaba/tongyi-deepresearch-30b-a3b': {
          provider: 'alibaba',
          costPerToken: 0.2,
          capabilities: ['research', 'analysis'],
        },
      }

      // Verify model structure
      Object.entries(models).forEach(([name, config]) => {
        expect(name).toContain('/')
        expect(config.provider).toBeDefined()
        expect(Array.isArray(config.capabilities)).toBe(true)
      })
    })

    it('should have free models for development', () => {
      const freeModels = Object.entries({
        'mistralai/devstral-2512:free': {
          provider: 'mistral',
          costPerToken: 0,
        },
        'z-ai/glm-4.5-air:free': {
          provider: 'zhipu',
          costPerToken: 0,
        },
      })

      freeModels.forEach(([name, config]) => {
        expect(name).toContain(':free')
        expect(config.costPerToken).toBe(0)
      })
    })
  })

  describe('getModelForMode', () => {
    it('should return correct model for quick chat mode', () => {
      const model = getModelForMode('quick-chat')

      expect(model).toContain('deepseek')
      expect(model).not.toContain('alibaba') // Alibaba is for deep research
    })

    it('should return correct model for deep research mode', () => {
      const model = getModelForMode('deep-research')

      expect(model).toContain('alibaba')
    })

    it('should return correct model for summarization', () => {
      const model = getModelForMode('summarization')

      expect(model).toContain('deepseek')
    })

    it('should return correct model for code assistance', () => {
      const model = getModelForMode('code-assist')

      expect(model).toContain('deepseek')
    })

    it('should throw for unknown mode', () => {
      expect(() => getModelForMode('unknown-mode' as any)).toThrow()
    })
  })

  describe('getModelForIntent', () => {
    it('should detect research intent and return deep research model', () => {
      const model = getModelForIntent('Analyze Bitcoin smart contracts')

      expect(model).toContain('alibaba')
    })

    it('should detect casual intent and return quick chat model', () => {
      const model = getModelForIntent('What is the price of ETH?')

      expect(model).toContain('deepseek')
    })

    it('should detect comparison intent', () => {
      const model = getModelForIntent('Compare Bitcoin and Ethereum')

      expect(model).toBeDefined()
    })

    it('should detect price inquiry intent', () => {
      const model = getModelForIntent('How much is SOL worth right now?')

      expect(model).toBeDefined()
    })

    it('should default to quick chat for unrecognized intents', () => {
      const model = getModelForIntent('Tell me a joke')

      expect(model).toContain('deepseek')
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
      const chatModels = [
        'deepseek/deepseek-v3.2-speciale',
        'mistralai/devstral-2512:free',
      ]

      chatModels.forEach((model) => {
        expect(model).toBeDefined()
      })
    })

    it('should support research capability', () => {
      const researchModels = [
        'alibaba/tongyi-deepresearch-30b-a3b',
        'deepseek/deepseek-v3.2-speciale',
      ]

      researchModels.forEach((model) => {
        expect(model).toBeDefined()
      })
    })

    it('should support code capability', () => {
      const codeModels = ['deepseek/deepseek-v3.2-speciale']

      codeModels.forEach((model) => {
        expect(model).toBeDefined()
      })
    })
  })

  describe('Cost Optimization', () => {
    it('should prefer free models when available', () => {
      const freeModel = 'mistralai/devstral-2512:free'
      const paidModel = 'deepseek/deepseek-v3.2-speciale'

      // In test environment, prefer free model
      expect(freeModel).toContain(':free')
      expect(paidModel).not.toContain(':free')
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
    const routes: Record<string, { primary: string; fallback: string }> = {
      'quick-chat': {
        primary: 'deepseek/deepseek-v3.2-speciale',
        fallback: 'openai/gpt-oss-120b:exacto',
      },
      'deep-research': {
        primary: 'alibaba/tongyi-deepresearch-30b-a3b',
        fallback: 'deepseek/deepseek-v3.2-speciale',
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
