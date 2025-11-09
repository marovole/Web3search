/**
 * OpenRouter API 类型定义
 * 文档: https://openrouter.ai/docs
 */

/**
 * OpenRouter 模型配置
 */
export interface OpenRouterModel {
  id: string
  name: string
  pricing: {
    prompt: number    // 每 1M tokens 价格
    completion: number
  }
}

/**
 * OpenRouter 聊天消息
 */
export interface OpenRouterMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

/**
 * OpenRouter API 请求参数
 */
export interface OpenRouterRequest {
  model: string
  messages: OpenRouterMessage[]
  temperature?: number
  max_tokens?: number
  top_p?: number
  frequency_penalty?: number
  presence_penalty?: number
  stream?: boolean
}

/**
 * OpenRouter API 响应（非流式）
 */
export interface OpenRouterResponse {
  id: string
  model: string
  created: number
  choices: Array<{
    index: number
    message: OpenRouterMessage
    finish_reason: string
  }>
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

/**
 * OpenRouter 流式响应 chunk
 */
export interface OpenRouterStreamChunk {
  id: string
  model: string
  created: number
  choices: Array<{
    index: number
    delta: {
      role?: string
      content?: string
    }
    finish_reason: string | null
  }>
}

/**
 * OpenRouter 错误响应
 */
export interface OpenRouterError {
  error: {
    message: string
    type: string
    code: string | number
  }
}

/**
 * OpenRouter 客户端配置
 */
export interface OpenRouterConfig {
  apiKey: string
  baseURL?: string
  defaultModel?: string
  timeout?: number // 毫秒
}
