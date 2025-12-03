/**
 * 安全头部和HTTPS管理服务
 * 提供安全头部配置、HTTPS强化和传输安全保护功能
 */

interface SecurityHeader {
  name: string
  value: string
  enabled: boolean
  description: string
  importance: 'low' | 'medium' | 'high' | 'critical'
}

interface HSTSConfig {
  enabled: boolean
  maxAge: number // 秒
  includeSubDomains: boolean
  preload: boolean
}

interface CertificateInfo {
  subject: string
  issuer: string
  validFrom: Date
  validTo: Date
  fingerprint: string
  protocol: string
  cipher: string
  isSecure: boolean
  daysUntilExpiry: number
}

interface TransportSecurity {
  httpsEnforced: boolean
  httpRedirected: boolean
  secureConnection: boolean
  protocolVersion: string
  cipherSuite: string
  certificateInfo: CertificateInfo | null
  securityScore: number // 0-100
}

interface SecurityHeaderConfig {
  strictTransportSecurity: HSTSConfig
  contentSecurityPolicy: boolean
  xFrameOptions: boolean
  xContentTypeOptions: boolean
  xXSSProtection: boolean
  referrerPolicy: boolean
  permissionsPolicy: boolean
  crossOriginEmbedderPolicy: boolean
  crossOriginOpenerPolicy: boolean
  crossOriginResourcePolicy: boolean
}

/**
 * 安全头部管理器
 */
export class SecurityHeaderManager {
  private static instance: SecurityHeaderManager
  private headers: Map<string, SecurityHeader> = new Map()
  private config: SecurityHeaderConfig
  private transportSecurity: TransportSecurity
  private isInitialized = false

  private readonly DEFAULT_HEADERS: SecurityHeader[] = [
    {
      name: 'Strict-Transport-Security',
      value: 'max-age=31536000; includeSubDomains; preload',
      enabled: true,
      description: '强制HTTPS连接，防止中间人攻击',
      importance: 'critical'
    },
    {
      name: 'Content-Security-Policy',
      value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://web3search-api.marovole.workers.dev https://api.lulaai.xyz; font-src 'self' data: https:; frame-ancestors 'none';",
      enabled: true,
      description: '内容安全策略，防止XSS和数据注入',
      importance: 'critical'
    },
    {
      name: 'X-Frame-Options',
      value: 'DENY',
      enabled: true,
      description: '防止点击劫持攻击',
      importance: 'high'
    },
    {
      name: 'X-Content-Type-Options',
      value: 'nosniff',
      enabled: true,
      description: '防止MIME类型嗅探',
      importance: 'high'
    },
    {
      name: 'X-XSS-Protection',
      value: '1; mode=block',
      enabled: true,
      description: 'XSS过滤器（已弃用，但仍有兼容性价值）',
      importance: 'medium'
    },
    {
      name: 'Referrer-Policy',
      value: 'strict-origin-when-cross-origin',
      enabled: true,
      description: '控制引用信息泄露',
      importance: 'medium'
    },
    {
      name: 'Permissions-Policy',
      value: 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()',
      enabled: true,
      description: '控制浏览器功能权限',
      importance: 'medium'
    },
    {
      name: 'Cross-Origin-Embedder-Policy',
      value: 'require-corp',
      enabled: false,
      description: '跨域嵌入策略',
      importance: 'low'
    },
    {
      name: 'Cross-Origin-Opener-Policy',
      value: 'same-origin',
      enabled: false,
      description: '跨域窗口策略',
      importance: 'low'
    },
    {
      name: 'Cross-Origin-Resource-Policy',
      value: 'same-origin',
      enabled: false,
      description: '跨域资源策略',
      importance: 'low'
    },
    {
      name: 'Cache-Control',
      value: 'no-store, no-cache, must-revalidate, proxy-revalidate',
      enabled: true,
      description: '缓存控制，防止敏感信息缓存',
      importance: 'medium'
    },
    {
      name: 'Pragma',
      value: 'no-cache',
      enabled: true,
      description: 'HTTP/1.0缓存控制',
      importance: 'low'
    }
  ]

  private readonly DEFAULT_CONFIG: SecurityHeaderConfig = {
    strictTransportSecurity: {
      enabled: true,
      maxAge: 31536000, // 1年
      includeSubDomains: true,
      preload: true
    },
    contentSecurityPolicy: true,
    xFrameOptions: true,
    xContentTypeOptions: true,
    xXSSProtection: true,
    referrerPolicy: true,
    permissionsPolicy: true,
    crossOriginEmbedderPolicy: false,
    crossOriginOpenerPolicy: false,
    crossOriginResourcePolicy: false
  }

