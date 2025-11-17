/**
 * 监控系统统一入口
 * 整合Sentry、Google Analytics、用户行为分析和智能告警系统
 */

import { initSentry, captureException, captureMessage, startSpan } from './sentry'
import { initAnalytics, analytics } from './analytics'
import { startTracking, trackEvent, trackPerformance, trackError } from './userAnalytics'
import {
  alertManager,
  startMonitoring,
  addPerformanceMetric,
  addBusinessMetric
} from './alertManager'
import { getEnvConfig } from '../utils/env'

interface MonitoringConfig {
  sentry?: {
    dsn?: string
    environment?: string
    enabled?: boolean
  }
  analytics?: {
    measurementId?: string
    enabled?: boolean
    consent?: boolean
  }
  userAnalytics?: {
    enabled?: boolean
    trackInteractions?: boolean
  }
  alerts?: {
    enabled?: boolean
    autoStart?: boolean
  }
}

/**
 * 监控系统管理器
 */
export class MonitoringManager {
  private static instance: MonitoringManager
  private isInitialized = false
  private config: MonitoringConfig = {}

  private constructor() {}

  /**
   * 获取MonitoringManager实例（单例模式）
   */
  static getInstance(): MonitoringManager {
    if (!MonitoringManager.instance) {
      MonitoringManager.instance = new MonitoringManager()
    }
    return MonitoringManager.instance
  }

  /**
   * 初始化监控系统
   */
  async initialize(config?: MonitoringConfig): Promise<void> {
    if (this.isInitialized) {
      console.warn('监控系统已经初始化')
      return
    }

    this.config = { ...this.getDefaultConfig(), ...config }

    try {
      // 初始化Sentry错误监控
      await this.initializeSentry()

      // 初始化Google Analytics
      await this.initializeAnalytics()

      // 初始化用户行为分析
      await this.initializeUserAnalytics()

      // 初始化智能告警系统
      await this.initializeAlerts()

      this.setupPerformanceMonitoring()
      this.setupErrorTracking()
      this.setupPageTracking()

      this.isInitialized = true
      console.log('✅ 监控系统初始化完成')

    } catch (error) {
      console.error('❌ 监控系统初始化失败:', error)
      captureException(error as Error, { context: 'monitoring_initialization' })
    }
  }

  /**
   * 获取默认配置
   */
  private getDefaultConfig(): MonitoringConfig {
    const envConfig = getEnvConfig()

    return {
      sentry: {
        dsn: envConfig.SENTRY_DSN,
        environment: envConfig.ENVIRONMENT,
        enabled: envConfig.ENABLE_SENTRY
      },
      analytics: {
        measurementId: envConfig.GA_MEASUREMENT_ID,
        enabled: envConfig.ENABLE_ANALYTICS,
        consent: false // 需要用户同意
      },
      userAnalytics: {
        enabled: true,
        trackInteractions: true
      },
      alerts: {
        enabled: true,
        autoStart: true
      }
    }
  }

  /**
   * 初始化Sentry
   */
  private async initializeSentry(): Promise<void> {
    if (this.config.sentry?.enabled && this.config.sentry?.dsn) {
      initSentry()
      console.log('🔧 Sentry错误监控已初始化')
    } else {
      console.log('ℹ️ Sentry错误监控已禁用 (DSN未配置或已禁用)')
    }
  }

  /**
   * 初始化Google Analytics
   */
  private async initializeAnalytics(): Promise<void> {
    if (this.config.analytics?.enabled && this.config.analytics?.measurementId) {
      initAnalytics({
        measurementId: this.config.analytics.measurementId,
        enableConsent: true,
        debugMode: getEnvConfig().DEBUG_MODE
      })

      if (this.config.analytics.consent) {
        analytics.setConsent(true)
      }

      console.log('📊 Google Analytics已初始化')
    } else {
      console.log('ℹ️ Google Analytics已禁用 (Measurement ID未配置或已禁用)')
    }
  }

  /**
   * 初始化用户行为分析
   */
  private async initializeUserAnalytics(): Promise<void> {
    if (this.config.userAnalytics?.enabled) {
      startTracking()
      console.log('👤 用户行为分析已启动')
    }
  }

