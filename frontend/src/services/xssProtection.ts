/**
 * XSS和注入防护服务
 * 提供输入验证、输出编码和内容清理功能
 */

import DOMPurify from 'dompurify'

interface XSSRule {
  id: string
  name: string
  description: string
  enabled: boolean
  patterns: RegExp[]
  severity: 'low' | 'medium' | 'high' | 'critical'
  action: 'block' | 'warn' | 'sanitize'
}

interface SanitizationConfig {
  allowedTags: string[]
  allowedAttributes: string[]
  allowedSchemes: string[]
  stripComments: boolean
  stripEmptyElements: boolean
}

interface InputValidation {
  field: string
  value: string
  type: 'string' | 'email' | 'url' | 'number' | 'html' | 'css' | 'js'
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  customValidator?: (value: string) => boolean
}

interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  sanitized?: string
}

/**
 * XSS防护管理器
 */
export class XSSProtectionManager {
  private static instance: XSSProtectionManager
  private rules: Map<string, XSSRule> = new Map()
  private config: SanitizationConfig
  private isInitialized = false
  private blockedAttempts: number = 0

  private readonly DEFAULT_CONFIG: SanitizationConfig = {
    allowedTags: [
      'p', 'br', 'strong', 'em', 'u', 'i', 'b', 'a', 'ul', 'ol', 'li',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre',
      'div', 'span', 'img', 'hr', 'table', 'tr', 'td', 'th', 'thead', 'tbody'
    ],
    allowedAttributes: [
      'href', 'title', 'alt', 'src', 'class', 'id', 'style', 'target',
      'rel', 'data-*'
    ],
    allowedSchemes: ['http', 'https', 'mailto', 'tel', 'data'],
    stripComments: true,
    stripEmptyElements: true
  }

