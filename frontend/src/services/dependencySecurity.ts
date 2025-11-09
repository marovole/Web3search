/**
 * 依赖安全管理服务
 * 提供依赖包漏洞扫描、许可证合规检查和依赖更新管理功能
 */

interface Vulnerability {
  id: string
  packageName: string
  version: string
  severity: 'low' | 'moderate' | 'high' | 'critical'
  title: string
  description: string
  url: string
  cwe?: string[]
  cvssScore?: number
  patchedVersions?: string[]
  recommendation?: string
  discoveredAt: number
}

interface Dependency {
  name: string
  version: string
  license: string
  type: 'dependencies' | 'devDependencies' | 'peerDependencies'
  vulnerabilities: Vulnerability[]
  lastChecked: number
  autoUpdate: boolean
}

interface LicenseInfo {
  name: string
  spdxId: string
  url: string
  allowed: boolean
  riskLevel: 'low' | 'medium' | 'high'
  conditions?: string[]
  limitations?: string[]
  permissions?: string[]
}

interface SecurityReport {
  generatedAt: number
  totalDependencies: number
  vulnerableDependencies: number
  vulnerabilitiesBySeverity: Record<string, number>
  licenseIssues: number
  outdatedDependencies: number
  recommendations: string[]
  dependencies: Dependency[]
}

interface SecurityConfig {
  autoScan: boolean
  scanInterval: number // 扫描间隔（小时）
  allowedLicenses: string[]
  blockedLicenses: string[]
  autoUpdatePatches: boolean
  notifyOnVulnerabilities: boolean
  severityThreshold: 'low' | 'moderate' | 'high' | 'critical'
}

type LicenseListKey = 'allowedLicenses' | 'blockedLicenses'

/**
 * 依赖安全管理器
 */
export class DependencySecurityManager {
  private static instance: DependencySecurityManager
  private dependencies: Map<string, Dependency> = new Map()
  private licenses: Map<string, LicenseInfo> = new Map()
  private config: SecurityConfig
  private isInitialized = false
  private scanInterval?: NodeJS.Timeout

  private readonly DEFAULT_CONFIG: SecurityConfig = {
    autoScan: true,
    scanInterval: 24, // 24小时
    allowedLicenses: [
      'MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC',
      'CC0-1.0', 'Unlicense', 'WTFPL'
    ],
    blockedLicenses: [
      'GPL-2.0', 'GPL-3.0', 'AGPL-1.0', 'AGPL-3.0'
    ],
    autoUpdatePatches: false,
    notifyOnVulnerabilities: true,
    severityThreshold: 'moderate'
  }

  private readonly LICENSE_DATABASE: Record<string, LicenseInfo> = {
    'MIT': {
      name: 'MIT License',
      spdxId: 'MIT',
      url: 'https://opensource.org/licenses/MIT',
      allowed: true,
      riskLevel: 'low',
      permissions: ['commercial-use', 'modifications', 'distribution', 'private-use'],
      conditions: ['include-copyright', 'include-license'],
      limitations: ['liability', 'warranty']
    },
    'Apache-2.0': {
      name: 'Apache License 2.0',
      spdxId: 'Apache-2.0',
      url: 'https://opensource.org/licenses/Apache-2.0',
      allowed: true,
      riskLevel: 'low',
      permissions: ['commercial-use', 'modifications', 'distribution', 'private-use', 'patent-use'],
      conditions: ['include-copyright', 'include-license', 'document-changes'],
      limitations: ['liability', 'warranty', 'trademark-use']
    },
    'GPL-3.0': {
      name: 'GNU General Public License v3.0',
      spdxId: 'GPL-3.0',
      url: 'https://opensource.org/licenses/GPL-3.0',
      allowed: false,
      riskLevel: 'high',
      permissions: ['commercial-use', 'modifications', 'distribution'],
      conditions: ['include-copyright', 'include-license', 'document-changes', 'disclose-source', 'same-license'],
      limitations: ['liability', 'warranty']
    }
  }

  private constructor() {
    this.config = { ...this.DEFAULT_CONFIG }
  }

  /**
   * 获取DependencySecurityManager实例（单例模式）
   */
  static getInstance(): DependencySecurityManager {
    if (!DependencySecurityManager.instance) {
      DependencySecurityManager.instance = new DependencySecurityManager()
    }
    return DependencySecurityManager.instance
  }

