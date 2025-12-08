/**
 * Model Routing Configuration
 * Defines model selection, fallback strategies, and version management
 *
 * @partof Week 2 T3: Model Routing/Fallback Matrix
 */

import type { OpenRouterPayload } from './openrouter'

/**
 * AI Model Provider Type
 */
export type ModelProvider = 'qwen' | 'deepseek' | 'anthropic' | 'openai'

/**
 * Model Configuration
 */
export interface ModelConfig {
  model: string
  provider: ModelProvider
  weight: number
  isFallback?: boolean
  costPer1M: {
    prompt: number
    completion: number
  }
  maxTokens: number
  capabilities: {
    reasoning: boolean
    code: boolean
    longContext: boolean
    streaming: boolean
  }
  timeout?: number
  retryAttempts?: number
}

/**
 * Routing Strategy
 */
export interface RoutingStrategy {
  primary: string[]
  fallback: string[]
  loadBalancing: 'round-robin' | 'weighted' | 'first-available'
}

/**
 * Model Routing Table
 *
 * Primary models: High quality, higher cost
 * Fallback models: Lower cost, good for non-critical requests
 *
 * @see OPENROUTER_API for available models: https://openrouter.ai/docs#models
 */
export const MODEL_ROUTING_TABLE: Record<string, ModelConfig> = {
  // ===== Primary Models (High Quality) =====
  'qwen-2.5-72b-instruct': {
    model: 'qwen/qwen-2.5-72b-instruct',
    provider: 'qwen',
    weight: 80,
    costPer1M: {
      prompt: 1.27,
      completion: 3.81
    },
    maxTokens: 32768,
    capabilities: {
      reasoning: true,
      code: true,
      longContext: true,
      streaming: true
    },
    timeout: 30000,
    retryAttempts: 3
  },
  'deepseek-chat': {
    model: 'deepseek/deepseek-v3.2-speciale',
    provider: 'deepseek',
    weight: 80,
    costPer1M: {
      prompt: 0.50,
      completion: 2.18
    },
    maxTokens: 131072,
    capabilities: {
      reasoning: true,
      code: true,
      longContext: true,
      streaming: true
    },
    timeout: 30000,
    retryAttempts: 3
  },

  // ===== Fallback Models (Cost-Optimized) =====
  'qwen-2.5-7b-instruct': {
    model: 'qwen/qwen-2.5-7b-instruct',
    provider: 'qwen',
    weight: 40,
    isFallback: true,
    costPer1M: {
      prompt: 0.16,
      completion: 0.48
    },
    maxTokens: 32768,
    capabilities: {
      reasoning: true,
      code: false,
      longContext: true,
      streaming: true
    },
    timeout: 25000,
    retryAttempts: 3
  },
  'deepseek-coder-6.7b': {
    model: 'deepseek/deepseek-coder-6.7b-base',
    provider: 'deepseek',
    weight: 30,
    isFallback: true,
    costPer1M: {
      prompt: 0.05,
      completion: 0.10
    },
    maxTokens: 32768,
    capabilities: {
      reasoning: false,
      code: true,
      longContext: false,
      streaming: true
    },
    timeout: 25000,
    retryAttempts: 3
  },

  // ===== Premium Models (Rare Use Cases) =====
  'claude-3-5-sonnet': {
    model: 'anthropic/claude-3.5-sonnet',
    provider: 'anthropic',
    weight: 5,
    costPer1M: {
      prompt: 3.0,
      completion: 15.0
    },
    maxTokens: 200000,
    capabilities: {
      reasoning: true,
      code: true,
      longContext: true,
      streaming: true
    },
    timeout: 45000,
    retryAttempts: 3
  },

  // ===== Scoring/Ranking Models =====
  'gpt-3.5-turbo': {
    model: 'openai/gpt-3.5-turbo',
    provider: 'openai',
    weight: 90,
    costPer1M: {
      prompt: 0.5,
      completion: 1.5
    },
    maxTokens: 16385,
    capabilities: {
      reasoning: false,
      code: false,
      longContext: true,
      streaming: true
    },
    timeout: 20000,
    retryAttempts: 3
  },

  // ===== Fallback Models (New) =====
  'gpt-oss-120b': {
    model: 'openai/gpt-oss-120b:exacto',
    provider: 'openai',
    weight: 50,
    isFallback: true,
    costPer1M: {
      prompt: 0.10,
      completion: 0.30
    },
    maxTokens: 32768,
    capabilities: {
      reasoning: true,
      code: true,
      longContext: true,
      streaming: true
    },
    timeout: 30000,
    retryAttempts: 3
  }
}

