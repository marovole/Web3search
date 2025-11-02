import React, { Component, ReactNode, ErrorInfo, useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ErrorBoundary } from './error-handling'
import { useSmartRetry } from './auto-retry'
import { 
  AlertTriangle, 
  RefreshCw, 
  Home, 
  Bug, 
  Shield,
  Zap,
  Database,
  Wifi
} from 'lucide-react'

/**
 * 降级策略类型
 */
export type FallbackStrategy = 
  | 'none'
  | 'cached'
  | 'simplified'
  | 'offline'
  | 'placeholder'
  | 'redirect'

/**
 * 错误严重程度
 */
export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical'

/**
 * 组件降级配置
 */
export interface FallbackConfig {
  strategy: FallbackStrategy
  component?: React.ComponentType<any>
  props?: Record<string, any>
  retryable?: boolean
  maxRetries?: number
  timeout?: number
}

/**
 * 错误分类器
 */
export class ErrorClassifier {
  static classify(error: Error): { type: string; severity: ErrorSeverity; retryable: boolean } {
    const message = error.message.toLowerCase()
    const stack = error.stack?.toLowerCase() || ''
    
    // 网络错误
    if (message.includes('network') || message.includes('fetch') || 
        message.includes('connection') || stack.includes('network')) {
      return { type: 'network', severity: 'medium', retryable: true }
    }
    
    // 权限错误
    if (message.includes('permission') || message.includes('unauthorized') || 
        message.includes('forbidden') || message.includes('401') || message.includes('403')) {
      return { type: 'permission', severity: 'high', retryable: false }
    }
    
    // 数据错误
    if (message.includes('data') || message.includes('parse') || 
        message.includes('invalid') || message.includes('400')) {
      return { type: 'data', severity: 'medium', retryable: true }
    }
    
    // 服务器错误
    if (message.includes('server') || message.includes('500') || 
        message.includes('502') || message.includes('503')) {
      return { type: 'server', severity: 'high', retryable: true }
    }
    
    // 超时错误
    if (message.includes('timeout') || message.includes('time out')) {
      return { type: 'timeout', severity: 'medium', retryable: true }
    }
    
    // 资源加载错误
    if (message.includes('loading') || message.includes('chunk') || 
        message.includes('module') || stack.includes('chunk')) {
      return { type: 'resource', severity: 'high', retryable: true }
    }
    
    // 默认为客户端错误
    return { type: 'client', severity: 'medium', retryable: true }
  }
}

/**
 * 缓存降级组件
 */
export const CachedFallback: React.FC<{
  cacheKey: string
  fallbackComponent?: React.ComponentType
  className?: string
}> = ({ cacheKey, fallbackComponent: FallbackComponent, className }) => {
  const [cachedData, setCachedData] = useState<any>(null)
  const [hasCache, setHasCache] = useState(false)

  useEffect(() => {
    try {
      const cached = localStorage.getItem(`fallback_cache_${cacheKey}`)
      if (cached) {
        const data = JSON.parse(cached)
        if (data.timestamp && Date.now() - data.timestamp < 24 * 60 * 60 * 1000) { // 24小时
          setCachedData(data.value)
          setHasCache(true)
        }
      }
    } catch (error) {
      console.warn('Failed to load cached data:', error)
    }
  }, [cacheKey])

  if (hasCache && cachedData) {
    return (
      <div className={cn("border-2 border-yellow-200 bg-yellow-50 p-4 rounded-lg", className)}>
        <div className="flex items-center gap-2 mb-2 text-yellow-700">
          <Database className="w-4 h-4" />
          <span className="text-sm font-medium">离线缓存数据</span>
        </div>
        {FallbackComponent ? (
          <FallbackComponent {...cachedData} />
        ) : (
          <pre className="text-xs text-muted-foreground overflow-auto">
            {JSON.stringify(cachedData, null, 2)}
          </pre>
        )}
      </div>
    )
  }

  return (
    <Alert className={cn("border-yellow-200 bg-yellow-50", className)}>
      <AlertTriangle className="h-4 w-4 text-yellow-600" />
      <AlertDescription className="text-yellow-700">
        暂无缓存数据，请检查网络连接后重试
      </AlertDescription>
    </Alert>
  )
}

/**
 * 简化模式降级组件
 */
