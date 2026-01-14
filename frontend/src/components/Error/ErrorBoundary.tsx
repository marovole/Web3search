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

  static override getDerivedStateFromError(error: Error): State {
    // 更新 state 使下一次渲染能够显示降级后的 UI
    return { hasError: true, error, errorType: categorizeError(error) }
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
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

      // 默认错误 UI
      return (
        <div className="flex flex-col items-center justify-center min-h-[200px] p-6 text-center">
          <div className="text-red-500 mb-4">
            {errorType === 'network' ? (
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
              </svg>
            ) : (
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </div>

          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {errorType === 'network' ? '网络连接问题' : '哎呀，出现了一些问题'}
          </h3>

          <p className="text-gray-600 mb-4 max-w-md">
            {errorType === 'network' 
              ? '无法连接到服务器，请检查您的网络连接后重试。' 
              : '应用程序遇到了意外错误。请尝试刷新页面或稍后再试。'}
          </p>

          <div className="flex gap-3 justify-center">
            <button
              onClick={this.handleRetry}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              重试
            </button>

            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              刷新页面
            </button>
          </div>

          {import.meta.env?.DEV && this.state.error && (
            <details className="mt-6 text-left">
              <summary className="cursor-pointer text-sm font-mono text-red-600">
                错误详情 (开发模式) - {errorType}
              </summary>
              <pre className="mt-2 p-4 bg-red-50 rounded-lg text-xs overflow-auto max-h-40">
                {this.state.error.toString()}
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