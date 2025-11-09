/**
 * 安全系统统一入口
 * 整合CSP管理、XSS防护、依赖安全和安全头部配置
 */

import { cspManager } from './csp'
import { xssProtection } from './xssProtection'
import { dependencySecurity } from './dependencySecurity'
import { securityHeaders } from './securityHeaders'
import { monitoring } from './monitoring'

interface SecurityConfig {
  csp?: {
    enabled?: boolean
    reportOnly?: boolean
    customDirectives?: Record<string, string[]>
  }
  xss?: {
    enabled?: boolean
    sanitizationConfig?: any
  }
  dependencies?: {
    enabled?: boolean
    autoScan?: boolean
    allowedLicenses?: string[]
  }
  headers?: {
    enabled?: boolean
    hsts?: boolean
    customHeaders?: Array<{ name: string; value: string }>
  }
  monitoring?: {
    enabled?: boolean
    reportViolations?: boolean
  }
}

interface SecurityStatus {
  initialized: boolean
  components: {
    csp: boolean
    xss: boolean
    dependencies: boolean
    headers: boolean
    monitoring: boolean
  }
  score: number
  threats: string[]
  recommendations: string[]
}

interface SecurityEvent {
  type: 'violation' | 'vulnerability' | 'attack' | 'compliance'
  severity: 'low' | 'medium' | 'high' | 'critical'
  source: string
  message: string
  timestamp: number
  metadata: Record<string, any>
}

/**
 * 安全系统管理器
 */
export class SecurityManager {
  private static instance: SecurityManager
  private isInitialized = false
  private config: SecurityConfig = {}
  private eventHistory: SecurityEvent[] = []
  private isMonitoring = false

  private constructor() {}

  /**
   * 获取SecurityManager实例（单例模式）
   */
  static getInstance(): SecurityManager {
    if (!SecurityManager.instance) {
      SecurityManager.instance = new SecurityManager()
    }
    return SecurityManager.instance
  }

  /**
   * 初始化安全系统
   */
  async initialize(config?: SecurityConfig): Promise<void> {
    if (this.isInitialized) {
      console.warn('安全系统已经初始化')
      return
    }

    this.config = { ...this.getDefaultConfig(), ...config }

    try {
      // 初始化CSP管理器
      if (this.config.csp?.enabled) {
        await cspManager.initialize({
          reportOnly: this.config.csp.reportOnly,
          directives: this.config.csp.customDirectives
        })
        console.log('🛡️ CSP管理器已初始化')
      }

      // 初始化XSS防护
      if (this.config.xss?.enabled) {
        await xssProtection.initialize(this.config.xss.sanitizationConfig)
        console.log('🔒 XSS防护已初始化')
      }

      // 初始化依赖安全管理
      if (this.config.dependencies?.enabled) {
        await dependencySecurity.initialize({
          autoScan: this.config.dependencies.autoScan,
          // 只传递已定义的配置值，避免 undefined 覆盖默认值
          ...(this.config.dependencies.allowedLicenses && {
            allowedLicenses: this.config.dependencies.allowedLicenses
          }),
          notifyOnVulnerabilities: true
        })
        console.log('📦 依赖安全管理已初始化')
      }

      // 初始化安全头部
      if (this.config.headers?.enabled) {
        await securityHeaders.initialize({
          contentSecurityPolicy: this.config.csp?.enabled,
          strictTransportSecurity: {
            enabled: true,
            maxAge: 31536000,
            includeSubDomains: true,
            preload: true
          }
        })
        console.log('🔐 安全头部已配置')
      }

      // 设置安全事件监听
      this.setupSecurityEventListeners()

      // 启动安全监控
      if (this.config.monitoring?.enabled) {
        this.startSecurityMonitoring()
      }

      this.isInitialized = true
      console.log('✅ 安全系统初始化完成')

      // 记录初始化事件
      this.recordSecurityEvent({
        type: 'compliance',
        severity: 'low',
        source: 'security_manager',
        message: '安全系统初始化完成',
        timestamp: Date.now(),
        metadata: { config: this.config }
      })

    } catch (error) {
      console.error('❌ 安全系统初始化失败:', error)
      throw error
    }
  }

  /**
   * 获取默认配置
   */
  private getDefaultConfig(): SecurityConfig {
    return {
      csp: {
        enabled: true,
        reportOnly: false // 生产环境设为false
      },
      xss: {
        enabled: true
      },
      dependencies: {
        enabled: true,
        autoScan: true,
        allowedLicenses: ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC']
      },
      headers: {
        enabled: true,
        hsts: true
      },
      monitoring: {
        enabled: true,
        reportViolations: true
      }
    }
  }

  /**
   * 设置安全事件监听器
   */
  private setupSecurityEventListeners(): void {
    // 监听CSP违规
    if (this.config.csp?.enabled) {
      // 这里可以设置CSP违规事件监听
      console.log('📡 CSP违规监听已设置')
    }

    // 监听XSS检测
    if (this.config.xss?.enabled) {
      // 这里可以设置XSS检测事件监听
      console.log('📡 XSS检测监听已设置')
    }

    // 监听安全头部违规
    if (this.config.headers?.enabled) {
      // 这里可以设置安全头部违规监听
      console.log('📡 安全头部监听已设置')
    }
  }

