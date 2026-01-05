/**
 * Tests for Model Routing Configuration
 * Primary: mistralai/devstral-2512:free
 * Fallback: z-ai/glm-4.5-air:free
 */

import { describe, expect, it } from 'vitest'
import {
  MODEL_ROUTING_TABLE,
  ROUTING_STRATEGIES,
  MODEL_VERSIONS,
  getModelConfig,
  selectModels,
  estimateCost,
  validateModelCapabilities,
  buildRoutedPayload,
} from '../../src/lib/model-routing'

// ============================================
// Model Routing Table Tests
// ============================================

describe('MODEL_ROUTING_TABLE', () => {
  it('contains devstral-chat model', () => {
    expect(MODEL_ROUTING_TABLE).toBeDefined()
    expect(MODEL_ROUTING_TABLE['devstral-chat']).toBeDefined()
  })

  it('contains glm-4-5-air fallback model', () => {
    expect(MODEL_ROUTING_TABLE['glm-4-5-air']).toBeDefined()
  })

  it('all models have required configuration fields', () => {
    Object.entries(MODEL_ROUTING_TABLE).forEach(([modelId, config]) => {
      expect(config.model).toBeDefined()
      expect(config.provider).toBeDefined()
      expect(config.weight).toBeGreaterThan(0)
      expect(config.costPer1M).toBeDefined()
      expect(config.costPer1M.prompt).toBeGreaterThanOrEqual(0)
      expect(config.costPer1M.completion).toBeGreaterThanOrEqual(0)
      expect(config.maxTokens).toBeGreaterThan(0)
      expect(config.capabilities).toBeDefined()
    })
  })

  it('devstral-chat is free model', () => {
    const config = MODEL_ROUTING_TABLE['devstral-chat']

    expect(config.model).toBe('mistralai/devstral-2512:free')
    expect(config.provider).toBe('mistral')
    expect(config.costPer1M.prompt).toBe(0)
    expect(config.costPer1M.completion).toBe(0)
    expect(config.maxTokens).toBe(32768)
  })

  it('glm-4-5-air is free fallback model', () => {
    const config = MODEL_ROUTING_TABLE['glm-4-5-air']

    expect(config.model).toBe('z-ai/glm-4.5-air:free')
    expect(config.provider).toBe('zhipu')
    expect(config.isFallback).toBe(true)
    expect(config.costPer1M.prompt).toBe(0)
    expect(config.costPer1M.completion).toBe(0)
  })

  it('devstral-chat has higher weight than fallback', () => {
    const primary = MODEL_ROUTING_TABLE['devstral-chat']
    const fallback = MODEL_ROUTING_TABLE['glm-4-5-air']

    expect(primary.weight).toBeGreaterThan(fallback.weight)
  })
})

// ============================================
// getModelConfig Tests
// ============================================

describe('getModelConfig', () => {
  it('returns devstral-chat configuration', () => {
    const config = getModelConfig('devstral-chat')

    expect(config).toBeDefined()
    expect(config?.model).toBe('mistralai/devstral-2512:free')
    expect(config?.provider).toBe('mistral')
  })

  it('returns glm-4-5-air configuration', () => {
    const config = getModelConfig('glm-4-5-air')

    expect(config).toBeDefined()
    expect(config?.model).toBe('z-ai/glm-4.5-air:free')
    expect(config?.provider).toBe('zhipu')
  })

  it('returns null for unknown model ID', () => {
    const config = getModelConfig('unknown-model-xyz')
    expect(config).toBeNull()
  })
})

// ============================================
// selectModels Tests
// ============================================

describe('selectModels', () => {
  it('returns devstral-chat and glm-4-5-air for quick-chat', () => {
    const models = selectModels('quick-chat')

    expect(models).toEqual(['devstral-chat', 'glm-4-5-air'])
  })

  it('returns only primary when includeFallback is false', () => {
    const models = selectModels('quick-chat', false)

    expect(models).toEqual(['devstral-chat'])
  })

  it('returns devstral-chat and glm-4-5-air for deep-research', () => {
    const models = selectModels('deep-research')

    expect(models).toEqual(['devstral-chat', 'glm-4-5-air'])
  })

  it('returns devstral-chat and glm-4-5-air for code-assist', () => {
    const models = selectModels('code-assist')

    expect(models).toEqual(['devstral-chat', 'glm-4-5-air'])
  })

  it('returns devstral-chat and glm-4-5-air for summarization', () => {
    const models = selectModels('summarization')

    expect(models).toEqual(['devstral-chat', 'glm-4-5-air'])
  })

  it('maintains order: primary before fallback', () => {
    const models = selectModels('quick-chat')

    expect(models[0]).toBe('devstral-chat')
    expect(models[1]).toBe('glm-4-5-air')
  })
})

// ============================================
// estimateCost Tests
// ============================================

describe('estimateCost', () => {
  it('returns zero cost for devstral-chat (free)', () => {
    const cost = estimateCost('devstral-chat', 1_000_000, 2_000_000)
    expect(cost).toBe(0)
  })

  it('returns zero cost for glm-4-5-air (free)', () => {
    const cost = estimateCost('glm-4-5-air', 1_000_000, 2_000_000)
    expect(cost).toBe(0)
  })

  it('returns zero cost for unknown model', () => {
    const cost = estimateCost('unknown-model', 1000, 1000)
    expect(cost).toBe(0)
  })

  it('handles zero tokens gracefully', () => {
    const cost = estimateCost('devstral-chat', 0, 0)
    expect(cost).toBe(0)
  })
})

