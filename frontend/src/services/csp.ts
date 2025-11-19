/**
 * 内容安全策略（CSP）管理服务
 * 提供CSP头部管理、违规监控和动态策略配置功能
 */

interface CSPDirective {
  name: string
  values: string[]
  enabled: boolean
}

interface CSPConfig {
  version: '1' | '2' | '3'
  reportOnly?: boolean
  directives: Record<string, string[]>
}

interface CSPViolation {
  blockedURI: string
  columnNumber?: number
  disposition: 'report' | 'enforce'
  documentURI: string
  effectiveDirective: string
  originalPolicy: string
  referrer: string
  sample: string
  sourceFile?: string
  statusCode: number
  violatedDirective: string
  lineNumber?: number
  timestamp: number
}

interface CSPRule {
  id: string
  name: string
  description: string
  enabled: boolean
  priority: number
  conditions: CSPCondition[]
  action: 'block' | 'report' | 'allow'
}

interface CSPCondition {
  directive: string
  pattern: string
  type: 'exact' | 'regex' | 'wildcard'
}

/**
 * CSP管理器
 */
export class CSPManager {
  private static instance: CSPManager
  private config: CSPConfig
  private violations: CSPViolation[] = []
  private rules: Map<string, CSPRule> = new Map()
  private isInitialized = false
  private nonceCache = new Map<string, string>()

