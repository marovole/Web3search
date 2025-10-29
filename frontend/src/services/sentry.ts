import * as Sentry from '@sentry/react'
import { getEnvConfig, isFeatureEnabled } from '../utils/env'

// 注意：使用Sentry内置性能监控，无需外部tracing包

/**
 * Sentry 错误监控服务配置
 * 只在生产环境和启用错误监控功能时初始化
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

      // 性能监控 - 使用Sentry内置性能监控
      integrations: [
        // 新版本Sentry已内置性能监控，无需外部BrowserTracing
        // 如需自定义路由追踪，可使用reactRouterV6BrowserTracingIntegration
      ],

      // 采样率配置
      tracesSampleRate: config.ENVIRONMENT === 'production' ? 0.1 : 1.0,

      // 错误采样率（生产环境降低采样率以节省配额）
      sampleRate: config.ENVIRONMENT === 'production' ? 0.5 : 1.0,

      // 过滤不必要的错误
      beforeSend(event, hint) {
        // 过滤掉一些常见的客户端错误
        const error = hint?.originalException

        // 忽略网络相关错误（已有专门的网络重试机制）
        if (error instanceof Error) {
          if (error.message.includes('Network Error') ||
              error.message.includes('timeout') ||
              error.message.includes('Request aborted')) {
            return null
          }
        }

        // 添加自定义标签和上下文
        if (event.extra) {
          event.tags = {
            ...event.tags,
            feature: 'chat-interface',
          }
        }

        return event
      },

      // 用户上下文
      // beforeSendSpan 已在新版本中弃用，使用其他方式追踪

      // 版本信息
      release: process.env.npm_package_version || '1.0.0',
    })

    console.log('✅ Sentry 错误监控已初始化')
  } catch (error) {
    console.error('❌ Sentry 初始化失败:', error)
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
 * 性能监控：开始Span
 * 使用新版本的Sentry性能监控API
 */
export function startSpan(name: string, operation: string = 'navigation', callback?: (span: Sentry.Span) => void) {
  if (!isFeatureEnabled('ENABLE_SENTRY')) return null

  try {
    // 使用新的Sentry.startSpan API
    return Sentry.startSpan({
      name,
      op: operation
    }, callback || (() => {}))
  } catch (error) {
    console.warn('Sentry span creation failed:', error)
    return null
  }
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
}