  /**
   * 初始化智能告警系统
   */
  private async initializeAlerts(): Promise<void> {
    if (this.config.alerts?.enabled) {
      if (this.config.alerts.autoStart) {
        startMonitoring()
        console.log('🚨 智能告警系统已启动')
      }
    }
  }

  /**
   * 设置性能监控
   */
  private setupPerformanceMonitoring(): void {
    // 监控页面加载性能
    if (typeof window !== 'undefined') {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
          if (navigation) {
            const loadTime = navigation.loadEventEnd - navigation.fetchStart

            // 记录到用户行为分析
            trackPerformance('page_load_time', loadTime, 'ms')

            // 记录到告警系统
            addPerformanceMetric({
              name: 'page_load_time',
              value: loadTime,
              unit: 'ms',
              timestamp: Date.now(),
              context: {
                url: window.location.pathname,
                userAgent: navigator.userAgent
              }
            })

            // Sentry性能监控
            startSpan('page_load', 'navigation')
          }
        }, 0)
      })

      // 监控Core Web Vitals
      this.observeCoreWebVitals()
    }
  }

  /**
   * 监控Core Web Vitals
   */
  private observeCoreWebVitals(): void {
    // 监控LCP (Largest Contentful Paint)
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const lastEntry = entries[entries.length - 1] as any

          if (lastEntry && lastEntry.startTime) {
            const lcp = Math.round(lastEntry.startTime)

            trackPerformance('lcp', lcp, 'ms')
            addPerformanceMetric({
              name: 'lcp',
              value: lcp,
              unit: 'ms',
              timestamp: Date.now()
            })
          }
        })

        observer.observe({ entryTypes: ['largest-contentful-paint'] })
      } catch (error) {
        console.warn('LCP监控初始化失败:', error)
      }
    }
  }

  /**
   * 设置错误追踪
   */
  private setupErrorTracking(): void {
    // 全局JavaScript错误处理
    window.addEventListener('error', (event) => {
      const error = event.error || new Error(event.message)

      // 记录到Sentry
      captureException(error, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        context: 'javascript_error'
      })

      // 记录到用户行为分析
      trackError(error, 'javascript_error')

      // 记录到告警系统
      addBusinessMetric({
        name: 'js_error_count',
        value: 1,
        timestamp: Date.now(),
        context: {
          error: error.message,
          url: window.location.pathname
        }
      })
    })

    // Promise拒绝处理
    window.addEventListener('unhandledrejection', (event) => {
      const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))

      captureException(error, {
        context: 'unhandled_promise_rejection'
      })

      trackError(error, 'promise_rejection')
    })

    // 网络错误监控
    this.setupNetworkErrorTracking()
  }

  /**
   * 设置网络错误追踪
   */
  private setupNetworkErrorTracking(): void {
    // 拦截fetch请求
    const originalFetch = window.fetch
    window.fetch = async (...args) => {
      const startTime = Date.now()
      const url = typeof args[0] === 'string' ? args[0] : (args[0] as any).url || (args[0] as URL).toString()

      try {
        const response = await originalFetch(...args)
        const duration = Date.now() - startTime

        // 记录API性能
        if (url.includes('/api/')) {
          trackPerformance(`api_request_${url}`, duration, 'ms')
          addPerformanceMetric({
            name: 'api_response_time',
            value: duration,
            unit: 'ms',
            timestamp: Date.now(),
            context: {
              url,
              status: response.status
            }
          })
        }

        return response
      } catch (error) {
        const duration = Date.now() - startTime

        // 记录网络错误
        captureException(error as Error, {
          context: 'network_error',
          url,
          duration
        })

        trackError(error as Error, 'network_error')

        addBusinessMetric({
          name: 'network_error_count',
          value: 1,
          timestamp: Date.now(),
          context: { url, duration }
        })

        throw error
      }
    }
  }

  /**
   * 设置页面追踪
   */
  private setupPageTracking(): void {
    // 页面访问追踪
    if (this.config.analytics?.enabled) {
      analytics.trackPageView({
        page_path: window.location.pathname,
        page_title: document.title
      })
    }

    // 路由变化监控
    this.observeRouteChanges()
  }

  /**
   * 监控路由变化
   */
  private observeRouteChanges(): void {
    let currentPath = window.location.pathname

    // 监控history API
    const originalPushState = history.pushState
    const originalReplaceState = history.replaceState

    history.pushState = function(...args) {
      const result = originalPushState.apply(this, args)
      setTimeout(() => checkRouteChange(), 0)
      return result
    }

    history.replaceState = function(...args) {
      const result = originalReplaceState.apply(this, args)
      setTimeout(() => checkRouteChange(), 0)
      return result
    }

    // 监控popstate事件
    window.addEventListener('popstate', () => {
      setTimeout(checkRouteChange, 0)
    })

    function checkRouteChange() {
      if (window.location.pathname !== currentPath) {
        currentPath = window.location.pathname

        // 记录页面访问
        analytics.trackPageView({
          page_path: currentPath,
          page_title: document.title
        })

        // 记录路由变化事件
        trackEvent('route_change', 'page_view', {
          from: currentPath,
          to: window.location.pathname
        })
      }
    }
  }

  /**
   * 设置用户同意
   */
  setUserConsent(analyticsConsent: boolean, trackingConsent?: boolean): void {
    if (this.config.analytics?.enabled) {
      analytics.setConsent(analyticsConsent)
    }

    if (trackingConsent && this.config.userAnalytics?.enabled) {
      startTracking()
    }
  }

  /**
   * 记录自定义事件
   */
  trackCustomEvent(
    name: string,
    category: string,
    properties?: Record<string, any>
  ): void {
    // Google Analytics
    analytics.trackEvent(name, category, properties?.label, properties?.value)

    // 用户行为分析
    trackEvent(name, category as any, properties)

    // Sentry（如果是重要事件）
    if (properties?.important) {
      captureMessage(`Custom event: ${name}`, 'info', properties)
    }
  }

  /**
   * 记录搜索事件
   */
  trackSearchEvent(query: string, type: 'quick' | 'deep', resultCount?: number, responseTime?: number): void {
    // Google Analytics
    analytics.trackSearch(query, type, resultCount)

    // 用户行为分析
    trackEvent('search', 'search', {
      query,
      type,
      resultCount,
      responseTime
    })

    // 业务指标
    addBusinessMetric({
      name: 'search_success_rate',
      value: resultCount && resultCount > 0 ? 1 : 0,
      timestamp: Date.now(),
      context: { type, queryLength: query.length }
    })
  }

  /**
   * 记录功能使用
   */
  trackFeatureUsage(featureName: string, action?: string, duration?: number): void {
    // Google Analytics
    analytics.trackFeature(featureName, action)

    // 用户行为分析
    trackEvent('feature_used', 'interaction', {
      feature: featureName,
      action,
      duration
    })

    // 告警系统业务指标
    addBusinessMetric({
      name: 'feature_usage',
      value: 1,
      timestamp: Date.now(),
      context: { featureName, action }
    })
  }

  /**
   * 获取监控状态
   */
  getMonitoringStatus(): {
    initialized: boolean
    components: Record<string, boolean>
    health: any
  } {
    return {
      initialized: this.isInitialized,
      components: {
        sentry: !!this.config.sentry?.enabled,
        analytics: !!this.config.analytics?.enabled,
        userAnalytics: !!this.config.userAnalytics?.enabled,
        alerts: !!this.config.alerts?.enabled
      },
      health: alertManager.getSystemHealth()
    }
  }

  /**
   * 重置监控系统
   */
  reset(): void {
    alertManager.stopMonitoring()
    this.isInitialized = false
    this.config = {}
    console.log('监控系统已重置')
  }
}

// 导出全局实例
export const monitoring = MonitoringManager.getInstance()

// 便捷函数
export const {
  initialize,
  setUserConsent,
  trackCustomEvent,
  trackSearchEvent,
  trackFeatureUsage,
  getMonitoringStatus,
  reset
} = monitoring

export type { MonitoringConfig }