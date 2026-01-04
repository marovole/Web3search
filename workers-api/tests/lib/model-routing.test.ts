/**
 * Tests for Model Routing Configuration
 * Validates routing strategies, cost estimation, and capability validation
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
  type ModelConfig,
} from '../../src/lib/model-routing'

// ============================================
// Model Routing Table Tests
// ============================================

describe('MODEL_ROUTING_TABLE', () => {
  it('contains expected model configurations', () => {
    expect(MODEL_ROUTING_TABLE).toBeDefined()
    expect(Object.keys(MODEL_ROUTING_TABLE).length).toBeGreaterThan(0)
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

  it('primary models have higher weights than fallback models', () => {
    const primaryModel = MODEL_ROUTING_TABLE['devstral-chat']
    const fallbackModel = MODEL_ROUTING_TABLE['gpt-oss-120b']

    expect(primaryModel.weight).toBeGreaterThan(fallbackModel.weight)
  })

  it('fallback models are marked with isFallback flag', () => {
    const fallbackModel = MODEL_ROUTING_TABLE['gpt-oss-120b']
    expect(fallbackModel.isFallback).toBe(true)

    const primaryModel = MODEL_ROUTING_TABLE['devstral-chat']
    expect(primaryModel.isFallback).toBeUndefined()
  })
})

// ============================================
// getModelConfig Tests
// ============================================

describe('getModelConfig', () => {
  it('returns model configuration for valid model ID', () => {
    const config = getModelConfig('qwen-2.5-72b-instruct')

    expect(config).toBeDefined()
    expect(config?.model).toBe('qwen/qwen-2.5-72b-instruct')
    expect(config?.provider).toBe('qwen')
    expect(config?.weight).toBe(80)
    expect(config?.maxTokens).toBe(32768)
  })

  it('returns correct capabilities for qwen-2.5-72b-instruct', () => {
    const config = getModelConfig('qwen-2.5-72b-instruct')

    expect(config?.capabilities).toEqual({
      reasoning: true,
      code: true,
      longContext: true,
      streaming: true,
    })
  })

  it('returns correct capabilities for deepseek-chat', () => {
    const config = getModelConfig('deepseek-chat')

    expect(config?.capabilities).toEqual({
      reasoning: true,
      code: true,
      longContext: true,
      streaming: true,
    })
  })

  it('returns null for unknown model ID', () => {
    const config = getModelConfig('unknown-model-xyz')
    expect(config).toBeNull()
  })

  it('returns different configurations for different models', () => {
    const qwen = getModelConfig('qwen-2.5-72b-instruct')
    const deepseek = getModelConfig('deepseek-chat')

    expect(qwen?.provider).toBe('qwen')
    expect(deepseek?.provider).toBe('deepseek')
    expect(qwen?.model).not.toBe(deepseek?.model)
  })
})

// ============================================
// selectModels Tests
// ============================================

describe('selectModels', () => {
  it('returns primary and fallback models by default for quick-chat', () => {
    const models = selectModels('quick-chat')

    expect(models).toEqual([
      ...ROUTING_STRATEGIES['quick-chat'].primary,
      ...ROUTING_STRATEGIES['quick-chat'].fallback,
    ])
  })

  it('returns only primary models when includeFallback is false', () => {
    const models = selectModels('quick-chat', false)

    expect(models).toEqual(ROUTING_STRATEGIES['quick-chat'].primary)
    expect(models).not.toContain('qwen-2.5-7b-instruct') // fallback
  })

  it('returns correct models for deep-research use case', () => {
    const models = selectModels('deep-research')

    expect(models).toContain('claude-3-5-sonnet')
    expect(models).toContain('qwen-2.5-72b-instruct') // fallback
  })

  it('returns correct models for code-assist use case', () => {
    const models = selectModels('code-assist')

    expect(models).toContain('deepseek-chat')
    expect(models).toContain('qwen-2.5-72b-instruct')
  })

  it('returns correct models for summarization use case', () => {
    const models = selectModels('summarization')

    expect(models).toContain('qwen-2.5-7b-instruct')
    expect(models).toContain('deepseek-chat')
  })

  it('maintains order: primary models before fallback models', () => {
    const models = selectModels('quick-chat')
    const strategy = ROUTING_STRATEGIES['quick-chat']

    const primaryCount = strategy.primary.length
    expect(models.slice(0, primaryCount)).toEqual(strategy.primary)
    expect(models.slice(primaryCount)).toEqual(strategy.fallback)
  })
})

// ============================================
// estimateCost Tests
// ============================================

describe('estimateCost', () => {
  it('calculates correct cost for qwen-2.5-72b-instruct', () => {
    const modelId = 'qwen-2.5-72b-instruct'
    const promptTokens = 1_000_000
    const completionTokens = 2_000_000

    const cost = estimateCost(modelId, promptTokens, completionTokens)

    // 1M prompt * $1.27 + 2M completion * $3.81 = $1.27 + $7.62 = $8.89
    expect(cost).toBeCloseTo(8.89, 2)
  })

  it('calculates correct cost for deepseek-chat', () => {
    const modelId = 'deepseek-chat'
    const promptTokens = 500_000
    const completionTokens = 1_000_000

    const cost = estimateCost(modelId, promptTokens, completionTokens)

    // 0.5M * $0.14 + 1M * $0.28 = $0.07 + $0.28 = $0.35
    expect(cost).toBeCloseTo(0.35, 2)
  })

  it('returns zero cost for unknown model', () => {
    const cost = estimateCost('unknown-model', 1000, 1000)
    expect(cost).toBe(0)
  })

  it('handles zero tokens gracefully', () => {
    const cost = estimateCost('qwen-2.5-72b-instruct', 0, 0)
    expect(cost).toBe(0)
  })

  it('calculates cost proportionally for small token counts', () => {
    const modelId = 'qwen-2.5-72b-instruct'
    const config = MODEL_ROUTING_TABLE[modelId]

    const promptTokens = 1000
    const completionTokens = 2000

    const cost = estimateCost(modelId, promptTokens, completionTokens)

    const expectedCost =
      (promptTokens / 1_000_000) * config.costPer1M.prompt +
      (completionTokens / 1_000_000) * config.costPer1M.completion

    expect(cost).toBeCloseTo(expectedCost, 6)
  })

  it('premium models cost more than standard models', () => {
    const claudeCost = estimateCost('claude-3-5-sonnet', 100_000, 100_000)
    const qwenCost = estimateCost('qwen-2.5-72b-instruct', 100_000, 100_000)

    expect(claudeCost).toBeGreaterThan(qwenCost)
  })
})

// ============================================
// validateModelCapabilities Tests
// ============================================

describe('validateModelCapabilities', () => {
  it('validates model meets all requirements', () => {
    const result = validateModelCapabilities('deepseek-chat', {
      reasoning: true,
      code: true,
      streaming: true,
    })

    expect(result.valid).toBe(true)
    expect(result.missing).toHaveLength(0)
  })

  it('detects missing capabilities', () => {
    const result = validateModelCapabilities('qwen-2.5-7b-instruct', {
      reasoning: true,
      code: true, // This model doesn't support code
    })

    expect(result.valid).toBe(false)
    expect(result.missing).toContain('code')
  })

  it('validates multiple missing capabilities', () => {
    const result = validateModelCapabilities('gpt-3.5-turbo', {
      reasoning: true, // Missing
      code: true, // Missing
    })

    expect(result.valid).toBe(false)
    expect(result.missing).toContain('reasoning')
    expect(result.missing).toContain('code')
  })

  it('handles unknown model ID', () => {
    const result = validateModelCapabilities('unknown-model', {
      reasoning: true,
    })

    expect(result.valid).toBe(false)
    expect(result.missing).toEqual(['model-not-found'])
  })

  it('passes validation when no requirements specified', () => {
    const result = validateModelCapabilities('qwen-2.5-72b-instruct', {})

    expect(result.valid).toBe(true)
    expect(result.missing).toHaveLength(0)
  })

  it('validates only specified requirements', () => {
    const result = validateModelCapabilities('qwen-2.5-7b-instruct', {
      reasoning: true, // Has this
      streaming: true, // Has this
      // NOT checking code capability
    })

    expect(result.valid).toBe(true)
    expect(result.missing).toHaveLength(0)
  })

  it('handles false requirements (not required)', () => {
    const result = validateModelCapabilities('qwen-2.5-7b-instruct', {
      code: false, // Explicitly not required
    })

    expect(result.valid).toBe(true)
    expect(result.missing).toHaveLength(0)
  })
})

// ============================================
// buildRoutedPayload Tests
// ============================================

describe('buildRoutedPayload', () => {
  const messages = [{ role: 'user' as const, content: 'Hello' }]

  it('builds payload with default primary model', () => {
    const payload = buildRoutedPayload('quick-chat', messages)

    const primaryModelId = ROUTING_STRATEGIES['quick-chat'].primary[0]
    const expectedModel = MODEL_ROUTING_TABLE[primaryModelId].model

    expect(payload.model).toBe(expectedModel)
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
      model: 'deepseek-chat',
    })

    expect(payload.model).toBe('deepseek/deepseek-chat')
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

  it('includes all selected models in routing metadata', () => {
    const payload = buildRoutedPayload('quick-chat', messages)

    const expectedModels = selectModels('quick-chat')
    expect(payload.metadata?.routing.models).toEqual(expectedModels)
  })

  it('uses correct load balancing strategy for each use case', () => {
    const quickChatPayload = buildRoutedPayload('quick-chat', messages)
    expect(quickChatPayload.metadata?.routing.strategy).toBe('weighted')

    const deepResearchPayload = buildRoutedPayload('deep-research', messages)
    expect(deepResearchPayload.metadata?.routing.strategy).toBe(
      'first-available'
    )
  })

  it('handles model override with custom model string', () => {
    const payload = buildRoutedPayload('quick-chat', messages, {
      model: 'custom/model-name',
    })

    // Should use the custom model string as-is when not in registry
    expect(payload.model).toBe('custom/model-name')
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

  it('each strategy has required fields', () => {
    Object.entries(ROUTING_STRATEGIES).forEach(([useCase, strategy]) => {
      expect(strategy.primary).toBeDefined()
      expect(strategy.fallback).toBeDefined()
      expect(strategy.loadBalancing).toBeDefined()
      expect(strategy.primary.length).toBeGreaterThan(0)
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
  it('tracks versions for deployed models', () => {
    expect(MODEL_VERSIONS).toBeDefined()
    expect(Object.keys(MODEL_VERSIONS).length).toBeGreaterThan(0)
  })

  it('each version has required fields', () => {
    Object.entries(MODEL_VERSIONS).forEach(([modelId, versions]) => {
      versions.forEach((version) => {
        expect(version.version).toBeDefined()
        expect(version.modelId).toBeDefined()
        expect(version.deployedAt).toBeDefined()
        expect(version.status).toBeDefined()
        expect(['active', 'deprecated', 'ready']).toContain(version.status)
      })
    })
  })
})
