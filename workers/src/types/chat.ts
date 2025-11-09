/**
 * 聊天 API 类型定义
 */

/**
 * 聊天请求参数
 */
export interface ChatRequest {
  query: string                    // 用户查询
  conversation_id?: string         // 对话 ID（可选）
  model?: string                   // AI 模型（可选）
  stream?: boolean                 // 是否流式响应（默认 true）
  max_tokens?: number              // 最大 tokens 数
  temperature?: number             // 温度参数 (0-2)
}

/**
 * 聊天响应（非流式）
 */
export interface ChatResponse {
  conversation_id: string          // 对话 ID
  message: string                  // AI 回复内容
  model: string                    // 使用的模型
  usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  created_at: string              // ISO 8601 时间戳
}

/**
 * 聊天流式响应 chunk
 */
export interface ChatStreamChunk {
  conversation_id: string
  content: string                 // 增量内容
  finish_reason: string | null   // 完成原因（null 表示未完成）
}

/**
 * 对话历史记录
 */
export interface Conversation {
  id: string
  user_id?: string
  created_at: string
  updated_at: string
}

/**
 * 消息记录
 */
export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  model?: string
  tokens?: number
  created_at: string
}

/**
 * 速率限制信息
 */
export interface RateLimitInfo {
  limit: number                   // 限制次数
  remaining: number               // 剩余次数
  reset: number                   // 重置时间戳（秒）
}
