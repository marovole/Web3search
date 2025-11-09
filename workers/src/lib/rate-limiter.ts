import type { RateLimitInfo } from '../types/chat'

/**
 * 速率限制器配置
 */
export interface RateLimiterConfig {
  kv: KVNamespace              // Cloudflare KV存储
  limit: number                 // 限制次数
  window: number                // 时间窗口（秒）
}

/**
 * 基于 Cloudflare KV 的速率限制器
 * 注意：KV 是最终一致性，可能有轻微延迟
 */
export class RateLimiter {
  private readonly kv: KVNamespace
  private readonly limit: number
  private readonly window: number

  constructor(config: RateLimiterConfig) {
    this.kv = config.kv
    this.limit = config.limit
    this.window = config.window
  }

  /**
   * 检查并递增计数器
   * @param key 限制键（通常是 IP 地址或用户 ID）
   * @returns 速率限制信息
   */
  async check(key: string): Promise<RateLimitInfo> {
    const now = Math.floor(Date.now() / 1000)
    const windowStart = now - (now % this.window)
    const kvKey = `ratelimit:${key}:${windowStart}`

    try {
      // 获取当前计数
      const currentStr = await this.kv.get(kvKey)
      const current = currentStr ? parseInt(currentStr, 10) : 0

      // 检查是否超限
      if (current >= this.limit) {
        return {
          limit: this.limit,
          remaining: 0,
          reset: windowStart + this.window,
        }
      }

      // 递增计数器
      const newCount = current + 1
      await this.kv.put(kvKey, newCount.toString(), {
        expirationTtl: this.window,
      })

      return {
        limit: this.limit,
        remaining: this.limit - newCount,
        reset: windowStart + this.window,
      }
    } catch (error) {
      console.error('Rate limiter error:', error)
      // 降级处理：出错时允许请求
      return {
        limit: this.limit,
        remaining: this.limit - 1,
        reset: windowStart + this.window,
      }
    }
  }

  /**
   * 重置速率限制
   * @param key 限制键
   */
  async reset(key: string): Promise<void> {
    const now = Math.floor(Date.now() / 1000)
    const windowStart = now - (now % this.window)
    const kvKey = `ratelimit:${key}:${windowStart}`
    await this.kv.delete(kvKey)
  }
}
