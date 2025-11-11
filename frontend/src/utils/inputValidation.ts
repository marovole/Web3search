/**
 * 输入验证和安全工具
 * 防止注入攻击和恶意输入
 */

export interface ValidationResult {
  isValid: boolean
  errors: string[]
  sanitized?: string
}

/**
 * 验证和清理文本输入
 */
export function validateTextInput(input: string, options: {
  minLength?: number
  maxLength?: number
  allowHTML?: boolean
  allowMarkdown?: boolean
} = {}): ValidationResult {
  const {
    minLength = 1,
    maxLength = 10000,
    allowHTML = false,
    allowMarkdown = false
  } = options

  const errors: string[] = []

  // 基本检查
  if (!input || typeof input !== 'string') {
    errors.push('输入不能为空')
    return { isValid: false, errors }
  }

  const trimmedInput = input.trim()

  // 长度检查
  if (trimmedInput.length < minLength) {
    errors.push(`输入长度不能少于${minLength}个字符`)
  }

  if (trimmedInput.length > maxLength) {
    errors.push(`输入长度不能超过${maxLength}个字符`)
  }

  // 危险内容检查
  const dangerousPatterns = [
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, // Script tags
    /javascript:/gi, // JavaScript protocol
    /on\w+\s*=/gi, // Event handlers
    /data:text\/html/gi, // Data URLs
  ]

  for (const pattern of dangerousPatterns) {
    if (pattern.test(trimmedInput)) {
      errors.push('输入包含不安全的内容')
      break
    }
  }

  // HTML内容检查
  if (!allowHTML && /<[^>]*>/g.test(trimmedInput)) {
    errors.push('不允许包含HTML标签')
  }

  // 清理输入
  let sanitized = trimmedInput
  
  // 移除潜在的恶意脚本
  sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
  sanitized = sanitized.replace(/javascript:/gi, '')
  sanitized = sanitized.replace(/on\w+\s*=/gi, '')
  
  // 如果不允许HTML，移除所有HTML标签
  if (!allowHTML) {
    sanitized = sanitized.replace(/<[^>]*>/g, '')
  }

  // 限制连续字符防止DoS攻击
  sanitized = sanitized.replace(/(.)\1{50,}/g, '$1'.repeat(10))

  return {
    isValid: errors.length === 0,
    errors,
    sanitized: sanitized.trim()
  }
}

/**
 * 验证聊天查询输入
 */
export function validateChatQuery(query: string): ValidationResult {
  return validateTextInput(query, {
    minLength: 1,
    maxLength: 2000, // 聊天查询限制更短
    allowHTML: false,
    allowMarkdown: true
  })
}

/**
 * 验证报告生成请求
 */
export function validateReportRequest(topic: string, sections: any[]): ValidationResult {
  const errors: string[] = []

  // 验证主题
  const topicValidation = validateTextInput(topic, {
    minLength: 5,
    maxLength: 200,
    allowHTML: false,
    allowMarkdown: false
  })

  if (!topicValidation.isValid) {
    errors.push(...topicValidation.errors.map(e => `主题: ${e}`))
  }

  // 验证章节
  if (!Array.isArray(sections) || sections.length === 0) {
    errors.push('至少需要一个章节')
  } else if (sections.length > 20) {
    errors.push('章节数量不能超过20个')
  } else {
    sections.forEach((section, index) => {
      if (!section.title || typeof section.title !== 'string') {
        errors.push(`章节${index + 1}: 标题不能为空`)
      } else if (section.title.length > 100) {
        errors.push(`章节${index + 1}: 标题长度不能超过100个字符`)
      }

      if (section.description && section.description.length > 500) {
        errors.push(`章节${index + 1}: 描述长度不能超过500个字符`)
      }
    })
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * 验证搜索查询
 */
export function validateSearchQuery(query: string): ValidationResult {
  return validateTextInput(query, {
    minLength: 2,
    maxLength: 100,
    allowHTML: false,
    allowMarkdown: false
  })
}

/**
 * 检测潜在的提示注入攻击
 */
export function detectPromptInjection(input: string): boolean {
  const injectionPatterns = [
    /ignore\s+previous\s+instructions/gi,
    /system\s*:/gi,
    /assistant\s*:/gi,
    /\b(jailbreak|jail\s*break)\b/gi,
    /\b(dan|do\s*anything\s*now)\b/gi,
    /\b(roleplay|role\s*play)\b/gi,
    /\b(hypothetical|hypothetically)\b.*\bif\b.*\byou\b/gi,
    /\bpretend\b.*\byou\b/gi,
    /\bimagine\b.*\byou\b/gi,
  ]

  return injectionPatterns.some(pattern => pattern.test(input))
}

/**
 * 增强的聊天查询验证（包含提示注入检测）
 */
export function validateEnhancedChatQuery(query: string): ValidationResult {
  const basicValidation = validateChatQuery(query)
  
  if (!basicValidation.isValid) {
    return basicValidation
  }

  if (detectPromptInjection(query)) {
    return {
      isValid: false,
      errors: ['查询内容包含不适当的指令'],
      sanitized: basicValidation.sanitized
    }
  }

  return basicValidation
}

/**
 * 速率限制检查（简单内存实现）
 */
class SimpleRateLimiter {
  private requests: Map<string, number[]> = new Map()
  private readonly maxRequests: number
  private readonly windowMs: number

  constructor(maxRequests: number = 10, windowMs: number = 60000) {
    this.maxRequests = maxRequests
    this.windowMs = windowMs
  }

  isAllowed(identifier: string): boolean {
    const now = Date.now()
    const windowStart = now - this.windowMs

    let requests = this.requests.get(identifier) || []
    
    // 清理过期的请求记录
    requests = requests.filter(timestamp => timestamp > windowStart)
    
    // 检查是否超过限制
    if (requests.length >= this.maxRequests) {
      return false
    }

    // 添加当前请求
    requests.push(now)
    this.requests.set(identifier, requests)

    return true
  }

  getRemainingRequests(identifier: string): number {
    const now = Date.now()
    const windowStart = now - this.windowMs
    
    const requests = this.requests.get(identifier) || []
    const validRequests = requests.filter(timestamp => timestamp > windowStart)
    
    return Math.max(0, this.maxRequests - validRequests.length)
  }
}

// 创建全局速率限制器实例
export const rateLimiter = new SimpleRateLimiter(10, 60000) // 每分钟10次请求