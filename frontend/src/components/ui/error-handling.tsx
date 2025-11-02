import React, { useState, useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  AlertTriangle,
  XCircle,
  Info,
  CheckCircle,
  RefreshCw,
  Home,
  ArrowLeft,
  ExternalLink,
  Mail,
  Bug
} from 'lucide-react'

/**
 * 错误类型
 */
export type ErrorType = 
  | 'network'
  | 'server' 
  | 'client'
  | 'validation'
  | 'permission'
  | 'notFound'
  | 'timeout'
  | 'quota'
  | 'maintenance'
  | 'unknown'

/**
 * 错误严重程度
 */
export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical'

/**
 * 错误信息接口
 */
export interface ErrorInfo {
  id: string
  type: ErrorType
  severity: ErrorSeverity
  title: string
  message: string
  details?: string
  actions?: ErrorAction[]
  timestamp: number
  retryable?: boolean
  userFriendly?: boolean
}

/**
 * 错误操作接口
 */
export interface ErrorAction {
  id: string
  label: string
  type: 'primary' | 'secondary' | 'danger'
  action: () => void | Promise<void>
  icon?: React.ReactNode
}

/**
 * 错误配置映射
 */
const ERROR_CONFIGS: Record<ErrorType, {
  icon: React.ReactNode
  color: string
  bgColor: string
  borderColor: string
  defaultTitle: string
  defaultMessage: string
  suggestions: string[]
}> = {
  network: {
    icon: <AlertTriangle className="w-5 h-5" />,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    defaultTitle: '网络连接错误',
    defaultMessage: '无法连接到服务器，请检查您的网络连接。',
    suggestions: [
      '检查网络连接是否正常',
      '尝试刷新页面',
      '稍后再试'
    ]
  },
  server: {
    icon: <XCircle className="w-5 h-5" />,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    defaultTitle: '服务器错误',
    defaultMessage: '服务器遇到了问题，请稍后再试。',
    suggestions: [
      '稍等片刻后重试',
      '如果问题持续，请联系技术支持',
      '尝试使用其他浏览器'
    ]
  },
  client: {
    icon: <Bug className="w-5 h-5" />,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    defaultTitle: '应用程序错误',
    defaultMessage: '应用程序遇到了意外错误。',
    suggestions: [
      '刷新页面重试',
      '清除浏览器缓存',
      '联系技术支持'
    ]
  },
  validation: {
    icon: <Info className="w-5 h-5" />,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    defaultTitle: '输入验证错误',
    defaultMessage: '请检查您的输入信息。',
    suggestions: [
      '检查必填字段',
      '确认输入格式正确',
      '查看详细错误信息'
    ]
  },
  permission: {
    icon: <AlertTriangle className="w-5 h-5" />,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    defaultTitle: '权限不足',
    defaultMessage: '您没有执行此操作的权限。',
    suggestions: [
      '联系管理员获取权限',
      '登录正确的账户',
      '检查账户状态'
    ]
  },
  notFound: {
    icon: <Info className="w-5 h-5" />,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    defaultTitle: '页面未找到',
    defaultMessage: '您访问的页面不存在。',
    suggestions: [
      '检查URL是否正确',
      '返回上一页',
      '访问首页'
    ]
  },
  timeout: {
    icon: <AlertTriangle className="w-5 h-5" />,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    defaultTitle: '请求超时',
    defaultMessage: '请求处理时间过长，请稍后再试。',
    suggestions: [
      '检查网络连接',
      '稍后重试',
      '减少请求数据量'
    ]
  },
  quota: {
    icon: <AlertTriangle className="w-5 h-5" />,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    defaultTitle: '配额不足',
    defaultMessage: '已达到使用限制。',
    suggestions: [
      '升级账户计划',
      '删除不必要的数据',
      '联系管理员'
    ]
  },
  maintenance: {
    icon: <Info className="w-5 h-5" />,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    defaultTitle: '系统维护中',
    defaultMessage: '系统正在进行维护，请稍后再试。',
    suggestions: [
      '稍等片刻后重试',
      '关注维护公告',
      '联系客服了解详情'
    ]
  },
  unknown: {
    icon: <XCircle className="w-5 h-5" />,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    defaultTitle: '未知错误',
    defaultMessage: '发生了未知错误，请稍后再试。',
    suggestions: [
      '刷新页面重试',
      '联系技术支持',
      '查看错误详情'
    ]
  }
}