  /**
   * 初始化依赖安全管理器
   */
  async initialize(config?: Partial<SecurityConfig>): Promise<void> {
    if (this.isInitialized) {
      console.warn('依赖安全管理器已经初始化')
      return
    }

    // 合并配置
    this.config = { ...this.config, ...config }

    // 加载package.json中的依赖
    await this.loadDependencies()

    // 初始化许可证数据库
    this.initializeLicenseDatabase()

    // 执行初始扫描
    await this.performSecurityScan()

    // 设置定期扫描
    if (this.config.autoScan) {
      this.setupPeriodicScanning()
    }

    this.isInitialized = true
    console.log('🔒 依赖安全管理器已初始化')
  }

  /**
   * 加载依赖信息
   */
  private async loadDependencies(): Promise<void> {
    try {
      // 在浏览器环境中，我们无法直接读取package.json
      // 这里使用一个模拟的依赖列表
      const mockDependencies: Record<string, { version: string; type: string }> = {
        'react': { version: '18.2.0', type: 'dependencies' },
        'react-dom': { version: '18.2.0', type: 'dependencies' },
        '@sentry/react': { version: '10.22.0', type: 'dependencies' },
        'dompurify': { version: '3.0.5', type: 'dependencies' },
        'typescript': { version: '5.2.2', type: 'devDependencies' },
        'vite': { version: '5.0.8', type: 'devDependencies' }
      }

      Object.entries(mockDependencies).forEach(([name, info]) => {
        this.dependencies.set(name, {
          name,
          version: info.version,
          license: this.guessLicense(name),
          type: info.type as any,
          vulnerabilities: [],
          lastChecked: Date.now(),
          autoUpdate: false
        })
      })

      console.log(`已加载 ${this.dependencies.size} 个依赖包`)
    } catch (error) {
      console.error('加载依赖信息失败:', error)
    }
  }

  /**
   * 猜测许可证
   */
  private guessLicense(packageName: string): string {
    // 基于包名猜测许可证（这是一个简化的实现）
    const knownLicenses: Record<string, string> = {
      'react': 'MIT',
      'react-dom': 'MIT',
      '@sentry/react': 'MIT',
      'dompurify': 'Apache-2.0',
      'typescript': 'Apache-2.0',
      'vite': 'MIT'
    }

    return knownLicenses[packageName] || 'Unknown'
  }

  /**
   * 初始化许可证数据库
   */
  private initializeLicenseDatabase(): void {
    Object.entries(this.LICENSE_DATABASE).forEach(([spdxId, license]) => {
      this.licenses.set(spdxId, license)
    })
  }

  /**
   * 执行安全扫描
   */
  private async performSecurityScan(): Promise<void> {
    console.log('🔍 开始执行依赖安全扫描...')

    const scanResults: Dependency[] = []

    for (const dependency of this.dependencies.values()) {
      // 检查漏洞
      const vulnerabilities = await this.checkVulnerabilities(dependency.name, dependency.version)

      // 更新依赖信息
      const updatedDependency = {
        ...dependency,
        vulnerabilities,
        lastChecked: Date.now()
      }

      this.dependencies.set(dependency.name, updatedDependency)
      scanResults.push(updatedDependency)

      // 如果发现严重漏洞，立即通知
      const criticalVulns = vulnerabilities.filter(v =>
        v.severity === 'critical' || v.severity === 'high'
      )

      if (criticalVulns.length > 0 && this.config.notifyOnVulnerabilities) {
        this.notifyVulnerabilities(dependency.name, criticalVulns)
      }
    }

    // 检查许可证合规性
    this.checkLicenseCompliance()

    console.log(`✅ 安全扫描完成，检查了 ${scanResults.length} 个依赖包`)
  }

  /**
   * 检查漏洞
   */
  private async checkVulnerabilities(packageName: string, version: string): Promise<Vulnerability[]> {
    // 这里应该调用真实的漏洞数据库API（如OSV API, Snyk API等）
    // 由于这是浏览器环境，我们使用模拟数据
    const mockVulnerabilities: Record<string, Vulnerability[]> = {
      'react': [
        {
          id: 'CVE-2021-23434',
          packageName: 'react',
          version: '18.2.0',
          severity: 'moderate',
          title: 'React Server-Side Rendering Vulnerability',
          description: 'A potential XSS vulnerability in server-side rendering',
          url: 'https://nvd.nist.gov/vuln/detail/CVE-2021-23434',
          cvssScore: 6.1,
          patchedVersions: ['18.2.1', '18.3.0'],
          recommendation: 'Update to React 18.2.1 or later',
          discoveredAt: Date.now()
        }
      ]
    }

    return mockVulnerabilities[packageName] || []
  }