export const SimplifiedFallback: React.FC<{
  originalComponent: React.ComponentType
  fallbackComponent: React.ComponentType
  features: string[]
  className?: string
}> = ({ originalComponent: OriginalComponent, fallbackComponent: FallbackComponent, features, className }) => {
  const [useSimplified, setUseSimplified] = useState(false)
  const [disabledFeatures, setDisabledFeatures] = useState<string[]>([])

  const handleSwitchToSimplified = () => {
    setUseSimplified(true)
    setDisabledFeatures(features)
  }

  const handleSwitchToFull = () => {
    setUseSimplified(false)
    setDisabledFeatures([])
  }

  const ComponentToRender = useSimplified ? FallbackComponent : OriginalComponent

  return (
    <div className={className}>
      {/* 功能切换提示 */}
      <Alert className="mb-4 border-blue-200 bg-blue-50">
        <Zap className="h-4 w-4 text-blue-600" />
        <AlertDescription className="text-blue-700">
          {useSimplified ? '正在使用简化模式' : '遇到性能问题？'} 
          <Button
            variant="link"
            size="sm"
            onClick={useSimplified ? handleSwitchToFull : handleSwitchToSimplified}
            className="ml-2 h-auto p-0 text-blue-700"
          >
            {useSimplified ? '切换到完整模式' : '切换到简化模式'}
          </Button>
        </AlertDescription>
      </Alert>

      {/* 禁用功能提示 */}
      {useSimplified && disabledFeatures.length > 0 && (
        <div className="mb-4 text-sm text-muted-foreground">
          已暂时禁用: {disabledFeatures.join(', ')}
        </div>
      )}

      {/* 渲染组件 */}
      <ComponentToRender />
    </div>
  )
}

/**
 * 离线模式降级组件
 */
