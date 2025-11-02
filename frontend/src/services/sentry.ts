import * as Sentry from '@sentry/react'
import { getEnvConfig, isFeatureEnabled } from '../utils/env'
import React from 'react'
import {
  useLocation,
  useNavigationType,
  createRoutesFromChildren,
  matchRoutes
} from 'react-router-dom'

// 注意：使用Sentry内置性能监控，无需外部tracing包

/**
 * Sentry 错误监控和RUM服务配置
 * 只在生产环境和启用错误监控功能时初始化
 * 包含完整的真实用户监控(RUM)功能
 */

export function initSentry() {
  const config = getEnvConfig()

  // 检查是否应该初始化 Sentry
  if (!config.ENABLE_SENTRY || config.ENVIRONMENT === 'development' || !config.SENTRY_DSN) {
    console.log('📊 Sentry 监控已禁用')
    return
  }

  try {
    Sentry.init({
      dsn: config.SENTRY_DSN,

      // 环境配置
      environment: config.SENTRY_ENVIRONMENT || config.ENVIRONMENT,
      debug: config.DEBUG_MODE,

      // 性能监控和RUM - 扩展配置
      integrations: [
        // 新版本Sentry已内置性能监控，包含RUM功能
        // 浏览器性能监控集成
        new Sentry.BrowserTracing({
          // 路由追踪配置
          routingInstrumentation: Sentry.reactRouterV6Instrumentation(
            React.useEffect,
            useLocation,
            useNavigationType,
            createRoutesFromChildren,
            matchRoutes
          ),
          // 自定义事务采样
          beforeNavigate: (context) => {
            // 过滤掉一些不重要的路由
            if (context.url.includes('/health') || context.url.includes('/metrics')) {
              return null
            }
            return {
              ...context,
              name: context.name.replace(/^\//, 'route-')
            }
          }
        }),
        // 用户会话重放（RUM扩展功能）
        new Sentry.Replay({
          // 会话重放采样率
          sessionSampleRate: config.ENVIRONMENT === 'production' ? 0.1 : 1.0,
          // 错误重放采样率
          errorSampleRate: 1.0,
          // 不记录敏感输入
          maskAllText: true,
          blockAllMedia: true,
        }),
      ],

      // 采样率配置 - RUM优化
      tracesSampleRate: getRUMTracesSampleRate(config.ENVIRONMENT),
      
      // 错误采样率（生产环境降低采样率以节省配额）
      sampleRate: config.ENVIRONMENT === 'production' ? 0.5 : 1.0,

      // 过滤不必要的错误
      beforeSend(event, hint) {
        return filterErrors(event, hint)
      },

      // RUM性能数据过滤
      beforeSendTransaction(transaction) {
        return filterTransaction(transaction)
      },

      // 用户上下文和隐私配置
      sendDefaultPii: false, // 不发送个人身份信息
      // RUM特定配置
      attachStacktrace: true,
      maxBreadcrumbs: 50,
      
      // 版本信息
      release: process.env.npm_package_version || '1.0.0',
      
      // 分布式追踪
      tracePropagationTargets: [
        'localhost', /^https:\/\/api\.web3search\.com/,
        /^https:\/\/web3search-api\.onrender\.com/
      ],
    })

    console.log('✅ Sentry 错误监控已初始化')
  } catch (error) {
    console.error('❌ Sentry 初始化失败:', error)
  }
}

/**
 * 获取RUM追踪采样率
 * 根据环境和配置动态调整采样率
 */
function getRUMTracesSampleRate(environment: string): number {
  switch (environment.toLowerCase()) {
    case 'production':
      return 0.1  // 生产环境10%采样率
    case 'staging':
      return 0.5  // 预发布环境50%采样率
    default:
      return 1.0  // 开发环境100%采样率
  }
}

/**
 * 过滤错误事件
 */
function filterErrors(event: Sentry.Event, hint: Sentry.EventHint): Sentry.Event | null {
  // 过滤掉一些常见的客户端错误
  const error = hint?.originalException

  // 忽略网络相关错误（已有专门的网络重试机制）
  if (error instanceof Error) {
    if (error.message.includes('Network Error') ||
        error.message.includes('timeout') ||
        error.message.includes('Request aborted') ||
        error.message.includes('AbortError')) {
      return null
    }
  }

  // 添加自定义标签和上下文
  if (event.extra) {
    event.tags = {
      ...event.tags,
      feature: 'web3search-rum',
      component: 'frontend',
    }
  }

  // 添加用户设备信息
  if (event.contexts) {
    event.contexts.device = {
      ...event.contexts.device,
      user_agent: navigator.userAgent,
      screen_resolution: `${screen.width}x${screen.height}`,
      viewport_size: `${window.innerWidth}x${window.innerHeight}`,
    }
  }

  return event
}

/**
 * 过滤事务数据
 */
function filterTransaction(transaction: Sentry.Transaction): Sentry.Transaction | null {
  // 过滤掉一些不重要的页面
  const transactionName = transaction.name
  if (transactionName.includes('/health') || 
      transactionName.includes('/metrics') ||
      transactionName.includes('favicon.ico')) {
    return null
  }

  // 添加自定义标签
  transaction.setTag('page_type', getPageType(transactionName))
  transaction.setTag('load_time', Date.now().toString())
  
  return transaction
}

/**
 * 根据URL获取页面类型
 */
function getPageType(url: string): string {
  if (url.includes('/chat') || url.includes('/search')) {
    return 'search'
  } else if (url.includes('/report')) {
    return 'report'
  } else if (url.includes('/deep-research')) {
    return 'deep_research'
  } else if (url === '/' || url.includes('/home')) {
    return 'home'
  } else {
    return 'other'
  }
}

/**
 * 记录自定义错误事件
 */
export function captureException(error: Error, context?: Record<string, any>) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) {
    console.error('Sentry disabled - Error:', error, context)
    return
  }

  Sentry.captureException(error, {
    extra: context,
    tags: {
      customError: true,
    },
  })
}

