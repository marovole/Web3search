/**
 * 智能告警系统
 * 提供性能异常检测、错误率监控、业务指标监控和多渠道通知功能
 */

import { captureException, captureMessage } from './sentry'
import { analytics } from './analytics'

interface AlertRule {
  id: string
  name: string
  description: string
  enabled: boolean
  severity: 'low' | 'medium' | 'high' | 'critical'
  type: 'performance' | 'error_rate' | 'business' | 'system'
  conditions: AlertCondition[]
  cooldown: number // 冷却时间（毫秒）
  lastTriggered?: number
}

interface AlertCondition {
  metric: string
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte'
  threshold: number
  duration?: number // 持续时间（毫秒）
}

interface Alert {
  id: string
  ruleId: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  type: 'performance' | 'error_rate' | 'business' | 'system'
  title: string
  message: string
  timestamp: number
  metadata: Record<string, any>
  resolved: boolean
  resolvedAt?: number
}

interface NotificationChannel {
  id: string
  name: string
  type: 'email' | 'slack' | 'sms' | 'webhook' | 'console'
  enabled: boolean
  config: Record<string, any>
  rateLimit?: {
    maxPerHour: number
    currentCount: number
    resetTime: number
  }
}

interface PerformanceMetric {
  name: string
  value: number
  unit: string
  timestamp: number
  context?: Record<string, any>
}

interface BusinessMetric {
  name: string
  value: number
  timestamp: number
  context?: Record<string, any>
}

/**
 * 智能告警管理器
 */
export class AlertManager {
  private static instance: AlertManager
  private rules: Map<string, AlertRule> = new Map()
  private alerts: Map<string, Alert> = new Map()
  private notificationChannels: Map<string, NotificationChannel> = new Map()
  private metricsHistory: Map<string, PerformanceMetric[]> = new Map()
  private businessMetrics: Map<string, BusinessMetric[]> = new Map()
  private isMonitoring = false
  private monitoringInterval?: NodeJS.Timeout

  private readonly METRICS_RETENTION = 24 * 60 * 60 * 1000 // 24小时
  private readonly DEFAULT_COOLDOWN = 5 * 60 * 1000 // 5分钟
  private readonly CHECK_INTERVAL = 30 * 1000 // 30秒

  private constructor() {
    this.initializeDefaultRules()
    this.initializeNotificationChannels()
  }

  /**
   * 获取AlertManager实例（单例模式）
   */
  static getInstance(): AlertManager {
    if (!AlertManager.instance) {
      AlertManager.instance = new AlertManager()
    }
    return AlertManager.instance
  }

  /**
   * 开始监控
   */
  startMonitoring(): void {
    if (this.isMonitoring) {
      return
    }

    this.isMonitoring = true
    this.monitoringInterval = setInterval(() => {
      this.checkAllRules()
    }, this.CHECK_INTERVAL)

    console.log('智能告警系统已启动')
    analytics.trackEvent('alert_monitoring_started', 'system')
  }