  /**
   * 安全获取许可证列表，避免 undefined 覆盖默认值
   */
  private resolveLicenseList(key: LicenseListKey): string[] {
    const partialConfig = this.config as Partial<Record<LicenseListKey, string[] | undefined>>
    const configuredList = partialConfig[key]

    if (Array.isArray(configuredList)) {
      return configuredList
    }

    if (!this.isInitialized) {
      console.warn(`依赖安全配置尚未初始化，${key} 使用默认值`)
    }

    const fallback = this.DEFAULT_CONFIG[key]
    return Array.isArray(fallback) ? [...fallback] : []
  }

  /**
   * 检查许可证合规性
   */
  private checkLicenseCompliance(): void {
    if (this.dependencies.size === 0) {
      return
    }

    const issues: string[] = []
    const blockedLicenses = this.resolveLicenseList('blockedLicenses')
    const allowedLicenses = this.resolveLicenseList('allowedLicenses')

    try {
      for (const dependency of this.dependencies.values()) {
        const license = this.licenses.get(dependency.license)

        if (!license) {
          issues.push(`未知许可证: ${dependency.name} (${dependency.license})`)
          continue
        }

        // 检查是否为阻止的许可证
        if (blockedLicenses.includes(dependency.license)) {
          issues.push(`禁止的许可证: ${dependency.name} 使用 ${dependency.license}`)
        }

        // 检查是否为允许的许可证
        if (
          allowedLicenses.length > 0 &&
          !allowedLicenses.includes(dependency.license)
        ) {
          issues.push(`未批准的许可证: ${dependency.name} 使用 ${dependency.license}`)
        }
      }

      if (issues.length > 0) {
        console.warn('⚠️ 许可证合规性问题:', issues)
        this.notifyLicenseIssues(issues)
      }
    } catch (error) {
      console.error('许可证合规性检查失败:', error)
    }
  }

  /**
   * 通知漏洞
   */
  private notifyVulnerabilities(packageName: string, vulnerabilities: Vulnerability[]): void {
    console.error(`🚨 发现安全漏洞: ${packageName}`)
    vulnerabilities.forEach(vuln => {
      console.error(`  - ${vuln.title} (${vuln.severity})`)
      console.error(`    ${vuln.description}`)
      console.error(`    修复建议: ${vuln.recommendation}`)
      console.error(`    更多信息: ${vuln.url}`)
    })

    // 这里可以添加更多的通知方式，如发送到监控系统
  }

  /**
   * 通知许可证问题
   */
  private notifyLicenseIssues(issues: string[]): void {
    console.warn('⚠️ 许可证合规性问题:')
    issues.forEach(issue => {
      console.warn(`  - ${issue}`)
    })
  }

  /**
   * 设置定期扫描
   */
  private setupPeriodicScanning(): void {
    const intervalMs = this.config.scanInterval * 60 * 60 * 1000

    this.scanInterval = setInterval(() => {
      this.performSecurityScan()
    }, intervalMs)

    console.log(`⏰ 已设置定期扫描，间隔: ${this.config.scanInterval} 小时`)
  }

  /**
   * 停止定期扫描
   */
  stopPeriodicScanning(): void {
    if (this.scanInterval) {
      clearInterval(this.scanInterval)
      this.scanInterval = undefined
      console.log('⏹️ 已停止定期扫描')
    }
  }

  /**
   * 手动触发扫描
   */
  async triggerScan(): Promise<SecurityReport> {
    console.log('🔍 手动触发安全扫描...')
    await this.performSecurityScan()
    return this.generateSecurityReport()
  }

  /**
   * 生成安全报告
   */
  generateSecurityReport(): SecurityReport {
    const vulnerabilitiesBySeverity: Record<string, number> = {
      low: 0,
      moderate: 0,
      high: 0,
      critical: 0
    }

    let vulnerableDependencies = 0
    let licenseIssues = 0
    let outdatedDependencies = 0

    const dependencies: Dependency[] = []
    const blockedLicenses = this.resolveLicenseList('blockedLicenses')

    for (const dependency of this.dependencies.values()) {
      dependencies.push(dependency)

      // 统计漏洞
      if (dependency.vulnerabilities.length > 0) {
        vulnerableDependencies++
        dependency.vulnerabilities.forEach(vuln => {
          vulnerabilitiesBySeverity[vuln.severity]++
        })
      }

      // 检查许可证问题
      const license = this.licenses.get(dependency.license)
      if (!license || blockedLicenses.includes(dependency.license)) {
        licenseIssues++
      }

      // 检查是否过期（简化实现）
      if (this.isOutdated(dependency)) {
        outdatedDependencies++
      }
    }

    // 生成建议
    const recommendations = this.generateRecommendations(vulnerabilitiesBySeverity, licenseIssues, outdatedDependencies)

    return {
      generatedAt: Date.now(),
      totalDependencies: this.dependencies.size,
      vulnerableDependencies,
      vulnerabilitiesBySeverity,
      licenseIssues,
      outdatedDependencies,
      recommendations,
      dependencies
    }
  }

