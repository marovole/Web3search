/**
 * Google Analytics 4 服务模块
 * 提供用户行为追踪和分析功能
 */

declare global {
  interface Window {
    gtag: (command: string, ...args: any[]) => void
    dataLayer: any[]
  }
}

interface AnalyticsConfig {
  measurementId: string
  enableConsent: boolean
  debugMode: boolean
  anonymizeIp: boolean
  cookieFlags: string
}

interface GtagEvent {
  action: string
  category: string
  label?: string
  value?: number
  custom_parameters?: Record<string, any>
}

interface PageViewData {
  page_title?: string
  page_location?: string
  page_path?: string
  custom_parameters?: Record<string, any>
}

/**
 * Google Analytics 4 管理类
 */
export class GoogleAnalytics {
  private static instance: GoogleAnalytics
  private config: AnalyticsConfig
  private isInitialized = false
  private consent = false

  private constructor() {
    // 默认配置
    this.config = {
      measurementId: import.meta.env.VITE_GA_MEASUREMENT_ID || '',
      enableConsent: true,
      debugMode: import.meta.env.NODE_ENV === 'development',
      anonymizeIp: true,
      cookieFlags: 'G1', // GDPR合规
    }
  }

  /**
   * 获取Analytics实例（单例模式）
   */
  static getInstance(): GoogleAnalytics {
    if (!GoogleAnalytics.instance) {
      GoogleAnalytics.instance = new GoogleAnalytics()
    }
    return GoogleAnalytics.instance
  }

  /**
   * 初始化Google Analytics
   */
  initialize(config?: Partial<AnalyticsConfig>): void {
    if (this.isInitialized) {
      console.warn('Google Analytics already initialized')
      return
    }

    // 合并配置
    this.config = { ...this.config, ...config }

    if (!this.config.measurementId) {
      console.warn('Google Analytics measurement ID not provided')
      return
    }

    // 检查用户同意
    if (!this.config.enableConsent || this.getConsent()) {
      this.consent = true
      this.loadGtag()
      this.configureGtag()
      this.isInitialized = true
      console.log('Google Analytics initialized with ID:', this.config.measurementId)
    }
  }

  /**
   * 加载gtag脚本
   */
  private loadGtag(): void {
    if (typeof window === 'undefined') {
      return
    }

    // 创建gtag函数
    window.dataLayer = window.dataLayer || []
    window.gtag = function(...args: any[]) {
      window.dataLayer.push(arguments)
    }

    // 设置初始配置
    window.gtag('js', new Date())
    window.gtag('config', this.config.measurementId, {
      debug_mode: this.config.debugMode,
      anonymize_ip: this.config.anonymizeIp,
      cookie_flags: this.config.cookieFlags,
      send_page_view: false, // 手动控制页面浏览
    })
  }

  /**
   * 配置gtag设置
   */
  private configureGtag(): void {
    if (!window.gtag) return

    // 设置默认配置
    window.gtag('set', {
      page_title: document.title,
      page_location: window.location.href,
      custom_map: {
        custom_parameter_1: 'app_version',
        custom_parameter_2: 'user_type',
      },
    })

    // 发送用户同意事件
    if (this.consent) {
      this.trackEvent('consent', 'analytics', 'granted')
    }
  }

  /**
   * 设置用户同意
   */
  setConsent(granted: boolean): void {
    this.consent = granted

    // 保存同意状态
    localStorage.setItem('analytics_consent', granted.toString())

    if (granted && !this.isInitialized) {
      this.initialize()
    } else if (!granted && this.isInitialized) {
      // 用户撤回同意时，禁用追踪
      this.disable()
    }

    // 触发同意变更事件
    this.trackEvent('consent', 'analytics', granted ? 'granted' : 'denied')
  }

  /**
   * 获取用户同意状态
   */
  getConsent(): boolean {
    if (!this.config.enableConsent) {
      return true // 如果不需要同意，默认同意
    }

    const stored = localStorage.getItem('analytics_consent')
    if (stored !== null) {
      return stored === 'true'
    }

    // 默认未同意，需要用户明确同意
    return false
  }

  /**
   * 禁用追踪
   */
  disable(): void {
    if (window.gtag) {
      window.gtag('config', this.config.measurementId, {
        send_page_view: false,
        allow_google_signals: false,
      })
    }
  }

  /**
   * 追踪页面浏览
   */
  trackPageView(data?: PageViewData): void {
    if (!this.isInitialized || !this.consent) {
      return
    }

    if (window.gtag) {
      window.gtag('event', 'page_view', {
        page_title: data?.page_title || document.title,
        page_location: data?.page_location || window.location.href,
        page_path: data?.page_path || window.location.pathname,
        ...data?.custom_parameters,
      })
    }
  }

  /**
   * 追踪自定义事件
   */
  trackEvent(action: string, category: string, label?: string, value?: number, customParameters?: Record<string, any>): void {
    if (!this.isInitialized || !this.consent) {
      return
    }

    if (window.gtag) {
      window.gtag('event', action, {
        event_category: category,
        event_label: label,
        value: value,
        custom_parameters: customParameters,
      })
    }
  }

  /**
   * 追踪搜索行为
   */
  trackSearch(query: string, searchType: 'quick' | 'deep', resultCount?: number): void {
    this.trackEvent('search', searchType, query, resultCount, {
      search_type: searchType,
      result_count: resultCount,
      query_length: query.length,
    })
  }

  /**
   * 追踪用户会话
   */
  trackSessionStart(sessionId: string): void {
    this.trackEvent('session_start', 'engagement', sessionId)
  }

  trackSessionEnd(sessionId: string, duration: number): void {
    this.trackEvent('session_end', 'engagement', sessionId, duration, {
      session_duration: duration,
    })
  }

  /**
   * 追踪功能使用
   */
  trackFeature(featureName: string, action: string = 'used'): void {
    this.trackEvent(action, 'feature', featureName)
  }

  /**
   * 追踪错误
   */
  trackError(error: Error, context?: string): void {
    this.trackEvent('error', 'system', context || 'unknown', 1, {
      error_name: error.name,
      error_message: error.message,
      error_stack: error.stack,
    })
  }

  /**
   * 追踪性能指标
   */
  trackPerformance(name: string, value: number, unit: string = 'ms'): void {
    this.trackEvent('timing', 'performance', name, value, {
      custom_parameter_1: name,
      custom_parameter_2: unit,
    })
  }

  /**
   * 设置用户属性
   */
  setUserProperty(property: string, value: string): void {
    if (!this.isInitialized || !this.consent || !window.gtag) {
      return
    }

    window.gtag('set', 'user_properties', {
      [property]: value,
    })
  }

  /**
   * 设置用户ID
   */
  setUserId(userId: string): void {
    if (!this.isInitialized || !this.consent || !window.gtag) {
      return
    }

    window.gtag('config', this.config.measurementId, {
      user_id: userId,
    })
  }

  /**
   * 发送自定义维度和指标
   */
  sendCustomDimensions(dimensions: Record<string, any>, metrics?: Record<string, number>): void {
    if (!this.isInitialized || !this.consent || !window.gtag) {
      return
    }

    window.gtag('set', {
      ...dimensions,
      ...metrics,
    })
  }

  /**
   * 检查是否已初始化
   */
  isReady(): boolean {
    return this.isInitialized && this.consent
  }
}

// 导出全局实例
export const analytics = GoogleAnalytics.getInstance()

// 便捷函数
export const {
  initialize: initAnalytics,
  setConsent,
  trackPageView,
  trackEvent,
  trackSearch,
  trackSessionStart,
  trackSessionEnd,
  trackFeature,
  trackError,
  trackPerformance,
  setUserProperty,
  setUserId,
  sendCustomDimensions,
  isReady,
} = analytics

export type { AnalyticsConfig, GtagEvent, PageViewData }