  /**
   * 停止监控
   */
  stopMonitoring(): void {
    if (!this.isMonitoring) {
      return
    }

    this.isMonitoring = false
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval)
      this.monitoringInterval = undefined
    }

    console.log('智能告警系统已停止')
    analytics.trackEvent('alert_monitoring_stopped', 'system')
  }

  /**
   * 添加性能指标
   */
  addPerformanceMetric(metric: PerformanceMetric): void {
    const history = this.metricsHistory.get(metric.name) || []
    history.push(metric)

    // 清理过期数据
    const cutoff = Date.now() - this.METRICS_RETENTION
    const validMetrics = history.filter(m => m.timestamp > cutoff)

    this.metricsHistory.set(metric.name, validMetrics)
  }

  /**
   * 添加业务指标
   */
  addBusinessMetric(metric: BusinessMetric): void {
    const history = this.businessMetrics.get(metric.name) || []
    history.push(metric)

    // 清理过期数据
    const cutoff = Date.now() - this.METRICS_RETENTION
    const validMetrics = history.filter(m => m.timestamp > cutoff)

    this.businessMetrics.set(metric.name, validMetrics)
  }

  /**
   * 添加告警规则
   */
  addAlertRule(rule: Omit<AlertRule, 'id'>): string {
    const id = this.generateId()
    const fullRule: AlertRule = {
      id,
      ...rule
    }

    this.rules.set(id, fullRule)
    console.log(`告警规则已添加: ${rule.name}`)
    return id
  }

  /**
   * 移除告警规则
   */
  removeAlertRule(ruleId: string): boolean {
    return this.rules.delete(ruleId)
  }

  /**
   * 获取所有活跃告警
   */
  getActiveAlerts(): Alert[] {
    return Array.from(this.alerts.values()).filter(alert => !alert.resolved)
  }

  /**
   * 获取告警历史
   */
  getAlertHistory(limit: number = 100): Alert[] {
    return Array.from(this.alerts.values())
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit)
  }

  /**
   * 手动解决告警
   */
  resolveAlert(alertId: string, reason?: string): boolean {
    const alert = this.alerts.get(alertId)
    if (!alert || alert.resolved) {
      return false
    }

    alert.resolved = true
    alert.resolvedAt = Date.now()

    if (reason) {
      alert.metadata.resolutionReason = reason
    }

    this.sendNotification(alert, 'resolved')
    analytics.trackEvent('alert_resolved', 'system', alert.type)

    return true
  }

  /**
   * 初始化默认告警规则
   */
  private initializeDefaultRules(): void {
    // 性能异常检测规则
    this.addAlertRule({
      name: '页面响应时间异常',
      description: '页面响应时间超过3秒',
      enabled: true,
      severity: 'medium',
      type: 'performance',
      cooldown: this.DEFAULT_COOLDOWN,
      conditions: [
        {
          metric: 'page_load_time',
          operator: 'gt',
          threshold: 3000,
          duration: 60000 // 持续1分钟
        }
      ]
    })

    // 错误率监控规则
    this.addAlertRule({
      name: 'JavaScript错误率过高',
      description: 'JavaScript错误率超过5%',
      enabled: true,
      severity: 'high',
      type: 'error_rate',
      cooldown: this.DEFAULT_COOLDOWN,
      conditions: [
        {
          metric: 'js_error_rate',
          operator: 'gt',
          threshold: 0.05,
          duration: 300000 // 持续5分钟
        }
      ]
    })

    // 业务指标监控规则
    this.addAlertRule({
      name: '搜索成功率过低',
      description: '搜索成功率低于80%',
      enabled: true,
      severity: 'medium',
      type: 'business',
      cooldown: this.DEFAULT_COOLDOWN,
      conditions: [
        {
          metric: 'search_success_rate',
          operator: 'lt',
          threshold: 0.8,
          duration: 600000 // 持续10分钟
        }
      ]
    })

    // 系统监控规则
    this.addAlertRule({
      name: 'API响应时间异常',
      description: 'API平均响应时间超过2秒',
      enabled: true,
      severity: 'high',
      type: 'system',
      cooldown: this.DEFAULT_COOLDOWN,
      conditions: [
        {
          metric: 'api_response_time',
          operator: 'gt',
          threshold: 2000,
          duration: 120000 // 持续2分钟
        }
      ]
    })
  }

  /**
   * 初始化通知渠道
   */
  private initializeNotificationChannels(): void {
    // 默认控制台通知渠道
    this.notificationChannels.set('console', {
      id: 'console',
      name: '控制台日志',
      type: 'webhook',
      enabled: true,
      config: {
        endpoint: 'console'
      }
    })
  }

  /**
   * 检查所有告警规则
   */
  private checkAllRules(): void {
    const now = Date.now()

    for (const rule of this.rules.values()) {
      if (!rule.enabled) continue

      // 检查冷却时间
      if (rule.lastTriggered && (now - rule.lastTriggered) < rule.cooldown) {
        continue
      }

      // 检查规则条件
      if (this.evaluateRule(rule)) {
        this.triggerAlert(rule)
        rule.lastTriggered = now
      }
    }
  }

  /**
   * 评估告警规则
   */
  private evaluateRule(rule: AlertRule): boolean {
    return rule.conditions.every(condition => this.evaluateCondition(condition))
  }

  /**
   * 评估单个条件
   */
  private evaluateCondition(condition: AlertCondition): boolean {
    const now = Date.now()
    let recentMetrics: (PerformanceMetric | BusinessMetric)[] = []

    if (this.metricsHistory.has(condition.metric)) {
      recentMetrics = this.metricsHistory.get(condition.metric)!.filter(
        m => m.timestamp > now - (condition.duration || this.CHECK_INTERVAL)
      )
    }

    if (this.businessMetrics.has(condition.metric)) {
      recentMetrics = this.businessMetrics.get(condition.metric)!.filter(
        m => m.timestamp > now - (condition.duration || this.CHECK_INTERVAL)
      )
    }

    if (recentMetrics.length === 0) {
      return false
    }

    const latestValue = recentMetrics[recentMetrics.length - 1].value

    switch (condition.operator) {
      case 'gt':
        return latestValue > condition.threshold
      case 'gte':
        return latestValue >= condition.threshold
      case 'lt':
        return latestValue < condition.threshold
      case 'lte':
        return latestValue <= condition.threshold
      case 'eq':
        return latestValue === condition.threshold
      default:
        return false
    }
  }

  /**
   * 触发告警
   */
  private triggerAlert(rule: AlertRule): void {
    const alert: Alert = {
      id: this.generateId(),
      ruleId: rule.id,
      severity: rule.severity,
      type: rule.type,
      title: rule.name,
      message: rule.description,
      timestamp: Date.now(),
      metadata: {
        rule: rule.name,
        triggeredConditions: rule.conditions
      },
      resolved: false
    }

    this.alerts.set(alert.id, alert)

    // 发送通知
    this.sendNotification(alert, 'triggered')

    // 记录到Sentry
    captureException(new Error(`Alert triggered: ${rule.name}`), {
      alertId: alert.id,
      severity: rule.severity,
      type: rule.type
    })

    // 记录到Analytics
    analytics.trackEvent('alert_triggered', 'system', rule.type)

    console.warn(`🚨 告警触发: ${rule.name} (${rule.severity})`)
  }

  /**
   * 发送通知
   */
  private sendNotification(alert: Alert, action: 'triggered' | 'resolved'): void {
    const channels = Array.from(this.notificationChannels.values()).filter(c => c.enabled)

    for (const channel of channels) {
      if (this.checkRateLimit(channel)) {
        this.sendNotificationToChannel(channel, alert, action)
      }
    }
  }

  /**
   * 检查通知频率限制
   */
  private checkRateLimit(channel: NotificationChannel): boolean {
    if (!channel.rateLimit) {
      return true
    }

    const now = Date.now()
    const { maxPerHour, currentCount, resetTime } = channel.rateLimit

    // 重置计数器
    if (now > resetTime) {
      channel.rateLimit.currentCount = 0
      channel.rateLimit.resetTime = now + 60 * 60 * 1000
    }

    if (currentCount >= maxPerHour) {
      return false
    }

    channel.rateLimit.currentCount++
    return true
  }

  /**
   * 发送通知到特定渠道
   */
  private sendNotificationToChannel(
    channel: NotificationChannel,
    alert: Alert,
    action: 'triggered' | 'resolved'
  ): void {
    const message = action === 'triggered'
      ? `🚨 告警触发: ${alert.title} - ${alert.message}`
      : `✅ 告警解决: ${alert.title}`

    switch (channel.type) {
      case 'console':
        console.log(`[${channel.name}] ${message}`)
        break
      case 'webhook':
        if (channel.config.endpoint === 'console') {
          console.log(`[${channel.name}] ${message}`)
        }
        break
      // 可以扩展其他通知渠道
      default:
        console.log(`[${channel.name}] ${message}`)
    }
  }

  /**
   * 生成唯一ID
   */
  private generateId(): string {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 获取系统健康状态
   */
  getSystemHealth(): {
    status: 'healthy' | 'warning' | 'critical'
    activeAlerts: number
    metrics: Record<string, any>
  } {
    const activeAlerts = this.getActiveAlerts()
    const criticalAlerts = activeAlerts.filter(a => a.severity === 'critical')
    const highAlerts = activeAlerts.filter(a => a.severity === 'high')

    let status: 'healthy' | 'warning' | 'critical' = 'healthy'
    if (criticalAlerts.length > 0) {
      status = 'critical'
    } else if (highAlerts.length > 0 || activeAlerts.length > 3) {
      status = 'warning'
    }

    return {
      status,
      activeAlerts: activeAlerts.length,
      metrics: {
        totalRules: this.rules.size,
        enabledRules: Array.from(this.rules.values()).filter(r => r.enabled).length,
        notificationChannels: this.notificationChannels.size,
        uptime: this.isMonitoring ? Date.now() : 0
      }
    }
  }
}

// 导出全局实例
export const alertManager = AlertManager.getInstance()

// 便捷函数
export const {
  startMonitoring,
  stopMonitoring,
  addPerformanceMetric,
  addBusinessMetric,
  addAlertRule,
  removeAlertRule,
  getActiveAlerts,
  getAlertHistory,
  resolveAlert,
  getSystemHealth
} = alertManager

export type { AlertRule, Alert, NotificationChannel, PerformanceMetric, BusinessMetric }