  private constructor() {
    this.config = { ...this.DEFAULT_CONFIG }
    this.transportSecurity = this.initializeTransportSecurity()
    this.initializeHeaders()
  }

  /**
   * 获取SecurityHeaderManager实例（单例模式）
   */
  static getInstance(): SecurityHeaderManager {
    if (!SecurityHeaderManager.instance) {
      SecurityHeaderManager.instance = new SecurityHeaderManager()
    }
    return SecurityHeaderManager.instance
  }

  /**
   * 初始化安全头部管理器
   */
  async initialize(config?: Partial<SecurityHeaderConfig>): Promise<void> {
    if (this.isInitialized) {
      console.warn('安全头部管理器已经初始化')
      return
    }

    // 合并配置
    this.config = { ...this.config, ...config }

    // 检查HTTPS连接
    await this.checkTransportSecurity()

    // 应用配置到头部
    this.applyConfigToHeaders()

    // 注入安全头部（在客户端模拟）
    this.injectSecurityHeaders()

    // 设置HTTPS强制
    this.enforceHTTPS()

    this.isInitialized = true
    console.log('🔒 安全头部管理器已初始化')
  }

  /**
   * 初始化传输安全状态
   */
  private initializeTransportSecurity(): TransportSecurity {
    return {
      httpsEnforced: false,
      httpRedirected: false,
      secureConnection: false,
      protocolVersion: '',
      cipherSuite: '',
      certificateInfo: null,
      securityScore: 0
    }
  }

  /**
   * 初始化头部
   */
  private initializeHeaders(): void {
    this.DEFAULT_HEADERS.forEach(header => {
      this.headers.set(header.name, { ...header })
    })
  }

  /**
   * 检查传输安全
   */
  private async checkTransportSecurity(): Promise<void> {
    // 检查当前协议
    this.transportSecurity.httpsEnforced = window.location.protocol === 'https:'
    this.transportSecurity.secureConnection = this.transportSecurity.httpsEnforced

    // 模拟证书信息检查（实际应该从服务器获取）
    if (this.transportSecurity.httpsEnforced) {
      this.transportSecurity.certificateInfo = this.createMockCertificateInfo()
    }

    // 计算安全评分
    this.calculateSecurityScore()
  }

  /**
   * 创建模拟证书信息
   */
  private createMockCertificateInfo(): CertificateInfo {
    const now = new Date()
    const validFrom = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000) // 30天前
    const validTo = new Date(now.getTime() + 335 * 24 * 60 * 60 * 1000) // 335天后

