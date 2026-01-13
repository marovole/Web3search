import React, { Component, ErrorInfo, ReactNode } from 'react'
import * as Sentry from '../../services/sentry-lite'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: ErrorInfo
  errorType: ErrorType
}

type ErrorType = 'network' | 'render' | 'unknown'

// Error classification helper
function categorizeError(error: Error): ErrorType {
  const errorMessage = error.message.toLowerCase()
  
  // Network errors
  if (
    errorMessage.includes('network') ||
    errorMessage.includes('fetch') ||
    errorMessage.includes('axios') ||
    errorMessage.includes('ECONNREFUSED') ||
    errorMessage.includes('timeout')
  ) {
    return 'network'
  }
  
  // Render errors (React-specific)
  if (
    errorMessage.includes('invalid') ||
    errorMessage.includes('cannot read') ||
    errorMessage.includes('undefined is not a function') ||
    errorMessage.includes('rendered fewer hooks') ||
    errorMessage.includes('maximum call stack')
  ) {
    return 'render'
  }
  
  return 'unknown'
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, errorType: 'unknown' }
  }

  static getDerivedStateFromError(error: Error): State {
    // 更新 state 使下一次渲染能够显示降级后的 UI
    return { hasError: true, error, errorType: categorizeError(error) }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // 记录错误信息
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({
      error,
      errorInfo,
    })

    // 发送错误到 Sentry
    Sentry.captureException(error, {
      errorInfo,
      componentStack: errorInfo.componentStack,
    })

    // 添加面包屑导航
    Sentry.addBreadcrumb({
      message: 'ErrorBoundary caught React error',
      category: 'error',
      level: 'fatal',
      data: {
        errorMessage: error.message,
        errorStack: error.stack,
        componentStack: errorInfo.componentStack,
        errorType: categorizeError(error),
      },
    })

    // Call optional error callback
    this.props.onError?.(error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined, errorType: 'unknown' })
  }

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义 fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback
      }

      // 根据错误类型显示不同的错误 UI
      const errorType = this.state.errorType
      const error = this.state.error

      // 生成错误追踪 ID（用于支持查询）
      const errorTraceId = React.useMemo(() => {
        return `ERR-${Date.now().toString(36).toUpperCase()}`
      }, [])

      // 默认错误 UI
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center bg-gray-50/50 rounded-xl mx-4 my-8 border border-gray-100">
          <div className="mb-6">
            {errorType === 'network' ? (
              <div className="w-20 h-20 mx-auto bg-orange-100 rounded-full flex items-center justify-center">
                <svg className="w-10 h-10 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3" />
                </svg>
              </div>
            ) : (
              <div className="w-20 h-20 mx-auto bg-red-100 rounded-full flex items-center justify-center">
                <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            )}
          </div>

          <h3 className="text-xl font-semibold text-gray-900 mb-3">
            {errorType === 'network' ? '网络连接问题' : '遇到了一些问题'}
          </h3>

          <p className="text-gray-600 mb-6 max-w-md leading-relaxed">
            {errorType === 'network'
              ? '无法连接到服务器，请检查您的网络连接后重试。如果问题持续存在，可能是服务器暂时不可用。'
              : '应用程序遇到了意外错误。我们的团队已经收到通知，您可以通过以下方式获取帮助。'}
          </p>

          {/* 错误追踪 ID */}
          <div className="mb-6 px-4 py-2 bg-white rounded-lg border border-gray-200 text-sm">
            <span className="text-gray-500">错误追踪号: </span>
            <span className="font-mono text-gray-700 font-medium">{errorTraceId}</span>
          </div>

          <div className="flex gap-3 justify-center flex-wrap">
            <button
              onClick={this.handleRetry}
              className="px-6 py-2.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-all hover:shadow-md active:scale-95"
            >
              重新尝试
            </button>

            <button
              onClick={() => window.location.reload()}
              className="px-6 py-2.5 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all hover:shadow-md active:scale-95"
            >
              刷新页面
            </button>

            <a
              href="mailto:support@web3search.io?subject=错误报告 - {errorTraceId}&body=错误追踪号: {errorTraceId}%0D%0D错误信息: {error?.message}"
              className="px-6 py-2.5 text-gray-600 hover:text-gray-800 transition-colors"
            >
              联系客服
            </a>
          </div>

          {/* 建议的操作 */}
          {errorType === 'network' && (
            <div className="mt-8 text-left bg-white p-4 rounded-lg border border-gray-200 max-w-md w-full">
              <h4 className="text-sm font-medium text-gray-700 mb-2">建议操作:</h4>
              <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                <li>检查网络连接是否正常</li>
                <li>尝试切换网络环境</li>
                <li>等待几分钟后重试</li>
              </ul>
            </div>
          )}

          {import.meta.env.DEV && error && (
            <details className="mt-6 text-left w-full max-w-2xl">
              <summary className="cursor-pointer text-sm font-mono text-red-600 bg-red-50 px-3 py-2 rounded">
                错误详情 (开发模式) - {errorType}
              </summary>
              <pre className="mt-2 p-4 bg-gray-900 text-gray-100 rounded-lg text-xs overflow-auto max-h-60 font-mono">
                {error.toString()}
                {'\n\n--- Component Stack ---'}
                {this.state.errorInfo && this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary