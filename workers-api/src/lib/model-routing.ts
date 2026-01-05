/**
 * Model Routing Configuration
 * All models use mistralai/devstral-2512:free (free tier)
 *
 * @partof Week 2 T3: Model Routing/Fallback Matrix
 */

import type { OpenRouterPayload } from './openrouter'

/**
 * AI Model Provider Type
 */
export type ModelProvider = 'mistral' | 'zhipu'

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
 * Primary: mistralai/devstral-2512:free (free tier)
 * Fallback: z-ai/glm-4.5-air:free (free tier)
 *
 * @see OPENROUTER_API for available models: https://openrouter.ai/docs#models
 */
export const MODEL_ROUTING_TABLE: Record<string, ModelConfig> = {
  // ===== Primary Model (Free) =====
  'devstral-chat': {
    model: 'mistralai/devstral-2512:free',
    provider: 'mistral',
    weight: 100,
    costPer1M: {
      prompt: 0,
      completion: 0
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

  // ===== Fallback Model (Free) =====
  'glm-4-5-air': {
    model: 'z-ai/glm-4.5-air:free',
    provider: 'zhipu',
    weight: 50,
    isFallback: true,
    costPer1M: {
      prompt: 0,
      completion: 0
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
 *
 * Primary: devstral-2512:free (Mistral)
 * Fallback: glm-4.5-air:free (Zhipu/智谱)
 */
export const ROUTING_STRATEGIES: Record<
  'quick-chat' | 'deep-research' | 'summarization' | 'code-assist',
  RoutingStrategy
> = {
  'quick-chat': {
    primary: ['devstral-chat'],
    fallback: ['glm-4-5-air'],
    loadBalancing: 'first-available'
  },
  'deep-research': {
    primary: ['devstral-chat'],
    fallback: ['glm-4-5-air'],
    loadBalancing: 'first-available'
  },
  'summarization': {
    primary: ['devstral-chat'],
    fallback: ['glm-4-5-air'],
    loadBalancing: 'first-available'
  },
  'code-assist': {
    primary: ['devstral-chat'],
    fallback: ['glm-4-5-air'],
    loadBalancing: 'first-available'
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
  'devstral-chat': [
    {
      version: '2512-free',
      modelId: 'mistralai/devstral-2512:free',
      deployedAt: '2026-01-01T00:00:00Z',
      status: 'active',
      migrationNotes: 'Primary model - mistralai/devstral-2512:free'
    }
  ],
  'glm-4-5-air': [
    {
      version: '4.5-air-free',
      modelId: 'z-ai/glm-4.5-air:free',
      deployedAt: '2026-01-05T00:00:00Z',
      status: 'active',
      migrationNotes: 'Fallback model - z-ai/glm-4.5-air:free'
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