  private readonly XSS_PATTERNS = [
    // Script标签
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    // JavaScript事件处理器
    /on\w+\s*=/gi,
    // JavaScript协议
    /javascript:/gi,
    // VBScript协议
    /vbscript:/gi,
    // Data协议（可能的XSS）
    /data:(?!image\/)/gi,
    // CSS表达式
    /expression\s*\(/gi,
    // @import
    /@import/gi,
    // 基本的XSS载荷
    /<iframe[^>]*>/gi,
    /<object[^>]*>/gi,
    /<embed[^>]*>/gi,
    /<link[^>]*>/gi,
    /<meta[^>]*>/gi,
    // 编码的XSS
    /%3cscript/gi,
    /%3e/gi,
    // Unicode编码
    /\\u003cscript/gi,
    // HTML实体编码
    /&lt;script/gi,
    /&gt;/gi,
    // 混淆的XSS
    /<\s*script[^>]*>/gi,
    /eval\s*\(/gi,
    /setTimeout\s*\(/gi,
    /setInterval\s*\(/gi,
    /Function\s*\(/gi
  ]

  private constructor() {
    this.config = { ...this.DEFAULT_CONFIG }
    this.initializeDefaultRules()
    this.configureDOMPurify()
  }

  /**
   * 获取XSSProtectionManager实例（单例模式）
   */
  static getInstance(): XSSProtectionManager {
    if (!XSSProtectionManager.instance) {
      XSSProtectionManager.instance = new XSSProtectionManager()
    }
    return XSSProtectionManager.instance
  }

  /**
   * 初始化XSS防护管理器
   */
  async initialize(config?: Partial<SanitizationConfig>): Promise<void> {
    if (this.isInitialized) {
      console.warn('XSS防护管理器已经初始化')
      return
    }

    // 合并配置
    this.config = { ...this.config, ...config }

    // 重新配置DOMPurify
    this.configureDOMPurify()

    // 设置全局XSS监听器
    this.setupGlobalListeners()

    this.isInitialized = true
    console.log('🛡️ XSS防护管理器已初始化')
  }

  /**
   * 初始化默认XSS规则
   */
  private initializeDefaultRules(): void {
    // Script标签检测
    this.addRule({
      id: 'script-tags',
      name: 'Script标签检测',
      description: '检测和阻止script标签',
      enabled: true,
      patterns: [/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi],
      severity: 'critical',
      action: 'block'
    })

    // 事件处理器检测
    this.addRule({
      id: 'event-handlers',
      name: '事件处理器检测',
      description: '检测JavaScript事件处理器',
      enabled: true,
      patterns: [/on\w+\s*=/gi],
      severity: 'high',
      action: 'block'
    })

    // JavaScript协议检测
    this.addRule({
      id: 'javascript-protocol',
      name: 'JavaScript协议检测',
      description: '检测javascript:协议',
      enabled: true,
      patterns: [/javascript:/gi],
      severity: 'high',
      action: 'block'
    })

    // CSS表达式检测
    this.addRule({
      id: 'css-expressions',
      name: 'CSS表达式检测',
      description: '检测危险的CSS表达式',
      enabled: true,
      patterns: [/expression\s*\(/gi],
      severity: 'medium',
      action: 'block'
    })

    // Iframe检测
    this.addRule({
      id: 'iframe-detection',
      name: 'Iframe标签检测',
      description: '检测iframe标签',
      enabled: true,
      patterns: [/<iframe[^>]*>/gi],
      severity: 'medium',
      action: 'warn'
    })
  }

  /**
   * 配置DOMPurify
   */
  private configureDOMPurify(): void {
    if (typeof DOMPurify !== 'undefined') {
      DOMPurify.addHook('uponSanitizeAttribute', (node, data) => {
        // 自定义属性清理逻辑
        if (data.attrName.startsWith('on')) {
          node.removeAttribute(data.attrName)
        }
      })

      DOMPurify.addHook('uponSanitizeElement', (node, data) => {
        // 自定义元素清理逻辑
        if (data.tagName === 'script') {
          node.parentNode?.removeChild(node)
        }
      })
    }
  }

  /**
   * 设置全局监听器
   */
  private setupGlobalListeners(): void {
    // 监听DOM变化
    if (typeof MutationObserver !== 'undefined') {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList') {
            mutation.addedNodes.forEach((node) => {
              if (node.nodeType === Node.ELEMENT_NODE) {
                this.scanElement(node as Element)
              }
            })
          }
        })
      })

      observer.observe(document.body, {
        childList: true,
        subtree: true
      })
    }

    // 监听动态脚本创建
    const originalCreateElement = document.createElement
    document.createElement = function(tagName: string) {
      const element = originalCreateElement.call(this, tagName)

      if (tagName.toLowerCase() === 'script') {
        // 监听script标签的内容设置
        Object.defineProperty(element, 'innerHTML', {
          set: (value) => {
            if (XSSProtectionManager.getInstance().containsXSS(value)) {
              console.warn('🚫 检测到潜在的XSS攻击，已阻止')
              return
            }
            element.setAttribute('innerHTML', value)
          }
        })
      }

      return element
    }
  }

  /**
   * 扫描元素中的XSS
   */
  private scanElement(element: Element): void {
    // 检查元素属性
    Array.from(element.attributes).forEach(attr => {
      if (this.containsXSS(attr.value)) {
        console.warn(`🚫 在属性 ${attr.name} 中检测到XSS:`, attr.value)
        this.handleXSSDetection(attr.value, 'attribute', attr.name)
      }
    })

    // 检查文本内容
    if (element.textContent && this.containsXSS(element.textContent)) {
      console.warn('🚫 在文本内容中检测到XSS:', element.textContent)
      this.handleXSSDetection(element.textContent, 'text')
    }
  }

  /**
   * 处理XSS检测
   */
  private handleXSSDetection(content: string, source: string, detail?: string): void {
    this.blockedAttempts++

    // 记录到监控系统
    console.warn('XSS检测详情:', {
      content: content.substring(0, 100),
      source,
      detail,
      timestamp: Date.now(),
      blockedAttempts: this.blockedAttempts
    })

    // 可以在这里添加更多的处理逻辑，如发送报告等
  }

  /**
   * 添加XSS规则
   */
  addRule(rule: XSSRule): string {
    const id = rule.id || this.generateId()
    const fullRule: XSSRule = {
      ...rule,
      id
    }

    this.rules.set(id, fullRule)
    console.log(`XSS规则已添加: ${rule.name}`)
    return id
  }

  /**
   * 移除XSS规则
   */
  removeRule(ruleId: string): boolean {
    return this.rules.delete(ruleId)
  }

  /**
   * 检查内容是否包含XSS
   */
  containsXSS(content: string): boolean {
    // 使用内置模式检查
    for (const pattern of this.XSS_PATTERNS) {
      if (pattern.test(content)) {
        return true
      }
    }

    // 使用自定义规则检查
    for (const rule of this.rules.values()) {
      if (!rule.enabled) continue

      for (const pattern of rule.patterns) {
        if (pattern.test(content)) {
          return true
        }
      }
    }

    return false
  }

  /**
   * 清理HTML内容
   */
  sanitizeHTML(dirty: string, config?: Partial<SanitizationConfig>): string {
    const finalConfig = { ...this.config, ...config }

    if (typeof DOMPurify !== 'undefined') {
      return DOMPurify.sanitize(dirty, {
        ALLOWED_TAGS: finalConfig.allowedTags,
        ALLOWED_ATTR: finalConfig.allowedAttributes,
        KEEP_CONTENT: true,
        RETURN_DOM: false,
        RETURN_DOM_FRAGMENT: false,
        SANITIZE_DOM: true,
        WHOLE_DOCUMENT: false
      })
    }

    // 如果DOMPurify不可用，使用基本的清理
    return this.basicSanitize(dirty)
  }

  /**
   * 基本的HTML清理（备用方案）
   */
  private basicSanitize(dirty: string): string {
    return dirty
      // 移除script标签
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      // 移除事件处理器
      .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '')
      // 移除javascript:协议
      .replace(/javascript:/gi, '')
      // 移除危险标签
      .replace(/<(iframe|object|embed|link|meta)[^>]*>/gi, '')
      // 基本HTML编码
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
  }

