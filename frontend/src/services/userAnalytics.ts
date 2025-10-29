/**
 * 用户行为分析服务
 * 提供用户行为数据收集、分析和追踪功能
 */

import { analytics } from './analytics'

interface UserEvent {
  id: string
  timestamp: number
  sessionId: string
  userId?: string
  eventType: 'page_view' | 'search' | 'interaction' | 'performance' | 'error' | 'engagement' | 'feature_usage' | 'analytics'
  eventName: string
  properties: Record<string, any>
}

interface UserSession {
  id: string
  startTime: number
  endTime?: number
  duration?: number
  userId?: string
  deviceInfo: DeviceInfo
  pageInfo: PageInfo
  events: UserEvent[]
  searchCount: number
  featureUsage: Record<string, FeatureUsage>
}

interface DeviceInfo {
  userAgent: string
  platform: string
  language: string
  screenResolution: string
  viewport: string
  timezone: string
  online: boolean
}

interface PageInfo {
  referrer: string
  landingPage: string
  exitPage?: string
  pageViews: number
  timeOnPage: number
  scrollDepth: number
  pagePath?: string
}

interface SearchEvent {
  query: string
  type: 'quick' | 'deep'
  resultCount?: number
  responseTime: number
  success: boolean
  timestamp: number
}

interface FeatureUsage {
  name: string
  firstUsed: number
  lastUsed: number
  usageCount: number
  totalUsageTime: number
}

/**
 * 用户分析管理器
 */
export class UserAnalytics {
  private static instance: UserAnalytics
  private currentSession: UserSession | null = null
  private eventQueue: UserEvent[] = []
  private sessionTimeout: NodeJS.Timeout | null = null
  private isTracking = false

  private readonly SESSION_TIMEOUT = 30 * 60 * 1000 // 30分钟
  private readonly MAX_QUEUE_SIZE = 1000

  private constructor() {
    this.initializeEventListeners()
  }

  /**
   * 获取用户分析实例（单例模式）
   */
  static getInstance(): UserAnalytics {
    if (!UserAnalytics.instance) {
      UserAnalytics.instance = new UserAnalytics()
    }
    return UserAnalytics.instance
  }

  /**
   * 初始化追踪
   */
  startTracking(userId?: string): void {
    if (this.isTracking) {
      return
    }

    this.isTracking = true
    this.createSession(userId)
    this.setupSessionTimeout()

    console.log('User analytics tracking started')
  }

