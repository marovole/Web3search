import type {
  OpenRouterConfig,
  OpenRouterRequest,
  OpenRouterResponse,
  OpenRouterStreamChunk,
  OpenRouterError,
} from '../types/openrouter'

/**
 * OpenRouter API 客户端
 * 文档: https://openrouter.ai/docs
 */
export class OpenRouterClient {
  private readonly apiKey: string
  private readonly baseURL: string
  private readonly defaultModel: string
  private readonly timeout: number

  constructor(config: OpenRouterConfig) {
    this.apiKey = config.apiKey
    this.baseURL = config.baseURL ?? 'https://openrouter.ai/api/v1'
    this.defaultModel = config.defaultModel ?? 'deepseek/deepseek-v3.2-speciale'
    this.timeout = config.timeout ?? 30000
  }

  /**
   * 发送非流式聊天请求
   */
  async chat(request: Omit<OpenRouterRequest, 'stream'>): Promise<OpenRouterResponse> {
    const url = `${this.baseURL}/chat/completions`
    const payload: OpenRouterRequest = {
      ...request,
      model: request.model || this.defaultModel,
      stream: false,
    }

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.timeout)

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': 'https://web3search.ai',
          'X-Title': 'Web3 Search',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const error: OpenRouterError = await response.json()
        throw new Error(`OpenRouter API error: ${error.error.message}`)
      }

      return await response.json()
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('OpenRouter request timeout')
      }
      throw error
    }
  }

  /**
   * 发送流式聊天请求
   * 返回 ReadableStream
   */
  async *chatStream(
    request: Omit<OpenRouterRequest, 'stream'>
  ): AsyncGenerator<OpenRouterStreamChunk, void, unknown> {
    const url = `${this.baseURL}/chat/completions`
    const payload: OpenRouterRequest = {
      ...request,
      model: request.model || this.defaultModel,
      stream: true,
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://web3search.ai',
        'X-Title': 'Web3 Search',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const error: OpenRouterError = await response.json()
      throw new Error(`OpenRouter API error: ${error.error.message}`)
    }

    if (!response.body) {
      throw new Error('No response body')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = '' // 缓冲区用于处理跨块的不完整行

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // 将新数据添加到缓冲区
        buffer += decoder.decode(value, { stream: true })

        // 按换行符分割，保留最后一个可能不完整的部分
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留最后一个不完整的行

        for (const line of lines) {
          const trimmedLine = line.trim()
          if (trimmedLine.startsWith('data: ')) {
            const data = trimmedLine.slice(6)
            if (data === '[DONE]') {
              return
            }

            try {
              const parsed: OpenRouterStreamChunk = JSON.parse(data)
              yield parsed
            } catch (e) {
              // 忽略无效的 JSON 片段（通常是由于数据截断）
              // 只在数据看起来应该是完整的时候才记录错误
              if (data.includes('{') && data.includes('}')) {
                console.error('Failed to parse SSE data:', data, e)
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }
}

/**
 * 创建 OpenRouter 客户端实例
 */
export function createOpenRouterClient(apiKey: string): OpenRouterClient {
  return new OpenRouterClient({ apiKey })
}