  /**
   * 验证输入
   */
  validateInput(input: InputValidation): ValidationResult {
    const errors: string[] = []
    const warnings: string[] = []

    // 检查必填
    if (input.required && !input.value.trim()) {
      errors.push(`${input.field} 是必填项`)
    }

    // 如果值为空且不是必填，跳过其他验证
    if (!input.value.trim() && !input.required) {
      return { valid: true, errors, warnings }
    }

    // XSS检查
    if (this.containsXSS(input.value)) {
      errors.push(`${input.field} 包含潜在的安全风险`)
    }

    // 长度检查
    if (input.minLength && input.value.length < input.minLength) {
      errors.push(`${input.field} 长度不能少于 ${input.minLength} 个字符`)
    }

    if (input.maxLength && input.value.length > input.maxLength) {
      errors.push(`${input.field} 长度不能超过 ${input.maxLength} 个字符`)
    }

    // 类型特定验证
    switch (input.type) {
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(input.value)) {
          errors.push(`${input.field} 必须是有效的邮箱地址`)
        }
        break

      case 'url':
        try {
          new URL(input.value)
        } catch {
          errors.push(`${input.field} 必须是有效的URL`)
        }
        break

      case 'number':
        if (isNaN(Number(input.value))) {
          errors.push(`${input.field} 必须是有效的数字`)
        }
        break

      case 'html':
        // HTML内容需要清理
        const sanitized = this.sanitizeHTML(input.value)
        if (sanitized !== input.value) {
          warnings.push(`${input.field} 包含不安全的HTML内容，已被清理`)
        }
        break

      case 'css':
        // CSS内容检查
        if (this.containsXSS(input.value)) {
          errors.push(`${input.field} 包含不安全的CSS内容`)
        }
        break

      case 'js':
        // JavaScript内容检查（更严格）
        if (this.containsXSS(input.value) || /eval|Function|setTimeout|setInterval/i.test(input.value)) {
          errors.push(`${input.field} 包含不安全的JavaScript内容`)
        }
        break
    }

    // 自定义验证
    if (input.customValidator && !input.customValidator(input.value)) {
      errors.push(`${input.field} 验证失败`)
    }

    // 正则表达式验证
    if (input.pattern && !input.pattern.test(input.value)) {
      errors.push(`${input.field} 格式不正确`)
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      sanitized: input.type === 'html' ? this.sanitizeHTML(input.value) : undefined
    }
  }

  /**
   * 安全地设置HTML内容
   */
  setSecureHTML(element: Element, html: string): void {
    const sanitized = this.sanitizeHTML(html)
    element.innerHTML = sanitized
  }

  /**
   * 安全地设置文本内容
   */
  setSecureText(element: Element, text: string): void {
    element.textContent = text
  }

  /**
   * 安全地创建元素
   */
  secureCreateElement(tagName: string, attributes?: Record<string, string>, html?: string): HTMLElement {
    const element = document.createElement(tagName)

    // 安全地设置属性
    if (attributes) {
      Object.entries(attributes).forEach(([key, value]) => {
        if (this.containsXSS(value)) {
          console.warn(`🚫 属性 ${key} 包含XSS，已被阻止:`, value)
          return
        }
        element.setAttribute(key, value)
      })
    }

    // 安全地设置HTML内容
    if (html) {
      this.setSecureHTML(element, html)
    }

    return element
  }

  /**
   * 获取安全统计
   */
  getStatistics(): {
    blockedAttempts: number
    enabledRules: number
    totalRules: number
    isInitialized: boolean
  } {
    return {
      blockedAttempts: this.blockedAttempts,
      enabledRules: Array.from(this.rules.values()).filter(rule => rule.enabled).length,
      totalRules: this.rules.size,
      isInitialized: this.isInitialized
    }
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<SanitizationConfig>): void {
    this.config = { ...this.config, ...config }
    this.configureDOMPurify()
  }

  /**
   * 生成唯一ID
   */
  private generateId(): string {
    return `xss_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 重置配置
   */
  reset(): void {
    this.config = { ...this.DEFAULT_CONFIG }
    this.rules.clear()
    this.blockedAttempts = 0
    this.initializeDefaultRules()
    this.configureDOMPurify()
    console.log('🔄 XSS防护配置已重置')
  }
}

// 导出全局实例
export const xssProtection = XSSProtectionManager.getInstance()

// 便捷函数
export const {
  initialize,
  addRule,
  removeRule,
  containsXSS,
  sanitizeHTML,
  validateInput,
  setSecureHTML,
  setSecureText,
  secureCreateElement,
  getStatistics,
  updateConfig,
  reset
} = xssProtection

export type { XSSRule, SanitizationConfig, InputValidation, ValidationResult }