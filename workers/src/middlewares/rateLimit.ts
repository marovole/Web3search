/**
 * API速率限制中间件
 * 使用Cloudflare KV存储实现分布式速率限制
 */

interface RateLimitConfig {
  windowMs: number    // 时间窗口（毫秒）
  maxRequests: number // 最大请求数
  keyGenerator?: (c: any) => string // 自定义key生成器
}

interface RateLimitResult {
  allowed: boolean
  remaining: number
  resetTime: number
  retryAfter?: number
}

/**
 * 创建速率限制中间件
 */
export function createRateLimit(config: RateLimitConfig) {
  const {
    windowMs,
    maxRequests,
    keyGenerator = (c) => {
      // 默认使用IP地址作为key
      const clientIP = c.req.header('CF-Connecting-IP') || 
                      c.req.header('X-Forwarded-For') || 
                      'unknown'
      return `rate_limit:${clientIP}`
    }
  } = config

  return async (c: any, next: any) => {
    const key = keyGenerator(c)
    const now = Date.now()
    const windowStart = now - windowMs

    try {
      // 获取当前请求记录
      const existing = await c.env.CACHE.get(key)
      let requests: number[] = existing ? JSON.parse(existing) : []

      // 清理过期的请求记录
      requests = requests.filter((timestamp: number) => timestamp > windowStart)

      // 检查是否超过限制
      if (requests.length >= maxRequests) {
        const oldestRequest = Math.min(...requests)
        const retryAfter = Math.ceil((oldestRequest + windowMs - now) / 1000)

        c.header('X-RateLimit-Limit', maxRequests.toString())
        c.header('X-RateLimit-Remaining', '0')
        c.header('X-RateLimit-Reset', (oldestRequest + windowMs).toString())
        c.header('Retry-After', retryAfter.toString())

        return c.json({
          error: 'Too Many Requests',
          message: `Rate limit exceeded. Try again in ${retryAfter} seconds.`,
          retry_after: retryAfter
        }, 429)
      }

      // 添加当前请求
      requests.push(now)
      
      // 保存到KV（设置过期时间）
      await c.env.CACHE.put(
        key, 
        JSON.stringify(requests), 
        { expirationTtl: Math.ceil(windowMs / 1000) }
      )

      // 设置响应头
      const remaining = maxRequests - requests.length
      c.header('X-RateLimit-Limit', maxRequests.toString())
      c.header('X-RateLimit-Remaining', remaining.toString())
      c.header('X-RateLimit-Reset', (now + windowMs).toString())

      await next()
    } catch (error) {
      // 如果速率限制服务失败，允许请求通过
      console.error('Rate limit error:', error)
      await next()
    }
  }
}

/**
 * 预定义的速率限制配置
 */
export const rateLimitConfigs = {
  // 通用API限制
  general: {
    windowMs: 60 * 1000,    // 1分钟
    maxRequests: 30,         // 每分钟30次
  },
  
  // 聊天API限制（更严格）
  chat: {
    windowMs: 60 * 1000,    // 1分钟
    maxRequests: 20,         // 每分钟20次
    keyGenerator: (c: any) => {
      const clientIP = c.req.header('CF-Connecting-IP') || 'unknown'
      const userAgent = c.req.header('User-Agent') || 'unknown'
      // 使用IP + User-Agent作为key，防止同一IP的多用户共享限制
      // 使用简单的哈希替代Buffer，避免Cloudflare Workers兼容性问题
      const hash = userAgent.split('').reduce((acc: number, char: string) => acc + char.charCodeAt(0), 0)
      return `chat_limit:${clientIP}:${hash.toString(36)}`
    }
  },
  
  // 搜索API限制
  search: {
    windowMs: 60 * 1000,    // 1分钟
    maxRequests: 20,         // 每分钟20次
  },
  
  // 报告生成限制（最严格）
  report: {
    windowMs: 5 * 60 * 1000, // 5分钟
    maxRequests: 3,           // 每5分钟3次
  }
}

/**
 * 便捷的速率限制中间件
 */
export const rateLimit = {
  general: createRateLimit(rateLimitConfigs.general),
  chat: createRateLimit(rateLimitConfigs.chat),
  search: createRateLimit(rateLimitConfigs.search),
  report: createRateLimit(rateLimitConfigs.report),
}