    return {
      subject: 'CN=api.lulaai.xyz',
      issuer: 'CN=Let\'s Encrypt Authority X3',
      validFrom,
      validTo,
      fingerprint: 'AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD',
      protocol: 'TLSv1.3',
      cipher: 'TLS_AES_256_GCM_SHA384',
      isSecure: true,
      daysUntilExpiry: Math.floor((validTo.getTime() - now.getTime()) / (24 * 60 * 60 * 1000))
    }
  }

  /**
   * 计算安全评分
   */
  private calculateSecurityScore(): void {
    let score = 0

    // HTTPS使用情况（40分）
    if (this.transportSecurity.httpsEnforced) {
      score += 40
    }

    // 证书有效性（20分）
    if (this.transportSecurity.certificateInfo?.isSecure) {
      score += 20

      // 证书有效期（额外加分）
      if (this.transportSecurity.certificateInfo.daysUntilExpiry > 30) {
        score += 5
      }
    }

    // 安全头部配置（40分）
    let headerScore = 0
    this.headers.forEach(header => {
      if (header.enabled) {
        switch (header.importance) {
          case 'critical':
            headerScore += 10
            break
          case 'high':
            headerScore += 8
            break
          case 'medium':
            headerScore += 5
            break
          case 'low':
            headerScore += 2
            break
        }
      }
    })
    score += Math.min(headerScore, 40)

    this.transportSecurity.securityScore = Math.min(score, 100)
  }

  /**
   * 应用配置到头部
   */
  private applyConfigToHeaders(): void {
    // HSTS配置
    const hstsHeader = this.headers.get('Strict-Transport-Security')
    if (hstsHeader && this.config.strictTransportSecurity.enabled) {
      const hsts = this.config.strictTransportSecurity
      hstsHeader.value = this.buildHSTSValue(hsts)
      hstsHeader.enabled = true
    }

    // CSP配置
    const cspHeader = this.headers.get('Content-Security-Policy')
    if (cspHeader) {
      cspHeader.enabled = this.config.contentSecurityPolicy
    }

    // 其他头部配置
    const headerMappings: Record<keyof SecurityHeaderConfig, string> = {
      xFrameOptions: 'X-Frame-Options',
      xContentTypeOptions: 'X-Content-Type-Options',
      xXSSProtection: 'X-XSS-Protection',
      referrerPolicy: 'Referrer-Policy',
      permissionsPolicy: 'Permissions-Policy',
      crossOriginEmbedderPolicy: 'Cross-Origin-Embedder-Policy',
      crossOriginOpenerPolicy: 'Cross-Origin-Opener-Policy',
      crossOriginResourcePolicy: 'Cross-Origin-Resource-Policy',
      contentSecurityPolicy: 'Content-Security-Policy',
      strictTransportSecurity: 'Strict-Transport-Security'
    }

    Object.entries(headerMappings).forEach(([configKey, headerName]) => {
      if (configKey !== 'contentSecurityPolicy' && configKey !== 'strictTransportSecurity') {
        const header = this.headers.get(headerName)
        if (header) {
          header.enabled = this.config[configKey as keyof Omit<SecurityHeaderConfig, 'contentSecurityPolicy' | 'strictTransportSecurity'>]
        }
      }
    })
  }

  /**
   * 构建HSTS值
   */
  private buildHSTSValue(config: HSTSConfig): string {
    const parts = [`max-age=${config.maxAge}`]

    if (config.includeSubDomains) {
      parts.push('includeSubDomains')
    }

    if (config.preload) {
      parts.push('preload')
    }

    return parts.join('; ')
  }

  /**
   * 注入安全头部（客户端模拟）
   */
  private injectSecurityHeaders(): void {
    // 在客户端环境中，我们无法真正设置HTTP头部
    // 但可以通过meta标签模拟一些头部效果
    const enabledHeaders = Array.from(this.headers.values()).filter(h => h.enabled)

    console.log('🔒 已配置的安全头部:')
    enabledHeaders.forEach(header => {
      console.log(`  ${header.name}: ${header.value}`)
    })

    // 可以通过CSP meta标签设置内容安全策略
    const cspHeader = this.headers.get('Content-Security-Policy')
    if (cspHeader && cspHeader.enabled) {
      this.injectCSPMetaTag(cspHeader.value)
    }
  }

  /**
   * 注入CSP meta标签
   */
  private injectCSPMetaTag(cspValue: string): void {
    // 生产环境使用服务器 CSP 头，不注入 meta 标签
    if (import.meta.env.PROD) {
      console.log('🛡️ 生产环境：使用服务器 CSP 头，跳过 meta 标签注入')
      return
    }

    // 移除现有的CSP meta标签
    const existingTags = document.querySelectorAll('meta[http-equiv="Content-Security-Policy"]')
    existingTags.forEach(tag => tag.remove())

    // 添加新的CSP meta标签
    const metaTag = document.createElement('meta')
    metaTag.httpEquiv = 'Content-Security-Policy'
    metaTag.content = cspValue
    document.head.appendChild(metaTag)

    console.log('🛡️ CSP meta标签已注入')
  }

  /**
   * 强制HTTPS
   */
  private enforceHTTPS(): void {
    if (!this.transportSecurity.httpsEnforced && window.location.protocol === 'http:') {
      // 重定向到HTTPS
      const httpsUrl = `https://${window.location.host}${window.location.pathname}${window.location.search}`
      console.warn('🔄 重定向到HTTPS:', httpsUrl)
      window.location.replace(httpsUrl)
    }
  }

  /**
   * 添加安全头部
   */
  addHeader(header: Omit<SecurityHeader, 'name'>, name?: string): void {
    const headerName = name || this.generateHeaderName()
    const fullHeader: SecurityHeader = {
      name: headerName,
      ...header
    }

    this.headers.set(headerName, fullHeader)
    console.log(`安全头部已添加: ${headerName}`)
  }

  /**
   * 移除安全头部
   */
  removeHeader(name: string): boolean {
    return this.headers.delete(name)
  }

  /**
   * 启用/禁用头部
   */
  toggleHeader(name: string, enabled?: boolean): boolean {
    const header = this.headers.get(name)
    if (!header) return false

    header.enabled = enabled !== undefined ? enabled : !header.enabled
    console.log(`安全头部 ${name} 已${header.enabled ? '启用' : '禁用'}`)
    return true
  }

  /**
   * 更新头部值
   */
  updateHeaderValue(name: string, value: string): boolean {
    const header = this.headers.get(name)
    if (!header) return false

    header.value = value
    console.log(`安全头部 ${name} 的值已更新`)
    return true
  }

  /**
   * 获取头部
   */
  getHeader(name: string): SecurityHeader | undefined {
    return this.headers.get(name)
  }

  /**
   * 获取所有头部
   */
  getAllHeaders(): SecurityHeader[] {
    return Array.from(this.headers.values())
  }

  /**
   * 获取启用的头部
   */
  getEnabledHeaders(): SecurityHeader[] {
    return Array.from(this.headers.values()).filter(h => h.enabled)
  }

  /**
   * 获取传输安全信息
   */
  getTransportSecurity(): TransportSecurity {
    return { ...this.transportSecurity }
  }

  /**
   * 检查安全合规性
   */
  checkCompliance(): {
    score: number
    grade: 'A+' | 'A' | 'B' | 'C' | 'D' | 'F'
    issues: string[]
    recommendations: string[]
  } {
    const issues: string[] = []
    const recommendations: string[] = []
    const score = this.transportSecurity.securityScore

    // 检查HTTPS
    if (!this.transportSecurity.httpsEnforced) {
      issues.push('网站未使用HTTPS')
      recommendations.push('启用HTTPS加密传输')
    }

    // 检查HSTS
    const hstsHeader = this.headers.get('Strict-Transport-Security')
    if (!hstsHeader || !hstsHeader.enabled) {
      issues.push('未启用HSTS')
      recommendations.push('启用HTTP严格传输安全')
    }

    // 检查CSP
    const cspHeader = this.headers.get('Content-Security-Policy')
    if (!cspHeader || !cspHeader.enabled) {
      issues.push('未启用CSP')
      recommendations.push('启用内容安全策略')
    }

    // 检查其他重要头部
    const importantHeaders = ['X-Frame-Options', 'X-Content-Type-Options']
    importantHeaders.forEach(headerName => {
      const header = this.headers.get(headerName)
      if (!header || !header.enabled) {
        issues.push(`未启用${headerName}`)
        recommendations.push(`启用${headerName}头部`)
      }
    })

    // 计算等级
    let grade: 'A+' | 'A' | 'B' | 'C' | 'D' | 'F'
    if (score >= 95) grade = 'A+'
    else if (score >= 90) grade = 'A'
    else if (score >= 80) grade = 'B'
    else if (score >= 70) grade = 'C'
    else if (score >= 60) grade = 'D'
    else grade = 'F'

    return {
      score,
      grade,
      issues,
      recommendations
    }
  }

  /**
   * 生成安全报告
   */
  generateSecurityReport(): {
    timestamp: number
    transportSecurity: TransportSecurity
    headers: SecurityHeader[]
    compliance: any
    summary: string
  } {
    const compliance = this.checkCompliance()

    const summary = `安全评分: ${compliance.score}/100 (${compliance.grade}) - ` +
      `${compliance.issues.length} 个问题，${this.getEnabledHeaders().length} 个安全头部已启用`

    return {
      timestamp: Date.now(),
      transportSecurity: this.transportSecurity,
      headers: this.getAllHeaders(),
      compliance,
      summary
    }
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<SecurityHeaderConfig>): void {
    this.config = { ...this.config, ...config }
    this.applyConfigToHeaders()
    this.injectSecurityHeaders()
  }

  /**
   * 重置配置
   */
  reset(): void {
    this.config = { ...this.DEFAULT_CONFIG }
    this.headers.clear()
    this.initializeHeaders()
    this.transportSecurity = this.initializeTransportSecurity()
    console.log('🔄 安全头部配置已重置')
  }

  /**
   * 生成头部名称
   */
  private generateHeaderName(): string {
    return `Custom-Security-Header-${Date.now()}`
  }
}

// 导出全局实例
export const securityHeaders = SecurityHeaderManager.getInstance()

// 便捷函数
export const {
  initialize,
  addHeader,
  removeHeader,
  toggleHeader,
  updateHeaderValue,
  getHeader,
  getAllHeaders,
  getEnabledHeaders,
  getTransportSecurity,
  checkCompliance,
  generateSecurityReport,
  updateConfig,
  reset
} = securityHeaders

export type { SecurityHeader, HSTSConfig, CertificateInfo, TransportSecurity, SecurityHeaderConfig }