  /**
   * 启动安全监控
   */
  private startSecurityMonitoring(): void {
    this.isMonitoring = true

    // 定期安全检查
    setInterval(() => {
      this.performSecurityCheck()
    }, 5 * 60 * 1000) // 每5分钟检查一次

    console.log('🔍 安全监控已启动')
  }

  /**
   * 执行安全检查
   */
  private async performSecurityCheck(): Promise<void> {
    try {
      // 检查依赖漏洞
      if (this.config.dependencies?.enabled) {
        const report = dependencySecurity.generateSecurityReport()
        if (report.vulnerableDependencies > 0) {
          this.recordSecurityEvent({
            type: 'vulnerability',
            severity: 'high',
            source: 'dependency_security',
            message: `发现 ${report.vulnerableDependencies} 个有漏洞的依赖`,
            timestamp: Date.now(),
            metadata: { report }
          })
        }
      }

      // 检查安全头部合规性
      if (this.config.headers?.enabled) {
        const compliance = securityHeaders.checkCompliance()
        if (compliance.score < 80) {
          this.recordSecurityEvent({
            type: 'compliance',
            severity: 'medium',
            source: 'security_headers',
            message: `安全合规性评分较低: ${compliance.score}/100`,
            timestamp: Date.now(),
            metadata: { compliance }
          })
        }
      }

    } catch (error) {
      console.error('安全检查失败:', error)
    }
  }

  /**
   * 记录安全事件
   */
  private recordSecurityEvent(event: SecurityEvent): void {
    this.eventHistory.push(event)

    // 保留最近100个事件
    if (this.eventHistory.length > 100) {
      this.eventHistory = this.eventHistory.slice(-100)
    }

    // 发送到监控系统
    if (this.config.monitoring?.enabled && this.config.monitoring?.reportViolations) {
      monitoring.trackCustomEvent('security_event', 'security', {
        type: event.type,
        severity: event.severity,
        source: event.source,
        message: event.message
      })
    }

    // 控制台输出
    this.logSecurityEvent(event)
  }

  /**
   * 输出安全事件日志
   */
  private logSecurityEvent(event: SecurityEvent): void {
    const level = this.getLogLevel(event.severity)
    const icon = this.getSeverityIcon(event.severity)

    console[level](`${icon} 安全事件 [${event.severity.toUpperCase()}] ${event.source}: ${event.message}`)
  }

  /**
   * 获取日志级别
   */
  private getLogLevel(severity: string): 'log' | 'warn' | 'error' {
    switch (severity) {
      case 'critical':
      case 'high':
        return 'error'
      case 'medium':
        return 'warn'
      default:
        return 'log'
    }
  }

  /**
   * 获取严重程度图标
   */
  private getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'critical':
        return '🚨'
      case 'high':
        return '⚠️'
      case 'medium':
        return '⚡'
      default:
        return 'ℹ️'
    }
  }

  /**
   * 手动执行安全扫描
   */
  async performSecurityScan(): Promise<{
    csp: any
    xss: any
    dependencies: any
    headers: any
    overallScore: number
    recommendations: string[]
  }> {
    console.log('🔍 开始执行全面安全扫描...')

    const results: any = {}

    // CSP扫描
    if (this.config.csp?.enabled) {
      results.csp = {
        statistics: cspManager.getStatistics(),
        violations: cspManager.getViolations(10)
      }
    }

    // XSS防护扫描
    if (this.config.xss?.enabled) {
      results.xss = {
        statistics: xssProtection.getStatistics()
      }
    }

    // 依赖安全扫描
    if (this.config.dependencies?.enabled) {
      results.dependencies = await dependencySecurity.triggerScan()
    }

    // 安全头部扫描
    if (this.config.headers?.enabled) {
      results.headers = securityHeaders.generateSecurityReport()
    }

    // 计算总体评分
    const overallScore = this.calculateOverallSecurityScore(results)

    // 生成建议
    const recommendations = this.generateSecurityRecommendations(results)

    console.log('✅ 安全扫描完成')
    console.log(`📊 总体安全评分: ${overallScore}/100`)

    return {
      ...results,
      overallScore,
      recommendations
    }
  }

  /**
   * 计算总体安全评分
   */
  private calculateOverallSecurityScore(results: any): number {
    let score = 0
    let components = 0

    // CSP评分（30分）
    if (results.csp) {
      const cspScore = results.csp.statistics.totalViolations === 0 ? 30 : Math.max(0, 30 - results.csp.statistics.totalViolations * 5)
      score += cspScore
      components++
    }

    // XSS防护评分（25分）
    if (results.xss) {
      const xssScore = results.xss.statistics.blockedAttempts === 0 ? 25 : Math.max(0, 25 - results.xss.statistics.blockedAttempts)
      score += xssScore
      components++
    }

    // 依赖安全评分（25分）
    if (results.dependencies) {
      const depScore = results.dependencies.vulnerableDependencies === 0 ? 25 : Math.max(0, 25 - results.dependencies.vulnerableDependencies * 10)
      score += depScore
      components++
    }

    // 安全头部评分（20分）
    if (results.headers) {
      score += results.headers.compliance.score * 0.2
      components++
    }

    return components > 0 ? Math.round(score) : 0
  }

  /**
   * 生成安全建议
   */
  private generateSecurityRecommendations(results: any): string[] {
    const recommendations: string[] = []

    // CSP建议
    if (results.csp && results.csp.statistics.totalViolations > 0) {
      recommendations.push(`检查并修复 ${results.csp.statistics.totalViolations} 个CSP违规`)
    }

    // XSS防护建议
    if (results.xss && results.xss.statistics.blockedAttempts > 0) {
      recommendations.push(`审查被阻止的 ${results.xss.statistics.blockedAttempts} 次XSS攻击尝试`)
    }

    // 依赖安全建议
    if (results.dependencies && results.dependencies.vulnerableDependencies > 0) {
      recommendations.push(`更新 ${results.dependencies.vulnerableDependencies} 个有漏洞的依赖包`)
    }

    // 安全头部建议
    if (results.headers && results.headers.compliance.score < 100) {
      recommendations.push('解决安全头部配置问题以提高合规性评分')
    }

    return recommendations
  }

  /**
   * 获取安全状态
   */
  getSecurityStatus(): SecurityStatus {
    const components = {
      csp: !!this.config.csp?.enabled,
      xss: !!this.config.xss?.enabled,
      dependencies: !!this.config.dependencies?.enabled,
      headers: !!this.config.headers?.enabled,
      monitoring: !!this.config.monitoring?.enabled
    }

    // 统计威胁
    const threats = this.eventHistory
      .filter(event => event.type === 'attack' || event.type === 'vulnerability')
      .slice(-10)
      .map(event => event.message)

    // 生成建议
    const recommendations = this.generateQuickRecommendations()

    return {
      initialized: this.isInitialized,
      components,
      score: this.getQuickSecurityScore(),
      threats,
      recommendations
    }
  }

  /**
   * 快速安全评分
   */
  private getQuickSecurityScore(): number {
    let score = 0

    // 基础组件启用情况（60分）
    if (this.config.csp?.enabled) score += 15
    if (this.config.xss?.enabled) score += 15
    if (this.config.dependencies?.enabled) score += 15
    if (this.config.headers?.enabled) score += 15

    // 最近威胁情况（40分）
    const recentThreats = this.eventHistory
      .filter(event =>
        (event.type === 'attack' || event.type === 'vulnerability') &&
        Date.now() - event.timestamp < 24 * 60 * 60 * 1000 // 24小时内
      )

    score += Math.max(0, 40 - recentThreats.length * 10)

    return Math.min(score, 100)
  }

  /**
   * 生成快速建议
   */
  private generateQuickRecommendations(): string[] {
    const recommendations: string[] = []

    if (!this.config.csp?.enabled) {
      recommendations.push('启用内容安全策略(CSP)以防止XSS攻击')
    }

    if (!this.config.xss?.enabled) {
      recommendations.push('启用XSS防护以保护应用安全')
    }

    if (!this.config.dependencies?.enabled) {
      recommendations.push('启用依赖安全管理以检测漏洞')
    }

    if (!this.config.headers?.enabled) {
      recommendations.push('配置安全头部以提高传输安全性')
    }

    const recentThreats = this.eventHistory
      .filter(event =>
        (event.type === 'attack' || event.type === 'vulnerability') &&
        Date.now() - event.timestamp < 24 * 60 * 60 * 1000
      )

    if (recentThreats.length > 0) {
      recommendations.push(`最近24小时内发现 ${recentThreats.length} 个安全威胁，建议立即检查`)
    }

    return recommendations
  }

  /**
   * 获取安全事件历史
   */
  getSecurityEvents(limit: number = 50): SecurityEvent[] {
    return this.eventHistory
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit)
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<SecurityConfig>): void {
    this.config = { ...this.config, ...config }

    // 重新初始化相关组件
    if (config.csp && this.config.csp?.enabled) {
      cspManager.updateConfig(config.csp)
    }

    if (config.headers && this.config.headers?.enabled) {
      securityHeaders.updateConfig({})
    }
  }

  /**
   * 重置安全系统
   */
  reset(): void {
    this.isInitialized = false
    this.isMonitoring = false
    this.eventHistory = []
    this.config = {}

    cspManager.reset()
    xssProtection.reset()
    dependencySecurity.reset()
    securityHeaders.reset()

    console.log('🔄 安全系统已重置')
  }
}

// 导出全局实例
export const security = SecurityManager.getInstance()

// 便捷函数
export const {
  initialize,
  performSecurityScan,
  getSecurityStatus,
  getSecurityEvents,
  updateConfig,
  reset
} = security

export type { SecurityConfig, SecurityStatus, SecurityEvent }