/**
 * 错误提示组件
 */
export const ErrorAlert: React.FC<{
  error: ErrorInfo
  className?: string
  showDetails?: boolean
  onDismiss?: () => void
  compact?: boolean
}> = ({ 
  error, 
  className, 
  showDetails = false, 
  onDismiss,
  compact = false 
}) => {
  const [showFullDetails, setShowFullDetails] = useState(false)
  const config = ERROR_CONFIGS[error.type]

  if (compact) {
    return (
      <Alert className={cn(
        config.bgColor,
        config.borderColor,
        className
      )}>
        <div className="flex items-center gap-2">
          <div className={config.color}>
            {config.icon}
          </div>
          <AlertDescription className="flex-1">
            <span className="font-medium">{error.title}</span>
            <span className="ml-2 text-sm">{error.message}</span>
          </AlertDescription>
          {onDismiss && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
              className="h-6 w-6 p-0"
            >
              <XCircle className="w-4 h-4" />
            </Button>
          )}
        </div>
      </Alert>
    )
  }

  return (
    <Card className={cn(
      "p-6 space-y-4",
      config.bgColor,
      config.borderColor,
      "border-2",
      className
    )}>
      {/* 错误头部 */}
      <div className="flex items-start gap-3">
        <div className={cn("flex-shrink-0 mt-1", config.color)}>
          {config.icon}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground">
            {error.title}
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            {error.message}
          </p>
        </div>
        {onDismiss && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDismiss}
            className="flex-shrink-0"
          >
            <XCircle className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* 建议操作 */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-foreground">建议操作：</p>
        <ul className="text-sm text-muted-foreground space-y-1">
          {config.suggestions.map((suggestion, index) => (
            <li key={index} className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <span>{suggestion}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 操作按钮 */}
      {error.actions && error.actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {error.actions.map((action) => (
            <Button
              key={action.id}
              variant={action.type === 'primary' ? 'default' : 'outline'}
              size="sm"
              onClick={action.action}
              className="flex items-center gap-2"
            >
              {action.icon}
              {action.label}
            </Button>
          ))}
        </div>
      )}

      {/* 错误详情 */}
      {(showDetails || error.details) && (
        <div className="border-t pt-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFullDetails(!showFullDetails)}
            className="text-xs"
          >
            {showFullDetails ? '隐藏' : '显示'}详细信息
          </Button>
          
          {showFullDetails && (
            <div className="mt-2 p-3 bg-background rounded text-xs font-mono">
              <div>错误ID: {error.id}</div>
              <div>类型: {error.type}</div>
              <div>严重程度: {error.severity}</div>
              <div>时间: {new Date(error.timestamp).toLocaleString()}</div>
              {error.details && (
                <div className="mt-2 whitespace-pre-wrap">
                  {error.details}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

/**
 * 全屏错误页面
 */
export const ErrorPage: React.FC<{
  error: ErrorInfo
  onRetry?: () => void
  onGoHome?: () => void
  onGoBack?: () => void
  className?: string
}> = ({ 
  error, 
  onRetry, 
  onGoHome, 
  onGoBack,
  className 
}) => {
  const config = ERROR_CONFIGS[error.type]

  return (
    <div className={cn(
      "flex flex-col items-center justify-center min-h-screen p-8 bg-background",
      className
    )}>
      <Card className="w-full max-w-lg p-8 text-center space-y-6">
        {/* 错误图标 */}
        <div className={cn("mx-auto", config.color)}>
          {React.cloneElement(config.icon as React.ReactElement, { 
            className: "w-16 h-16" 
          })}
        </div>

        {/* 错误信息 */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-foreground">
            {error.title}
          </h1>
          <p className="text-muted-foreground">
            {error.message}
          </p>
        </div>

        {/* 建议操作 */}
        <div className="text-left space-y-2">
          <p className="text-sm font-medium text-foreground">您可以尝试：</p>
          <ul className="text-sm text-muted-foreground space-y-1">
            {config.suggestions.slice(0, 3).map((suggestion, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 操作按钮 */}
        <div className="flex flex-col gap-3">
          {error.retryable && onRetry && (
            <Button onClick={onRetry} className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              重试
            </Button>
          )}
          
          <div className="flex gap-2">
            {onGoBack && (
              <Button variant="outline" onClick={onGoBack} className="flex-1">
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回
              </Button>
            )}
            
            {onGoHome && (
              <Button variant="outline" onClick={onGoHome} className="flex-1">
                <Home className="w-4 h-4 mr-2" />
                首页
              </Button>
            )}
          </div>
        </div>

        {/* 联系支持 */}
        <div className="text-xs text-muted-foreground space-y-1 pt-4 border-t">
          <p>如果问题持续存在，请联系技术支持</p>
          <div className="flex items-center justify-center gap-4">
            <Button variant="ghost" size="sm" className="h-auto p-0">
              <Mail className="w-3 h-3 mr-1" />
              support@example.com
            </Button>
            <Button variant="ghost" size="sm" className="h-auto p-0">
              <ExternalLink className="w-3 h-3 mr-1" />
              帮助中心
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

/**
 * 错误Toast组件
 */
export const ErrorToast: React.FC<{
  error: ErrorInfo
  onClose: () => void
  autoClose?: boolean
  duration?: number
}> = ({ 
  error, 
  onClose, 
  autoClose = true,
  duration = 5000 
}) => {
  const config = ERROR_CONFIGS[error.type]

  useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(onClose, duration)
      return () => clearTimeout(timer)
    }
  }, [autoClose, duration, onClose])

  return (
    <div className={cn(
      "fixed top-4 right-4 z-50 max-w-sm p-4 rounded-lg shadow-lg border-2 animate-slide-in",
      config.bgColor,
      config.borderColor
    )}>
      <div className="flex items-start gap-3">
        <div className={cn("flex-shrink-0", config.color)}>
          {config.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground">
            {error.title}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {error.message}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="flex-shrink-0 h-6 w-6 p-0"
        >
          <XCircle className="w-3 h-3" />
        </Button>
      </div>
    </div>
  )
}

/**
 * 错误处理Hook
 */
export const useErrorHandler = () => {
  const [errors, setErrors] = useState<ErrorInfo[]>([])

  const addError = useCallback((error: Partial<ErrorInfo>) => {
    const errorInfo: ErrorInfo = {
      id: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: error.type || 'unknown',
      severity: error.severity || 'medium',
      title: error.title || ERROR_CONFIGS[error.type || 'unknown'].defaultTitle,
      message: error.message || ERROR_CONFIGS[error.type || 'unknown'].defaultMessage,
      timestamp: Date.now(),
      retryable: error.retryable ?? true,
      userFriendly: error.userFriendly ?? true,
      ...error
    }

    setErrors(prev => [...prev, errorInfo])
    return errorInfo
  }, [])

  const removeError = useCallback((id: string) => {
    setErrors(prev => prev.filter(error => error.id !== id))
  }, [])

  const clearErrors = useCallback(() => {
    setErrors([])
  }, [])

  const handleError = useCallback((error: Error, context?: string) => {
    console.error('Application error:', error, context)
    
    return addError({
      type: 'client',
      severity: 'high',
      title: '应用程序错误',
      message: error.message || '发生了意外错误',
      details: `${error.name}: ${error.message}\n${error.stack}`,
      retryable: true
    })
  }, [addError])

  return {
    errors,
    addError,
    removeError,
    clearErrors,
    handleError
  }
}

/**
 * 错误边界组件
 */
export class ErrorBoundary extends React.Component<
  {
    children: React.ReactNode
    fallback?: React.ComponentType<{ error: Error; reset: () => void }>
    onError?: (error: Error, errorInfo: React.ErrorInfo) => void
  },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: any) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    this.props.onError?.(error, errorInfo)
  }

  reset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback
        return <FallbackComponent error={this.state.error} reset={this.reset} />
      }

      return (
        <ErrorPage
          error={{
            id: 'boundary-error',
            type: 'client',
            severity: 'critical',
            title: '应用程序错误',
            message: '应用程序遇到了严重错误，需要重新加载。',
            details: this.state.error.stack,
            timestamp: Date.now(),
            retryable: true
          }}
          onRetry={this.reset}
          onGoHome={() => window.location.href = '/'}
        />
      )
    }

    return this.props.children
  }
}