/**
 * Use Case Based Routing Strategies
 */
export const ROUTING_STRATEGIES: Record<
  'quick-chat' | 'deep-research' | 'summarization' | 'code-assist',
  RoutingStrategy
> = {
  'quick-chat': {
    primary: ['deepseek-chat', 'qwen-2.5-72b-instruct'],
    fallback: ['qwen-2.5-7b-instruct'],
    loadBalancing: 'weighted'
  },
  'deep-research': {
    primary: ['deepseek-chat'],
    fallback: ['gpt-oss-120b'],
    loadBalancing: 'first-available'
  },
  'summarization': {
    primary: ['qwen-2.5-7b-instruct', 'deepseek-chat'],
    fallback: ['gpt-3.5-turbo'],
    loadBalancing: 'weighted'
  },
  'code-assist': {
    primary: ['deepseek-chat', 'qwen-2.5-72b-instruct'],
    fallback: ['deepseek-coder-6.7b', 'qwen-2.5-7b-instruct'],
    loadBalancing: 'weighted'
  }
}

/**
 * Model Version Management
 * Tracks current versions and enables graceful migration
 */
export interface ModelVersion {
  version: string
  modelId: string
  deployedAt: string
  status: 'active' | 'deprecated' | 'ready'
  migrationNotes?: string
}

export const MODEL_VERSIONS: Record<string, ModelVersion[]> = {
  'qwen-2.5-72b-instruct': [
    {
      version: '1.0.0',
      modelId: 'qwen/qwen-2.5-72b-instruct',
      deployedAt: '2025-11-09T00:00:00Z',
      status: 'active'
    }
  ],
  'deepseek-chat': [
    {
      version: '1.0',
      modelId: 'deepseek/deepseek-chat',
      deployedAt: '2025-11-09T00:00:00Z',
      status: 'active'
    }
  ]
}

/**
 * Get model configuration by ID
 */
export function getModelConfig(modelId: string): ModelConfig | null {
  return MODEL_ROUTING_TABLE[modelId] || null
}

/**
 * Select models for a specific use case
 * Returns weighted list of models based on routing strategy
 */
export function selectModels(
  useCase: keyof typeof ROUTING_STRATEGIES,
  includeFallback: boolean = true
): string[] {
  const strategy = ROUTING_STRATEGIES[useCase]
  const models: string[] = [...strategy.primary]

  if (includeFallback) {
    models.push(...strategy.fallback)
  }

  return models
}

/**
 * Cost estimation for a request
 */
export function estimateCost(
  modelId: string,
  promptTokens: number,
  completionTokens: number
): number {
  const config = getModelConfig(modelId)
  if (!config) return 0

  const promptCost = (promptTokens / 1000000) * config.costPer1M.prompt
  const completionCost = (completionTokens / 1000000) * config.costPer1M.completion

  return promptCost + completionCost
}

/**
 * Validate model capabilities against request requirements
 */
export function validateModelCapabilities(
  modelId: string,
  requirements: Partial<ModelConfig['capabilities']>
): { valid: boolean; missing: string[] } {
  const config = getModelConfig(modelId)
  if (!config) return { valid: false, missing: ['model-not-found'] }

  const missing: string[] = []

  for (const [capability, required] of Object.entries(requirements)) {
    if (required && !config.capabilities[capability as keyof typeof config.capabilities]) {
      missing.push(capability)
    }
  }

  return {
    valid: missing.length === 0,
    missing
  }
}

/**
 * Build OpenRouter payload with routing metadata
 */
export function buildRoutedPayload(
  useCase: keyof typeof ROUTING_STRATEGIES,
  messages: any[],
  options?: {
    model?: string
    temperature?: number
    maxTokens?: number
    stream?: boolean
  }
): OpenRouterPayload {
  const selectedModels = selectModels(useCase)
  const primaryModel = options?.model || selectedModels[0]

  return {
    model: MODEL_ROUTING_TABLE[primaryModel]?.model || primaryModel,
    messages,
    temperature: options?.temperature,
    max_tokens: options?.maxTokens,
    stream: options?.stream,
    metadata: {
      useCase,
      routing: {
        models: selectedModels,
        strategy: ROUTING_STRATEGIES[useCase].loadBalancing
      }
    }
  }
}

// Export for tests
export default {
  MODEL_ROUTING_TABLE,
  ROUTING_STRATEGIES,
  MODEL_VERSIONS,
  getModelConfig,
  selectModels,
  estimateCost,
  validateModelCapabilities,
  buildRoutedPayload
}