// ============================================
// validateModelCapabilities Tests
// ============================================

describe('validateModelCapabilities', () => {
  it('devstral-chat passes all capability requirements', () => {
    const result = validateModelCapabilities('devstral-chat', {
      reasoning: true,
      code: true,
      streaming: true,
      longContext: true,
    })

    expect(result.valid).toBe(true)
    expect(result.missing).toHaveLength(0)
  })

  it('glm-4-5-air passes all capability requirements', () => {
    const result = validateModelCapabilities('glm-4-5-air', {
      reasoning: true,
      code: true,
      streaming: true,
      longContext: true,
    })

    expect(result.valid).toBe(true)
    expect(result.missing).toHaveLength(0)
  })

  it('handles unknown model ID', () => {
    const result = validateModelCapabilities('unknown-model', {
      reasoning: true,
    })

    expect(result.valid).toBe(false)
    expect(result.missing).toEqual(['model-not-found'])
  })

  it('passes validation when no requirements specified', () => {
    const result = validateModelCapabilities('devstral-chat', {})

    expect(result.valid).toBe(true)
    expect(result.missing).toHaveLength(0)
  })
})

// ============================================
// buildRoutedPayload Tests
// ============================================

describe('buildRoutedPayload', () => {
  const messages = [{ role: 'user' as const, content: 'Hello' }]

  it('builds payload with devstral-chat as primary model', () => {
    const payload = buildRoutedPayload('quick-chat', messages)

    expect(payload.model).toBe('mistralai/devstral-2512:free')
    expect(payload.messages).toEqual(messages)
  })

  it('includes routing metadata', () => {
    const payload = buildRoutedPayload('deep-research', messages)

    expect(payload.metadata?.useCase).toBe('deep-research')
    expect(payload.metadata?.routing).toBeDefined()
    expect(payload.metadata?.routing.strategy).toBe('first-available')
    expect(payload.metadata?.routing.models).toEqual(
      selectModels('deep-research')
    )
  })

  it('allows overriding the model', () => {
    const payload = buildRoutedPayload('quick-chat', messages, {
      model: 'glm-4-5-air',
    })

    expect(payload.model).toBe('z-ai/glm-4.5-air:free')
  })

  it('includes optional parameters when provided', () => {
    const payload = buildRoutedPayload('summarization', messages, {
      temperature: 0.7,
      maxTokens: 1000,
      stream: true,
    })

    expect(payload.temperature).toBe(0.7)
    expect(payload.max_tokens).toBe(1000)
    expect(payload.stream).toBe(true)
  })

  it('handles missing optional parameters', () => {
    const payload = buildRoutedPayload('code-assist', messages)

    expect(payload.temperature).toBeUndefined()
    expect(payload.max_tokens).toBeUndefined()
    expect(payload.stream).toBeUndefined()
  })
})

// ============================================
// ROUTING_STRATEGIES Tests
// ============================================

describe('ROUTING_STRATEGIES', () => {
  it('contains all expected use cases', () => {
    expect(ROUTING_STRATEGIES).toHaveProperty('quick-chat')
    expect(ROUTING_STRATEGIES).toHaveProperty('deep-research')
    expect(ROUTING_STRATEGIES).toHaveProperty('summarization')
    expect(ROUTING_STRATEGIES).toHaveProperty('code-assist')
  })

  it('each strategy has primary devstral-chat', () => {
    Object.values(ROUTING_STRATEGIES).forEach((strategy) => {
      expect(strategy.primary).toEqual(['devstral-chat'])
    })
  })

  it('each strategy has fallback glm-4-5-air', () => {
    Object.values(ROUTING_STRATEGIES).forEach((strategy) => {
      expect(strategy.fallback).toEqual(['glm-4-5-air'])
    })
  })

  it('all referenced models exist in routing table', () => {
    Object.entries(ROUTING_STRATEGIES).forEach(([useCase, strategy]) => {
      const allModels = [...strategy.primary, ...strategy.fallback]

      allModels.forEach((modelId) => {
        expect(MODEL_ROUTING_TABLE[modelId]).toBeDefined()
      })
    })
  })
})

// ============================================
// MODEL_VERSIONS Tests
// ============================================

describe('MODEL_VERSIONS', () => {
  it('tracks versions for devstral-chat', () => {
    expect(MODEL_VERSIONS).toBeDefined()
    expect(MODEL_VERSIONS['devstral-chat']).toBeDefined()
  })

  it('tracks versions for glm-4-5-air', () => {
    expect(MODEL_VERSIONS['glm-4-5-air']).toBeDefined()
  })

  it('devstral-chat has active version', () => {
    const versions = MODEL_VERSIONS['devstral-chat']
    const activeVersion = versions.find((v) => v.status === 'active')

    expect(activeVersion).toBeDefined()
    expect(activeVersion?.modelId).toBe('mistralai/devstral-2512:free')
  })

  it('glm-4-5-air has active version', () => {
    const versions = MODEL_VERSIONS['glm-4-5-air']
    const activeVersion = versions.find((v) => v.status === 'active')

    expect(activeVersion).toBeDefined()
    expect(activeVersion?.modelId).toBe('z-ai/glm-4.5-air:free')
  })
})