export const OfflineFallback: React.FC<{
  onlineComponent: React.ComponentType
  offlineComponent: React.ComponentType
  syncActions?: Array<{
    label: string
    action: () => Promise<void>
  }>
  className?: string
}> = ({ onlineComponent: OnlineComponent, offlineComponent: OfflineComponent, syncActions = [], className }) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [pendingActions, setPendingActions] = useState(0)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const handleSyncAction = async (action: () => Promise<void>) => {
    setPendingActions(prev => prev + 1)
    try {
      await action()
    } finally {
      setPendingActions(prev => prev - 1)
    }
  }

  if (isOnline) {
    return <OnlineComponent />
  }

  return (
    <div className={className}>
      {/* 离线提示 */}
      <Alert className="mb-4 border-orange-200 bg-orange-50">
        <Wifi className="h-4 w-4 text-orange-600" />
        <AlertDescription className="text-orange-700">
          当前处于离线状态，部分功能可能受限
        </AlertDescription>
      </Alert>

      {/* 待同步操作 */}
      {pendingActions > 0 && (
        <div className="mb-4 text-sm text-blue-600">
          正在同步 {pendingActions} 个操作...
        </div>
      )}

      {/* 离线组件 */}
      <OfflineComponent />

      {/* 同步操作 */}
      {syncActions.length > 0 && (
        <div className="mt-4 flex gap-2">
          {syncActions.map((action, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={() => handleSyncAction(action.action)}
              disabled={pendingActions > 0}
            >
              {action.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * 占位符降级组件
 */
export const PlaceholderFallback: React.FC<{
  title?: string
  description?: string
  icon?: React.ReactNode
  actions?: Array<{
    label: string
    action: () => void
    variant?: 'default' | 'outline' | 'ghost'
  }>
  className?: string
}> = ({ 
  title = '功能暂时不可用', 
  description = '此功能正在维护中，请稍后再试',
  icon = <Shield className="w-8 h-8" />,
  actions = [],
  className 
}) => {
  return (
    <Card className={cn("p-6 text-center space-y-4", className)}>
      <div className="flex justify-center text-muted-foreground">
        {icon}
      </div>
      
      <div>
        <h3 className="text-lg font-semibold text-foreground mb-2">
          {title}
        </h3>
        <p className="text-sm text-muted-foreground">
          {description}
        </p>
      </div>

      {actions.length > 0 && (
        <div className="flex justify-center gap-2">
          {actions.map((action, index) => (
            <Button
              key={index}
              variant={action.variant || 'outline'}
              size="sm"
              onClick={action.action}
            >
              {action.label}
            </Button>
          ))}
        </div>
      )}
    </Card>
  )
}

/**
 * 智能错误边界组件
 */
export class SmartErrorBoundary extends Component<
  {
    children: ReactNode
    fallback?: React.ComponentType<{ error: Error; errorInfo: ErrorInfo; retry: () => void }>
    config?: Partial<FallbackConfig>
    onError?: (error: Error, errorInfo: ErrorInfo, classification: any) => void
  },
  {
    hasError: boolean
    error: Error | null
    errorInfo: ErrorInfo | null
    classification: any
  }
> {
  private retryCount = 0
  private maxRetries = this.props.config?.maxRetries || 3

  constructor(props: any) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      classification: null
    }
  }

  static getDerivedStateFromError(error: Error) {
    const classification = ErrorClassifier.classify(error)
    return {
      hasError: true,
      error,
      classification
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const classification = ErrorClassifier.classify(error)
    
    this.setState({
      error,
      errorInfo,
      classification
    })

    this.props.onError?.(error, errorInfo, classification)
    
    // 错误上报
    console.error('Smart Error Boundary caught error:', {
      error,
      errorInfo,
      classification,
      retryCount: this.retryCount
    })
  }

  handleRetry = () => {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        classification: null
      })
    }
  }

  render() {
    if (this.state.hasError && this.state.error && this.state.errorInfo) {
      const { classification } = this.state
      const config = this.props.config || {}

      // 根据错误类型选择降级策略
      switch (config.strategy) {
        case 'cached':
          return (
            <CachedFallback
              cacheKey={`error_${Date.now()}`}
              className="mt-4"
            />
          )

        case 'simplified':
          return (
            <div className="mt-4">
              <PlaceholderFallback
                title="功能简化中"
                description="由于技术问题，已切换到简化模式"
                icon={<Zap className="w-8 h-8" />}
                actions={[
                  {
                    label: '重试',
                    action: this.handleRetry,
                    variant: 'default'
                  }
                ]}
              />
            </div>
          )

        case 'offline':
          return (
            <div className="mt-4">
              <PlaceholderFallback
                title="离线模式"
                description="网络连接异常，已切换到离线模式"
                icon={<Wifi className="w-8 h-8" />}
                actions={[
                  {
                    label: '重试连接',
                    action: this.handleRetry,
                    variant: 'default'
                  }
                ]}
              />
            </div>
          )

        case 'placeholder':
          return (
            <div className="mt-4">
              <PlaceholderFallback
                title="功能暂时不可用"
                description={`错误类型: ${classification.type}，严重程度: ${classification.severity}`}
                icon={<AlertTriangle className="w-8 h-8" />}
                actions={[
                  {
                    label: '重试',
                    action: this.handleRetry,
                    variant: classification.retryable ? 'default' : 'outline'
                  }
                ]}
              />
            </div>
          )

        default:
          if (this.props.fallback) {
            const FallbackComponent = this.props.fallback
            return (
              <FallbackComponent
                error={this.state.error}
                errorInfo={this.state.errorInfo}
                retry={this.handleRetry}
              />
            )
          }

          return (
            <div className="mt-4">
              <PlaceholderFallback
                title="应用程序错误"
                description={this.state.error.message}
                icon={<Bug className="w-8 h-8" />}
                actions={[
                  {
                    label: this.retryCount < this.maxRetries ? '重试' : '重新加载页面',
                    action: this.handleRetry,
                    variant: classification.retryable ? 'default' : 'outline'
                  }
                ]}
              />
            </div>
          )
      }
    }

    return this.props.children
  }
}

/**
 * 降级策略Hook
 */
export const useFallbackStrategy = (config: FallbackConfig) => {
  const [strategy, setStrategy] = useState<FallbackStrategy>(config.strategy)
  const [isFallbackActive, setIsFallbackActive] = useState(false)

  const activateFallback = useCallback((newStrategy?: FallbackStrategy) => {
    setStrategy(newStrategy || config.strategy)
    setIsFallbackActive(true)
  }, [config.strategy])

  const deactivateFallback = useCallback(() => {
    setIsFallbackActive(false)
  }, [])

  const switchStrategy = useCallback((newStrategy: FallbackStrategy) => {
    setStrategy(newStrategy)
  }, [])

  return {
    strategy,
    isFallbackActive,
    activateFallback,
    deactivateFallback,
    switchStrategy
  }
}

/**
 * 渐进式降级Provider
 */
export const ProgressiveFallbackProvider: React.FC<{
  children: ReactNode
  strategies: Array<{
    condition: () => boolean
    config: FallbackConfig
  }>
}> = ({ children, strategies }) => {
  const [activeStrategy, setActiveStrategy] = useState<FallbackConfig | null>(null)

  useEffect(() => {
    // 检查是否需要激活降级策略
    for (const strategy of strategies) {
      if (strategy.condition()) {
        setActiveStrategy(strategy.config)
        break
      }
    }
  }, [strategies])

  if (activeStrategy) {
    switch (activeStrategy.strategy) {
      case 'cached':
        return <CachedFallback cacheKey="progressive_fallback" />
      case 'simplified':
        return (
          <PlaceholderFallback
            title="简化模式"
            description="系统性能优化中，已启用简化模式"
            icon={<Zap className="w-8 h-8" />}
          />
        )
      case 'offline':
        return (
          <PlaceholderFallback
            title="离线模式"
            description="网络连接异常，已启用离线模式"
            icon={<Wifi className="w-8 h-8" />}
          />
        )
      case 'placeholder':
        return (
          <PlaceholderFallback
            title="功能维护中"
            description="此功能正在升级，请稍后再试"
            icon={<Shield className="w-8 h-8" />}
          />
        )
      default:
        return <>{children}</>
    }
  }

  return <>{children}</>
}
