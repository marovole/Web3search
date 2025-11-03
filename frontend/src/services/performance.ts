/**
 * 性能监控服务
 * 集成Web Vitals和自定义性能指标
 */

import { getEnvConfig, isFeatureEnabled } from '../utils/env'

interface WebVitalMetrics {
  id: string
  name: string
  value: number
  delta: number
  rating: 'good' | 'needs-improvement' | 'poor'
  timestamp: number
}

interface CustomMetrics {
  firstContentfulPaint?: number
  largestContentfulPaint?: number
  firstInputDelay?: number
  cumulativeLayoutShift?: number
  timeToInteractive?: number
}

interface PerformanceEntry {
  name: string
  entryType: string
  startTime: number
  duration: number
  value?: number
}

/**
 * 性能监控管理器
 */
class PerformanceMonitor {
  private metrics: WebVitalMetrics[] = []
  private isMonitoring = false
  private observer?: PerformanceObserver

  constructor() {
    this.init()
  }

  /**
   * 初始化性能监控
   */
  private init() {
    const config = getEnvConfig()

    // 检查是否应该启用性能监控
    if (!isFeatureEnabled('ENABLE_PERFORMANCE_MONITORING')) {
      console.log('📊 性能监控已禁用')
      return
    }

    this.isMonitoring = true
    console.log('✅ 性能监控已启用')

    // 设置监控
    this.setupWebVitalsMonitoring()
    this.setupCustomMetrics()
  }

  /**
   * 设置Web Vitals监控
   */
  private setupWebVitalsMonitoring() {
    if (!this.isMonitoring || typeof window === 'undefined') return

    try {
      // 创建PerformanceObserver监听各种性能指标
      this.observer = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries()

        entries.forEach((entry) => {
          if (entry.entryType === 'largest-contentful-paint') {
            this.recordMetric({
              id: `lcp-${Date.now()}`,
              name: 'LCP',
              value: entry.startTime,
              delta: 0,
              rating: this.rateLCP(entry.startTime),
              timestamp: Date.now()
            })
          } else if (entry.entryType === 'first-input') {
            const inputEntry = entry as any
            this.recordMetric({
              id: `fid-${Date.now()}`,
              name: 'FID',
              value: inputEntry.processingStart - entry.startTime,
              delta: 0,
              rating: this.rateFID(inputEntry.processingStart - entry.startTime),
              timestamp: Date.now()
            })
          } else if (entry.entryType === 'layout-shift') {
            const layoutShiftEntry = entry as any
            if (!layoutShiftEntry.hadRecentInput) {
              this.recordMetric({
                id: `cls-${Date.now()}`,
                name: 'CLS',
                value: layoutShiftEntry.value,
                delta: layoutShiftEntry.value,
                rating: this.rateCLS(layoutShiftEntry.value),
                timestamp: Date.now()
              })
            }
          }
        })
      })