  private readonly DEFAULT_DIRECTIVES: Record<string, string[]> = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "https:"],
    "font-src": ["'self'", "data:", "https:"],
    "connect-src": ["'self'", "https://api.lulaai.xyz"],
    "frame-src": ["'none'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
    "upgrade-insecure-requests": [],
    "block-all-mixed-content": []
  }

  private constructor() {
    this.config = {
      version: '3',
      reportOnly: false,
      directives: { ...this.DEFAULT_DIRECTIVES }
    }
    this.initializeDefaultRules()
  }

  /**
   * 获取CSPManager实例（单例模式）
   */
  static getInstance(): CSPManager {
    if (!CSPManager.instance) {
      CSPManager.instance = new CSPManager()
    }
    return CSPManager.instance
  }

  /**
   * 初始化CSP管理器
   */
  async initialize(config?: Partial<CSPConfig>): Promise<void> {
    if (this.isInitialized) {
      console.warn('CSP管理器已经初始化')
      return
    }

    // 合并配置
    this.config = {
      ...this.config,
      ...config,
      directives: {
        ...this.config.directives,
        ...config?.directives
      }
    }

    // 设置CSP违规报告监听
    this.setupViolationReporting()

    // 生成CSP头部
    this.injectCSPHeader()

    this.isInitialized = true
    console.log('🛡️ CSP管理器已初始化')
  }

  /**
   * 初始化默认CSP规则
   */
  private initializeDefaultRules(): void {
    // 内联脚本规则
    this.addRule({
      id: 'inline-scripts',
      name: '内联脚本检测',
      description: '检测并阻止内联脚本执行',
      enabled: true,
      priority: 1,
      conditions: [
        {
          directive: 'script-src',
          pattern: "'unsafe-inline'",
          type: 'exact'
        }
      ],
      action: 'block'
    })

    // 外部资源规则
    this.addRule({
      id: 'external-resources',
      name: '外部资源检测',
      description: '监控来自非信任域名的外部资源',
      enabled: true,
      priority: 2,
      conditions: [
        {
          directive: 'default-src',
          pattern: 'http://*',
          type: 'wildcard'
        }
      ],
      action: 'report'
    })

    // 数据协议规则
    this.addRule({
      id: 'data-protocols',
      name: '数据协议检测',
      description: '允许必要的数据协议使用',
      enabled: true,
      priority: 3,
      conditions: [
        {
          directive: 'img-src',
          pattern: 'data:',
          type: 'exact'
        }
      ],
      action: 'allow'
    })
  }

  /**
   * 设置违规报告监听
   */
  private setupViolationReporting(): void {
    // 监听securitypolicyviolation事件
    document.addEventListener('securitypolicyviolation', (event) => {
      const violation: CSPViolation = {
        blockedURI: event.blockedURI,
        columnNumber: event.columnNumber,
        disposition: event.disposition as 'report' | 'enforce',
        documentURI: event.documentURI,
        effectiveDirective: event.effectiveDirective,
        originalPolicy: event.originalPolicy,
        referrer: event.referrer,
        sample: event.sample,
        sourceFile: event.sourceFile,
        statusCode: event.statusCode,
        violatedDirective: event.violatedDirective,
        lineNumber: event.lineNumber,
        timestamp: Date.now()
      }

      this.handleViolation(violation)
    })

    // 设置Report-to API（如果支持）
    if ('ReportingObserver' in window) {
      const observer = new ReportingObserver((reports) => {
        reports.forEach((report) => {
          if (report.type === 'csp-violation') {
            this.handleViolation(report.body as any)
          }
        })
      })

      observer.observe()
    }
  }

  /**
   * 处理CSP违规
   */
  private handleViolation(violation: CSPViolation): void {
    // 记录违规
    this.violations.push(violation)

    // 清理旧违规记录（保留最近100条）
    if (this.violations.length > 100) {
      this.violations = this.violations.slice(-100)
    }

    // 检查规则匹配
    const matchedRule = this.findMatchingRule(violation)
    if (matchedRule) {
      this.executeRuleAction(matchedRule, violation)
    }

    // 记录到监控系统
    this.reportViolation(violation)
  }

  /**
   * 查找匹配的规则
   */
  private findMatchingRule(violation: CSPViolation): CSPRule | null {
    const enabledRules = Array.from(this.rules.values())
      .filter(rule => rule.enabled)
      .sort((a, b) => a.priority - b.priority)

    for (const rule of enabledRules) {
      if (this.matchesRule(rule, violation)) {
        return rule
      }
    }

    return null
  }

  /**
   * 检查违规是否匹配规则
   */
  private matchesRule(rule: CSPRule, violation: CSPViolation): boolean {
    return rule.conditions.some(condition => {
      const value = this.getDirectiveValue(violation, condition.directive)
      return this.matchPattern(value, condition.pattern, condition.type)
    })
  }

  /**
   * 获取指令值
   */
  private getDirectiveValue(violation: CSPViolation, directive: string): string {
    switch (directive) {
      case 'script-src':
        return violation.blockedURI
      case 'style-src':
        return violation.blockedURI
      case 'img-src':
        return violation.blockedURI
      case 'connect-src':
        return violation.blockedURI
      default:
        return violation.violatedDirective
    }
  }

  /**
   * 模式匹配
   */
  private matchPattern(value: string, pattern: string, type: 'exact' | 'regex' | 'wildcard'): boolean {
    switch (type) {
      case 'exact':
        return value === pattern
      case 'regex':
        return new RegExp(pattern).test(value)
      case 'wildcard': {
        const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$')
        return regex.test(value)
      }
      default:
        return false
    }
  }

  /**
   * 执行规则动作
   */
  private executeRuleAction(rule: CSPRule, violation: CSPViolation): void {
    switch (rule.action) {
      case 'block':
        console.warn(`🚫 CSP违规被阻止: ${rule.name}`, violation)
        break
      case 'report':
        console.info(`📝 CSP违规被记录: ${rule.name}`, violation)
        break
      case 'allow':
        console.log(`✅ CSP违规被允许: ${rule.name}`, violation)
        break
    }
  }

  /**
   * 报告违规到监控系统
   */
  private reportViolation(violation: CSPViolation): void {
    // 这里可以集成到Sentry或其他监控系统
    if (typeof window !== 'undefined' && 'sentry' in window) {
      // 记录到Sentry
      console.warn('CSP违规:', {
        type: 'csp_violation',
        directive: violation.violatedDirective,
        blockedURI: violation.blockedURI,
        documentURI: violation.documentURI
      })
    }

    // 发送到分析系统
    this.trackViolationEvent(violation)
  }

  /**
   * 追踪违规事件
   */
  private trackViolationEvent(violation: CSPViolation): void {
    // 这里可以集成到Google Analytics
    if (typeof window !== 'undefined' && 'gtag' in window) {
      (window as any).gtag('event', 'csp_violation', {
        'event_category': 'security',
        'event_label': violation.violatedDirective,
        'value': 1
      })
    }
  }

  /**
   * 注入CSP头部
   */
  private injectCSPHeader(): void {
    if (typeof document === 'undefined') return

    const metaTag = document.createElement('meta')
    metaTag.httpEquiv = this.config.reportOnly ? 'Content-Security-Policy-Report-Only' : 'Content-Security-Policy'
    metaTag.content = this.buildCSPString()

    // 移除现有的CSP meta标签
    const existingTags = document.querySelectorAll('meta[http-equiv*="Content-Security-Policy"]')
    existingTags.forEach(tag => tag.remove())

    // 添加新的CSP meta标签
    document.head.appendChild(metaTag)

    console.log('🔒 CSP头部已注入:', metaTag.content)
  }

  /**
   * 构建CSP字符串
   */
  private buildCSPString(): string {
    const directives: string[] = []

    for (const [directive, values] of Object.entries(this.config.directives)) {
      if (values.length > 0) {
        directives.push(`${directive} ${values.join(' ')}`)
      } else {
        directives.push(directive)
      }
    }

    // 添加报告端点
    if (!this.config.reportOnly) {
      directives.push("report-uri /csp-violation-report-endpoint")
      directives.push("report-to csp-endpoint")
    }

    return directives.join('; ')
  }

  /**
   * 添加CSP规则
   */
  addRule(rule: CSPRule): string {
    const id = rule.id || this.generateId()
    const fullRule: CSPRule = {
      ...rule,
      id
    }

    this.rules.set(id, fullRule)
    console.log(`CSP规则已添加: ${rule.name}`)
    return id
  }

  /**
   * 移除CSP规则
   */
  removeRule(ruleId: string): boolean {
    return this.rules.delete(ruleId)
  }

  /**
   * 更新CSP配置
   */
  updateConfig(config: Partial<CSPConfig>): void {
    this.config = {
      ...this.config,
      ...config,
      directives: {
        ...this.config.directives,
        ...config.directives
      }
    }

    // 重新注入CSP头部
    this.injectCSPHeader()
  }

  /**
   * 添加指令值
   */
  addDirectiveValue(directive: string, value: string): void {
    if (!this.config.directives[directive]) {
      this.config.directives[directive] = []
    }

    if (!this.config.directives[directive].includes(value)) {
      this.config.directives[directive].push(value)
      this.injectCSPHeader()
    }
  }

  /**
   * 移除指令值
   */
  removeDirectiveValue(directive: string, value: string): void {
    if (this.config.directives[directive]) {
      const index = this.config.directives[directive].indexOf(value)
      if (index > -1) {
        this.config.directives[directive].splice(index, 1)
        this.injectCSPHeader()
      }
    }
  }

  /**
   * 生成nonce值
   */
  generateNonce(directive: string = 'script-src'): string {
    const key = `${directive}_${Date.now()}`
    const nonce = btoa(Math.random().toString(36).substring(2, 15))
    this.nonceCache.set(key, nonce)

    // 清理过期nonce
    this.cleanupNonces()

    return nonce
  }

  /**
   * 清理过期nonce
   */
  private cleanupNonces(): void {
    const now = Date.now()
    const expiration = 5 * 60 * 1000 // 5分钟

    for (const [key] of this.nonceCache.entries()) {
      const timestamp = parseInt(key.split('_')[1])
      if (now - timestamp > expiration) {
        this.nonceCache.delete(key)
      }
    }
  }

  /**
   * 获取CSP违规历史
   */
  getViolations(limit: number = 50): CSPViolation[] {
    return this.violations
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit)
  }

  /**
   * 获取CSP统计
   */
  getStatistics(): {
    totalViolations: number
    violationsByDirective: Record<string, number>
    recentViolations: CSPViolation[]
    enabledRules: number
    isReportOnly: boolean
  } {
    const violationsByDirective: Record<string, number> = {}

    this.violations.forEach(violation => {
      violationsByDirective[violation.violatedDirective] =
        (violationsByDirective[violation.violatedDirective] || 0) + 1
    })

    return {
      totalViolations: this.violations.length,
      violationsByDirective,
      recentViolations: this.getViolations(10),
      enabledRules: Array.from(this.rules.values()).filter(rule => rule.enabled).length,
      isReportOnly: !!this.config.reportOnly
    }
  }

  /**
   * 启用强制模式
   */
  enforceMode(): void {
    this.config.reportOnly = false
    this.injectCSPHeader()
    console.log('🔒 CSP已切换到强制模式')
  }

  /**
   * 启用报告模式
   */
  reportOnlyMode(): void {
    this.config.reportOnly = true
    this.injectCSPHeader()
    console.log('📝 CSP已切换到报告模式')
  }

  /**
   * 生成唯一ID
   */
  private generateId(): string {
    return `csp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 获取当前CSP配置
   */
  getCurrentConfig(): CSPConfig {
    return { ...this.config }
  }

  /**
   * 重置CSP配置
   */
  reset(): void {
    this.config = {
      version: '3',
      reportOnly: false,
      directives: { ...this.DEFAULT_DIRECTIVES }
    }
    this.violations = []
    this.rules.clear()
    this.initializeDefaultRules()
    this.injectCSPHeader()
    console.log('🔄 CSP配置已重置')
  }
}

// 导出全局实例
export const cspManager = CSPManager.getInstance()

// 便捷函数
export const {
  initialize,
  addRule,
  removeRule,
  updateConfig,
  addDirectiveValue,
  removeDirectiveValue,
  generateNonce,
  getViolations,
  getStatistics,
  enforceMode,
  reportOnlyMode,
  getCurrentConfig,
  reset
} = cspManager

export type { CSPConfig, CSPViolation, CSPRule, CSPDirective }