import React, { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import * as Sentry from '../../services/sentry-lite'

interface Props {
  children: ReactNode
  componentName: string
  onRetry?: () => void
  fallbackHeight?: string
}

interface State {
  hasError: boolean
  error?: Error
}

class ResearchErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`[${this.props.componentName}] Error:`, error, errorInfo)

    Sentry.captureException(error, {
      errorInfo,
      componentStack: errorInfo.componentStack,
    })

    Sentry.addBreadcrumb({
      message: `Research component error: ${this.props.componentName}`,
      category: 'research',
      level: 'error',
      data: {
        component: this.props.componentName,
        errorMessage: error.message,
      },
    })
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined })
    this.props.onRetry?.()
  }

  override render() {
    if (this.state.hasError) {
      return (
        <div
          className={`flex flex-col items-center justify-center p-4 rounded-lg bg-red-500/10 border border-red-500/20 ${this.props.fallbackHeight || 'min-h-[120px]'}`}
        >
          <AlertTriangle className="w-6 h-6 text-red-400 mb-2" />
          <p className="text-sm text-red-400 text-center mb-2">
            {this.props.componentName} 加载失败
          </p>
          <button
            onClick={this.handleRetry}
            className="flex items-center gap-1 px-3 py-1 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            重试
          </button>
          {import.meta.env?.DEV && this.state.error && (
            <p className="mt-2 text-xs text-red-300/60 font-mono truncate max-w-full px-2">
              {this.state.error.message}
            </p>
          )}
        </div>
      )
    }

    return this.props.children
  }
}

export default ResearchErrorBoundary