      // 注册观察者
      this.observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] })

      // 监控FCP (First Contentful Paint)
      this.observeFCP()

    } catch (error) {
      console.warn('Web Vitals监控初始化失败:', error)
    }
  }

  /**
   * 观察First Contentful Paint
   */
  private observeFCP() {
    if (!window.performance || !window.performance.getEntriesByType) return

    const observer = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries()
      const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint')

      if (fcpEntry) {
        this.recordMetric({
          id: `fcp-${Date.now()}`,
          name: 'FCP',
          value: fcpEntry.startTime,
          delta: 0,
          rating: this.rateFCP(fcpEntry.startTime),
          timestamp: Date.now()
        })
        observer.disconnect()
      }
    })

    observer.observe({ entryTypes: ['paint'] })
  }

  /**
   * 设置自定义性能指标
   */
  private setupCustomMetrics() {
    if (!this.isMonitoring) return

    // 监控页面加载时间
    window.addEventListener('load', () => {
      setTimeout(() => {
        this.recordPageLoadMetrics()
      }, 0)
    })

    // 监控API响应时间
    this.setupAPIMonitoring()
  }

  /**
   * 记录页面加载指标
   */
  private recordPageLoadMetrics() {
    if (!window.performance || !window.performance.timing) return

    const timing = window.performance.timing
    const navigation = window.performance.navigation

    // 计算关键指标
    const metrics = {
      dnsLookup: timing.domainLookupEnd - timing.domainLookupStart,
      tcpConnection: timing.connectEnd - timing.connectStart,
      serverResponse: timing.responseEnd - timing.requestStart,
      domLoad: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
      pageLoad: timing.loadEventEnd - timing.loadEventStart,
      totalTime: timing.loadEventEnd - timing.navigationStart,
    }

    console.log('📊 页面性能指标:', metrics)

    // 记录自定义指标
    this.recordMetric({
      id: `pageload-${Date.now()}`,
      name: 'Page Load Time',
      value: metrics.totalTime,
      delta: 0,
      rating: this.ratePageLoad(metrics.totalTime),
      timestamp: Date.now()
    })
  }

  /**
   * 设置API监控
   */
  private setupAPIMonitoring() {
    // 使用Fetch API拦截器监控API性能
    const originalFetch = window.fetch

    window.fetch = async (...args) => {
      const startTime = performance.now()

      try {
        const response = await originalFetch(...args)
        const endTime = performance.now()
        const duration = endTime - startTime

        // 记录API性能指标
        this.recordAPIMetric(args[0] as string, duration, response.status)

        return response
      } catch (error) {
        const endTime = performance.now()
        const duration = endTime - startTime

        this.recordAPIMetric(args[0] as string, duration, 0)
        throw error
      }
    }
  }

  /**
   * 记录API性能指标
   */
  private recordAPIMetric(url: string, duration: number, status: number) {
    const apiName = url.split('/').pop() || 'unknown'

    this.recordMetric({
      id: `api-${apiName}-${Date.now()}`,
      name: `API: ${apiName}`,
      value: duration,
      delta: 0,
      rating: this.rateAPIResponse(duration),
      timestamp: Date.now()
    })
  }

  /**
   * 记录性能指标
   */
  private recordMetric(metric: WebVitalMetrics) {
    this.metrics.push(metric)

    // 限制存储的指标数量
    if (this.metrics.length > 100) {
      this.metrics = this.metrics.slice(-50)
    }

    // 在控制台输出性能信息
    console.log(`📈 ${metric.name}: ${metric.value.toFixed(2)}ms (${metric.rating})`)

    // 发送到Sentry（如果可用）
    this.sendToSentry(metric)
  }

  /**
   * 发送性能指标到Sentry
   */
  private sendToSentry(metric: WebVitalMetrics) {
    // 如果Sentry可用，将性能指标作为额外信息发送
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.addBreadcrumb({
        message: `Performance: ${metric.name}`,
        category: 'performance',
        level: metric.rating === 'good' ? 'info' : 'warning',
        data: {
          value: metric.value,
          rating: metric.rating,
          timestamp: metric.timestamp
        }
      })
    }
  }

  /**
   * 评分函数
   */
  private rateLCP(value: number): 'good' | 'needs-improvement' | 'poor' {
    if (value <= 2500) return 'good'
    if (value <= 4000) return 'needs-improvement'
    return 'poor'
  }

  private rateFID(value: number): 'good' | 'needs-improvement' | 'poor' {
    if (value <= 100) return 'good'
    if (value <= 300) return 'needs-improvement'
    return 'poor'
  }

  private rateCLS(value: number): 'good' | 'needs-improvement' | 'poor' {
    if (value <= 0.1) return 'good'
    if (value <= 0.25) return 'needs-improvement'
    return 'poor'
  }

  private rateFCP(value: number): 'good' | 'needs-improvement' | 'poor' {
    if (value <= 1800) return 'good'
    if (value <= 3000) return 'needs-improvement'
    return 'poor'
  }

  private ratePageLoad(value: number): 'good' | 'needs-improvement' | 'poor' {
    if (value <= 3000) return 'good'
    if (value <= 5000) return 'needs-improvement'
    return 'poor'
  }

  private rateAPIResponse(value: number): 'good' | 'needs-improvement' | 'poor' {
    if (value <= 500) return 'good'
    if (value <= 1500) return 'needs-improvement'
    return 'poor'
  }

  /**
   * 获取当前性能指标
   */
  public getMetrics(): WebVitalMetrics[] {
    return [...this.metrics]
  }

  /**
   * 获取最新的Web Vitals指标
   */
  public getWebVitals(): CustomMetrics {
    const latestMetrics = this.getMetrics()
    const result: CustomMetrics = {}

    latestMetrics.forEach(metric => {
      switch (metric.name) {
        case 'FCP':
          result.firstContentfulPaint = metric.value
          break
        case 'LCP':
          result.largestContentfulPaint = metric.value
          break
        case 'FID':
          result.firstInputDelay = metric.value
          break
        case 'CLS':
          result.cumulativeLayoutShift = metric.value
          break
      }
    })

    return result
  }

  /**
   * 计算性能评分
   */
  public getPerformanceScore(): number {
    const vitals = this.getWebVitals()
    const scores = []

    if (vitals.firstContentfulPaint) {
      scores.push(this.scoreMetric(vitals.firstContentfulPaint, [1800, 3000]))
    }
    if (vitals.largestContentfulPaint) {
      scores.push(this.scoreMetric(vitals.largestContentfulPaint, [2500, 4000]))
    }
    if (vitals.firstInputDelay) {
      scores.push(this.scoreMetric(vitals.firstInputDelay, [100, 300]))
    }
    if (vitals.cumulativeLayoutShift) {
      scores.push(this.scoreMetric(vitals.cumulativeLayoutShift * 1000, [100, 250]))
    }

    if (scores.length === 0) return 100
    return Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
  }

  private scoreMetric(value: number, thresholds: [number, number]): number {
    const [good, poor] = thresholds
    if (value <= good) return 100
    if (value >= poor) return 0
    return Math.round(100 - ((value - good) / (poor - good)) * 100)
  }

  /**
   * 清理监控
   */
  public dispose() {
    if (this.observer) {
      this.observer.disconnect()
    }
    this.isMonitoring = false
  }
}

// 延迟创建实例，避免在模块加载时执行
let performanceMonitorInstance: PerformanceMonitor | null = null

function getPerformanceMonitor(): PerformanceMonitor {
  if (!performanceMonitorInstance) {
    performanceMonitorInstance = new PerformanceMonitor()
  }
  return performanceMonitorInstance
}

export default getPerformanceMonitor

// 导出主要功能
export { PerformanceMonitor }
export type { WebVitalMetrics, CustomMetrics }