/**
 * 记录自定义消息
 */
export function captureMessage(message: string, level: Sentry.SeverityLevel = 'info', context?: Record<string, any>) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) {
    console.log(`Sentry disabled - Message [${level}]:`, message, context)
    return
  }

  Sentry.captureMessage(message, {
    level,
    extra: context,
  })
}

/**
 * 设置用户信息
 */
export function setUser(user: { id: string; email?: string; username?: string }) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return

  Sentry.setUser(user)
}

/**
 * 清除用户信息
 */
export function clearUser() {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return

  Sentry.setUser(null)
}

/**
 * 添加面包屑导航
 */
export function addBreadcrumb(breadcrumb: Sentry.Breadcrumb) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return

  Sentry.addBreadcrumb(breadcrumb)
}

/**
 * 设置上下文信息
 */
export function setContext(key: string, context: Record<string, any>) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return

  Sentry.setContext(key, context)
}

/**
 * 性能监控：开始Span（RUM增强版）
 * 使用新版本的Sentry性能监控API，支持RUM指标收集
 */
export function startSpan(name: string, operation: string = 'navigation', callback?: (span: Sentry.Span) => void) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return null

  try {
    // 使用新的Sentry.startSpan API
    return Sentry.startSpan({
      name,
      op: operation,
      data: {
        page_type: getPageType(window.location.pathname),
        timestamp: Date.now(),
        url: window.location.href
      }
    }, callback || (() => {}))
  } catch (error) {
    console.warn('Sentry span creation failed:', error)
    return null
  }
}

/**
 * RUM核心Web Vitals监控
 */
export function trackCoreWebVitals() {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return

  // Largest Contentful Paint (LCP)
  new PerformanceObserver((list) => {
    const entries = list.getEntries()
    const lastEntry = entries[entries.length - 1]
    Sentry.setMeasurement('lcp', lastEntry.startTime, 'millisecond')
  }).observe({ type: 'largest-contentful-paint', buffered: true })

  // First Input Delay (FID)
  new PerformanceObserver((list) => {
    const entries = list.getEntries()
    entries.forEach((entry) => {
      Sentry.setMeasurement('fid', entry.processingStart - entry.startTime, 'millisecond')
    })
  }).observe({ type: 'first-input', buffered: true })

  // Cumulative Layout Shift (CLS)
  let clsValue = 0
  new PerformanceObserver((list) => {
    const entries = list.getEntries()
    entries.forEach((entry) => {
      if (!(entry as any).hadRecentInput) {
        clsValue += (entry as any).value
      }
    })
    Sentry.setMeasurement('cls', clsValue, 'none')
  }).observe({ type: 'layout-shift', buffered: true })

  // Time to First Byte (TTFB)
  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
  if (navigation) {
    Sentry.setMeasurement('ttfb', navigation.responseStart - navigation.requestStart, 'millisecond')
  }
}

/**
 * 用户交互监控
 */