  /**
   * 停止追踪
   */
  stopTracking(): void {
    if (!this.isTracking) {
      return
    }

    this.isTracking = false

    if (this.currentSession) {
      this.endSession()
    }

    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout)
      this.sessionTimeout = null
    }

    // 发送队列中的事件
    this.flushEventQueue()

    console.log('User analytics tracking stopped')
  }

  /**
   * 创建新会话
   */
  private createSession(userId?: string): void {
    const sessionId = this.generateSessionId()
    const now = Date.now()

    this.currentSession = {
      id: sessionId,
      startTime: now,
      userId,
      deviceInfo: this.getDeviceInfo(),
      pageInfo: this.getPageInfo(),
      events: [],
      searchCount: 0,
      featureUsage: {},
    }

    // 触发会话开始事件
    analytics.trackSessionStart(sessionId)
    this.trackEvent('session_start', 'engagement', {
      session_id: sessionId,
      user_id: userId,
      device_type: this.currentSession.deviceInfo.platform,
      referrer: this.currentSession.pageInfo.referrer,
    })
  }

  /**
   * 结束当前会话
   */
  private endSession(): void {
    if (!this.currentSession) {
      return
    }

    const now = Date.now()
    this.currentSession.endTime = now
    this.currentSession.duration = now - this.currentSession.startTime

    // 触发会话结束事件
    analytics.trackSessionEnd(
      this.currentSession.id,
      this.currentSession.duration
    )

    // 分析会话数据
    this.analyzeSession()
  }

  /**
   * 设置会话超时
   */
  private setupSessionTimeout(): void {
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout)
    }

    this.sessionTimeout = setTimeout(() => {
      this.endSession()
      this.createSession() // 创建新会话
      this.setupSessionTimeout()
    }, this.SESSION_TIMEOUT)
  }

  /**
   * 追踪用户事件
   */
  trackEvent(
    eventName: string,
    eventType: UserEvent['eventType'],
    properties: Record<string, any> = {}
  ): void {
    if (!this.isTracking || !this.currentSession) {
      return
    }

    const event: UserEvent = {
      id: this.generateEventId(),
      timestamp: Date.now(),
      sessionId: this.currentSession.id,
      userId: this.currentSession.userId,
      eventType,
      eventName,
      properties: {
        ...properties,
        session_id: this.currentSession.id,
        user_id: this.currentSession.userId,
      },
    }

    // 添加到当前会话
    this.currentSession.events.push(event)

    // 添加到队列等待发送
    this.eventQueue.push(event)

    // 如果队列过大，刷新队列
    if (this.eventQueue.length >= this.MAX_QUEUE_SIZE) {
      this.flushEventQueue()
    }

    // 发送到Google Analytics
    this.sendEventToGA(event)
  }

  /**
   * 追踪页面浏览
   */
  trackPageView(pagePath?: string, pageTitle?: string): void {
    const properties: Record<string, any> = {
      page_path: pagePath || window.location.pathname,
      page_title: pageTitle || document.title,
    }

    // 更新页面信息
    if (this.currentSession) {
      this.currentSession.pageInfo.pageViews++
      this.currentSession.pageInfo.timeOnPage = 0
      this.currentSession.pageInfo.pagePath = pagePath || window.location.pathname
    }

    this.trackEvent('page_view', 'page_view', properties)
    analytics.trackPageView({
      page_path: pagePath,
      page_title: pageTitle,
    })
  }

  /**
   * 追踪搜索行为
   */
  trackSearch(search: SearchEvent): void {
    if (!this.currentSession) {
      return
    }

    this.currentSession.searchCount++

    const properties = {
      search_id: this.generateEventId(),
      search_query: search.query,
      search_type: search.type,
      search_success: search.success,
      response_time: search.responseTime,
      result_count: search.resultCount,
    }

    this.trackEvent('search', 'search', properties)
    analytics.trackSearch(search.query, search.type, search.resultCount)
  }

  /**
   * 追踪功能使用
   */
  trackFeatureUsage(featureName: string, action: string = 'use', duration?: number): void {
    if (!this.currentSession) {
      return
    }

    const now = Date.now()
    const currentUsage = this.currentSession.featureUsage[featureName] || {
      name: featureName,
      firstUsed: now,
      lastUsed: now,
      usageCount: 0,
      totalUsageTime: 0,
    }

    currentUsage.lastUsed = now
    currentUsage.usageCount++
    if (duration) {
      currentUsage.totalUsageTime += duration
    }

    this.currentSession.featureUsage[featureName] = currentUsage

    this.trackEvent('feature_usage', 'interaction', {
      feature_name: featureName,
      action,
      usage_count: currentUsage.usageCount,
      usage_duration: duration,
    })

    analytics.trackFeature(featureName, action)
  }

  /**
   * 追踪性能指标
   */
  trackPerformance(name: string, value: number, unit?: string): void {
    this.trackEvent('performance', 'performance', {
      metric_name: name,
      metric_value: value,
      metric_unit: unit,
    })

    analytics.trackPerformance(name, value, unit)
  }

  /**
   * 追踪错误
   */
  trackError(error: Error, context?: string): void {
    const properties = {
      error_type: error.constructor.name,
      error_message: error.message,
      error_context: context,
      error_stack: error.stack,
    }

    this.trackEvent('error', 'error', properties)
    analytics.trackError(error, context)
  }

  /**
   * 生成会话ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 生成事件ID
   */
  private generateEventId(): string {
    return `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 获取设备信息
   */
  private getDeviceInfo(): DeviceInfo {
    return {
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      screenResolution: `${screen.width}x${screen.height}`,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      online: navigator.onLine,
    }
  }

  /**
   * 获取页面信息
   */
  private getPageInfo(): PageInfo {
    return {
      referrer: document.referrer || 'direct',
      landingPage: window.location.pathname,
      pageViews: 0,
      timeOnPage: 0,
      scrollDepth: 0,
    }
  }

  /**
   * 发送事件到Google Analytics
   */
  private sendEventToGA(event: UserEvent): void {
    if (!analytics.isReady()) {
      return
    }

    switch (event.eventType) {
      case 'search':
        // GA事件会在trackSearch中处理
        break
      case 'feature_usage':
        // GA事件会在trackFeature中处理
        break
      case 'performance':
        // GA事件会在trackPerformance中处理
        break
      case 'error':
        // GA事件会在trackError中处理
        break
      default:
        analytics.trackEvent(event.eventName, event.eventType, event.properties.label, event.properties.value, event.properties)
    }
  }

  /**
   * 刷新事件队列
   */
  private flushEventQueue(): void {
    if (this.eventQueue.length === 0) {
      return
    }

    // 这里可以发送到后端分析服务
    // 目前只是清空队列
    console.log(`Flushing ${this.eventQueue.length} events to backend`)
    this.eventQueue = []
  }

  /**
   * 分析会话数据
   */
  private analyzeSession(): void {
    if (!this.currentSession) {
      return
    }

    const session = this.currentSession

    // 计算关键指标
    const metrics = {
      totalEvents: session.events.length,
      avgSessionTime: session.duration || 0,
      searchRate: session.searchCount > 0 ? 1 : 0,
      featureEngagement: Object.keys(session.featureUsage).length,
      errorRate: 0, // 从events中计算
    }

    // 计算错误率
    const errorEvents = session.events.filter(e => e.eventType === 'error')
    metrics.errorRate = errorEvents.length / session.events.length

    // 发送会话分析到分析平台
    this.trackEvent('session_analyzed', 'analytics', {
      session_duration: session.duration,
      total_events: metrics.totalEvents,
      search_count: session.searchCount,
      error_rate: metrics.errorRate,
      feature_engagement: metrics.featureEngagement,
    })
  }

  /**
   * 初始化事件监听器
   */
  private initializeEventListeners(): void {
    // 监听页面可见性变化
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.stopTracking()
      } else {
        this.startTracking()
      }
    })

    // 监听页面卸载
    window.addEventListener('beforeunload', () => {
      this.stopTracking()
    })

    // 监听页面焦点变化
    window.addEventListener('focus', () => {
      if (this.isTracking && this.currentSession) {
        this.trackEvent('focus', 'engagement')
      }
    })

    window.addEventListener('blur', () => {
      if (this.isTracking && this.currentSession) {
        this.trackEvent('blur', 'engagement')
      }
    })
  }

  /**
   * 获取当前会话信息
   */
  getCurrentSession(): UserSession | null {
    return this.currentSession
  }

  /**
   * 获取会话统计
   */
  getSessionStats(): {
    sessionId: string
    duration: number
    eventCount: number
    searchCount: number
    featureCount: number
    errorCount: number
  } | null {
    if (!this.currentSession) {
      return null
    }

    const session = this.currentSession
    const now = Date.now()
    const duration = now - session.startTime

    return {
      sessionId: session.id,
      duration,
      eventCount: session.events.length,
      searchCount: session.searchCount,
      featureCount: Object.keys(session.featureUsage).length,
      errorCount: session.events.filter(e => e.eventType === 'error').length,
    }
  }
}

// 导出全局实例
export const userAnalytics = UserAnalytics.getInstance()

// 便捷函数
export const {
  startTracking,
  stopTracking,
  trackEvent,
  trackPageView,
  trackSearch,
  trackFeatureUsage,
  trackPerformance,
  trackError,
  getCurrentSession,
  getSessionStats,
} = userAnalytics

export type { UserEvent, UserSession, SearchEvent, FeatureUsage, DeviceInfo, PageInfo }