  /**
   * 检查依赖是否过期
   */
  private isOutdated(dependency: Dependency): boolean {
    // 这是一个简化的实现，实际应该检查npm registry中的最新版本
    const knownOutdated: Record<string, string> = {
      'react': '18.3.0',
      '@sentry/react': '10.23.0'
    }

    const latestVersion = knownOutdated[dependency.name]
    if (latestVersion && this.compareVersions(dependency.version, latestVersion) < 0) {
      return true
    }

    return false
  }

  /**
   * 比较版本号
   */
  private compareVersions(version1: string, version2: string): number {
    const v1parts = version1.split('.').map(Number)
    const v2parts = version2.split('.').map(Number)

    const maxLength = Math.max(v1parts.length, v2parts.length)

    for (let i = 0; i < maxLength; i++) {
      const v1part = v1parts[i] || 0
      const v2part = v2parts[i] || 0

      if (v1part > v2part) return 1
      if (v1part < v2part) return -1
    }

    return 0
  }

  /**
   * 生成建议
   */
  private generateRecommendations(
    vulnerabilitiesBySeverity: Record<string, number>,
    licenseIssues: number,
    outdatedDependencies: number
  ): string[] {
    const recommendations: string[] = []

    // 漏洞相关建议
    const totalVulnerabilities = Object.values(vulnerabilitiesBySeverity).reduce((a, b) => a + b, 0)
    if (totalVulnerabilities > 0) {
      if (vulnerabilitiesBySeverity.critical > 0) {
        recommendations.push(`立即更新包含严重漏洞的依赖包（${vulnerabilitiesBySeverity.critical} 个）`)
      }
      if (vulnerabilitiesBySeverity.high > 0) {
        recommendations.push(`尽快更新包含高危漏洞的依赖包（${vulnerabilitiesBySeverity.high} 个）`)
      }
      if (vulnerabilitiesBySeverity.moderate > 0) {
        recommendations.push(`计划更新包含中危漏洞的依赖包（${vulnerabilitiesBySeverity.moderate} 个）`)
      }
    }

    // 许可证相关建议
    if (licenseIssues > 0) {
      recommendations.push(`解决 ${licenseIssues} 个许可证合规性问题`)
    }

    // 过期依赖相关建议
    if (outdatedDependencies > 0) {
      recommendations.push(`更新 ${outdatedDependencies} 个过期的依赖包`)
    }

    // 通用建议
    if (totalVulnerabilities === 0 && licenseIssues === 0 && outdatedDependencies === 0) {
      recommendations.push('所有依赖包都是安全的，继续保持定期扫描')
    }

    return recommendations
  }

  /**
   * 获取依赖信息
   */
  getDependency(name: string): Dependency | undefined {
    return this.dependencies.get(name)
  }

  /**
   * 获取所有依赖
   */
  getAllDependencies(): Dependency[] {
    return Array.from(this.dependencies.values())
  }

  /**
   * 获取有漏洞的依赖
   */
  getVulnerableDependencies(): Dependency[] {
    return Array.from(this.dependencies.values()).filter(dep => dep.vulnerabilities.length > 0)
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<SecurityConfig>): void {
    this.config = { ...this.config, ...config }

    // 如果自动扫描设置发生变化，重新设置定期扫描
    if (config.autoScan !== undefined) {
      this.stopPeriodicScanning()
      if (config.autoScan) {
        this.setupPeriodicScanning()
      }
    }
  }

  /**
   * 添加自定义许可证
   */
  addLicense(license: LicenseInfo): void {
    this.licenses.set(license.spdxId, license)
  }

  /**
   * 导出依赖列表
   */
  exportDependencies(): string {
    const data = {
      dependencies: Array.from(this.dependencies.values()),
      config: this.config,
      exportedAt: Date.now()
    }

    return JSON.stringify(data, null, 2)
  }

  /**
   * 重置管理器
   */
  reset(): void {
    this.stopPeriodicScanning()
    this.dependencies.clear()
    this.config = { ...this.DEFAULT_CONFIG }
    console.log('🔄 依赖安全管理器已重置')
  }
}

// 导出全局实例
export const dependencySecurity = DependencySecurityManager.getInstance()

// 便捷函数
export const {
  initialize,
  triggerScan,
  generateSecurityReport,
  getDependency,
  getAllDependencies,
  getVulnerableDependencies,
  updateConfig,
  addLicense,
  exportDependencies,
  reset
} = dependencySecurity

export type { Vulnerability, Dependency, LicenseInfo, SecurityReport, SecurityConfig }