export function trackUserInteraction(action: string, element?: string, properties?: Record<string, any>) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return

  Sentry.addBreadcrumb({
    category: 'user',
    message: `User ${action}`,
    level: 'info',
    data: {
      action,
      element,
      page_type: getPageType(window.location.pathname),
      ...properties
    }
  })

  // 记录自定义指标
  Sentry.setMeasurement(`user.${action}`, 1, 'none')
}

/**
 * API请求监控（RUM增强版）
 */
export function trackAPIRequest(url: string, method: string, status: number, duration: number, responseSize?: number) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return

  const apiName = new URL(url).pathname
  
  Sentry.addBreadcrumb({
    category: 'http',
    message: `${method} ${apiName}`,
    level: status >= 400 ? 'error' : 'info',
    data: {
      method,
      url: apiName,
      status_code: status,
      duration_ms: duration,
      response_size_bytes: responseSize
    }
  })

  // 记录性能指标
  Sentry.setMeasurement(`api.${apiName.replace(/\//g, '.')}.duration`, duration, 'millisecond')
  Sentry.setMeasurement(`api.${method.toLowerCase()}.duration`, duration, 'millisecond')
}

/**
 * 页面加载性能监控
 */
export function trackPageLoad() {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return

  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
  if (!navigation) return

  const metrics = {
    // 基本加载指标
    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
    
    // 网络指标
    dnsLookup: navigation.domainLookupEnd - navigation.domainLookupStart,
    tcpConnect: navigation.connectEnd - navigation.connectStart,
    requestTime: navigation.responseEnd - navigation.requestStart,
    
    // 处理指标
    domProcessing: navigation.domComplete - navigation.domLoading,
    
    // 总体指标
    totalTime: navigation.loadEventEnd - navigation.navigationStart
  }

  // 发送所有指标到Sentry
  Object.entries(metrics).forEach(([name, value]) => {
    Sentry.setMeasurement(`page.${name}`, value, 'millisecond')
  })

  // 添加页面加载面包屑
  Sentry.addBreadcrumb({
    category: 'navigation',
    message: 'Page load completed',
    level: 'info',
    data: {
      page_type: getPageType(window.location.pathname),
      load_time_ms: metrics.totalTime,
      ...metrics
    }
  })
}

/**
 * 资源加载监控
 */
export function trackResourceLoading() {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return

  const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries()
    
    entries.forEach((entry) => {
      if (entry.entryType === 'resource') {
        const resource = entry as PerformanceResourceTiming
        const resourceType = getResourceType(resource.name)
        
        Sentry.setMeasurement(
          `resource.${resourceType}.duration`, 
          resource.responseEnd - resource.requestStart, 
          'millisecond'
        )
        
        Sentry.setMeasurement(
          `resource.${resourceType}.size`, 
          resource.transferSize || 0, 
          'byte'
        )
      }
    })
  })
  
  observer.observe({ type: 'resource', buffered: true })
}

/**
 * 根据资源名称获取资源类型
 */
function getResourceType(url: string): string {
  if (url.includes('.js')) return 'script'
  if (url.includes('.css')) return 'stylesheet'
  if (url.match(/\.(png|jpg|jpeg|gif|webp|svg)$/i)) return 'image'
  if (url.match(/\.(woff|woff2|ttf|eot)$/i)) return 'font'
  if (url.includes('/api/')) return 'api'
  return 'other'
}

/**
 * 错误监控增强版
 */
export function trackError(error: Error, context?: Record<string, any>) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) {
    console.error('Sentry disabled - Error:', error, context)
    return
  }

  // 添加用户环境信息
  const enhancedContext = {
    ...context,
    user_agent: navigator.userAgent,
    page_url: window.location.href,
    page_type: getPageType(window.location.pathname),
    viewport_size: `${window.innerWidth}x${window.innerHeight}`,
    connection_type: (navigator as any).connection?.effectiveType || 'unknown',
    online_status: navigator.onLine
  }

  Sentry.captureException(error, {
    extra: enhancedContext,
    tags: {
      error_type: error.constructor.name,
      page_type: getPageType(window.location.pathname),
      feature: 'web3search-rum'
    }
  })
}

/**
 * 性能监控：开始事务（向后兼容）
 */
export function startTransaction(name: string, operation: string = 'navigation') {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return null

  // 新版本中，使用startSpan替代startTransaction
  return startSpan(name, operation)
}

export default {
  initSentry,
  captureException,
  captureMessage,
  setUser,
  clearUser,
  addBreadcrumb,
  setContext,
  startSpan,
  startTransaction,
  trackCoreWebVitals,
  trackUserInteraction,
  trackAPIRequest,
  trackPageLoad,
  trackResourceLoading,
  trackError,
}