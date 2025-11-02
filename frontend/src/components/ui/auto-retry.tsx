import React, { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Clock,
  WifiOff
} from 'lucide-react'

/**
 * 重试配置接口
 */
export interface RetryConfig {
  maxAttempts: number
  baseDelay: number
  maxDelay: number
  backoffFactor: number
  retryCondition?: (error: any) => boolean
  onRetry?: (attempt: number, error: any) => void
  onSuccess?: (attempt: number) => void
  onFailure?: (error: any) => void
}

/**
 * 重试状态
 */
export interface RetryState {
  attempt: number
  isRetrying: boolean
  lastError: any
  nextRetryIn: number
  canRetry: boolean
}

/**
 * 默认重试配置
 */
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffFactor: 2,
  retryCondition: (error) => {
    // 默认重试条件：网络错误或5xx服务器错误
    return error.name === 'NetworkError' || 
           (error.status >= 500 && error.status < 600) ||
           error.code === 'NETWORK_ERROR' ||
           error.code === 'TIMEOUT'
  }
}

/**
 * 智能重试Hook
 */
export const useSmartRetry = <T,>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
) => {
  const finalConfig = { ...DEFAULT_RETRY_CONFIG, ...config }
  const [state, setState] = useState<RetryState>({
    attempt: 0,
    isRetrying: false,
    lastError: null,
    nextRetryIn: 0,
    canRetry: true
  })
  
  const retryTimeoutRef = useRef<NodeJS.Timeout>()
  const abortControllerRef = useRef<AbortController>()

  const calculateDelay = useCallback((attempt: number) => {
    const delay = Math.min(
      finalConfig.baseDelay * Math.pow(finalConfig.backoffFactor, attempt - 1),
      finalConfig.maxDelay
    )
    
    // 添加随机抖动，避免雷群效应
    return delay + Math.random() * 1000
  }, [finalConfig])

  const execute = useCallback(async (): Promise<T> => {
    // 取消之前的重试
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
    }
    
    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    abortControllerRef.current = new AbortController()

    let attempt = 0
    let lastError: any = null

    while (attempt < finalConfig.maxAttempts) {
      attempt++
      
      try {
        setState(prev => ({
          ...prev,
          attempt,
          isRetrying: true,
          lastError: null,
          canRetry: attempt < finalConfig.maxAttempts
        }))

        const result = await fn()
        
        // 成功
        setState(prev => ({
          ...prev,
          isRetrying: false,
          lastError: null,
          nextRetryIn: 0
        }))

        finalConfig.onSuccess?.(attempt)
        return result

      } catch (error) {
        lastError = error
        
        setState(prev => ({
          ...prev,
          lastError: error,
          isRetrying: false
        }))

        // 检查是否应该重试
        if (attempt >= finalConfig.maxAttempts || 
            !finalConfig.retryCondition?.(error)) {
          break
        }

        // 计算下次重试延迟
        const delay = calculateDelay(attempt)
        
        setState(prev => ({
          ...prev,
          nextRetryIn: delay
        }))

        finalConfig.onRetry?.(attempt, error)

        // 等待重试
        await new Promise(resolve => {
          retryTimeoutRef.current = setTimeout(resolve, delay)
        })
      }
    }

    // 所有重试都失败了
    setState(prev => ({
      ...prev,
      isRetrying: false,
      canRetry: false,
      nextRetryIn: 0
    }))

    finalConfig.onFailure?.(lastError)
    throw lastError
  }, [fn, finalConfig, calculateDelay])

  const reset = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
    }
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    setState({
      attempt: 0,
      isRetrying: false,
      lastError: null,
      nextRetryIn: 0,
      canRetry: true
    })
  }, [])

  const cancel = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
    }
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    setState(prev => ({
      ...prev,
      isRetrying: false,
      nextRetryIn: 0
    }))
  }, [])

  // 清理定时器
  useEffect(() => {
    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current)
      }
    }
  }, [])

  return {
    execute,
    reset,
    cancel,
    state
  }
}

/**
 * 重试指示器组件
 */
export const RetryIndicator: React.FC<{
  state: RetryState
  config: RetryConfig
  onRetry?: () => void
  onCancel?: () => void
  className?: string
  compact?: boolean
}> = ({ 
  state, 
  config, 
  onRetry, 
  onCancel,
  className,
  compact = false 
}) => {
  const [timeLeft, setTimeLeft] = useState(0)

  useEffect(() => {
    if (state.nextRetryIn > 0) {
      setTimeLeft(Math.ceil(state.nextRetryIn / 1000))
      
      const interval = setInterval(() => {
        setTimeLeft(prev => Math.max(0, prev - 1))
      }, 1000)

      return () => clearInterval(interval)
    }
  }, [state.nextRetryIn])

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2 text-sm", className)}>
        {state.isRetrying ? (
          <>
            <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
            <span>重试中... ({state.attempt}/{config.maxAttempts})</span>
          </>
        ) : state.lastError ? (
          <>
            <XCircle className="w-4 h-4 text-red-500" />
            <span>
              失败 ({state.attempt}/{config.maxAttempts})
              {state.canRetry && onRetry && (
                <Button
                  variant="link"
                  size="sm"
                  onClick={onRetry}
                  className="ml-1 h-auto p-0"
                >
                  重试
                </Button>
              )}
            </span>
          </>
        ) : null}
      </div>
    )
  }

  return (
    <Card className={cn("p-4 space-y-3", className)}>
      {/* 状态指示 */}
      <div className="flex items-center gap-3">
        {state.isRetrying ? (
          <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
        ) : state.lastError ? (
          <XCircle className="w-5 h-5 text-red-500" />
        ) : (
          <CheckCircle className="w-5 h-5 text-green-500" />
        )}
        
        <div className="flex-1">
          <div className="font-medium">
            {state.isRetrying ? '正在重试...' : 
             state.lastError ? '重试失败' : '操作成功'}
          </div>
          <div className="text-sm text-muted-foreground">
            尝试次数: {state.attempt}/{config.maxAttempts}
          </div>
        </div>
      </div>

      {/* 进度条 */}
      {state.isRetrying && (
        <Progress value={(state.attempt / config.maxAttempts) * 100} />
      )}

      {/* 倒计时 */}
      {state.nextRetryIn > 0 && (
        <div className="flex items-center gap-2 text-sm text-blue-600">
          <Clock className="w-4 h-4" />
          <span>下次重试: {timeLeft}秒</span>
        </div>
      )}

      {/* 错误信息 */}
      {state.lastError && (
        <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
          {state.lastError.message || '操作失败'}
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex gap-2">
        {state.isRetrying && onCancel && (
          <Button variant="outline" size="sm" onClick={onCancel}>
            取消
          </Button>
        )}
        
        {!state.isRetrying && state.canRetry && onRetry && (
          <Button size="sm" onClick={onRetry}>
            <RefreshCw className="w-4 h-4 mr-2" />
            立即重试
          </Button>
        )}
      </div>
    </Card>
  )
}

/**
 * 网络错误恢复Hook
 */
export const useNetworkRecovery = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [recoveryAttempts, setRecoveryAttempts] = useState(0)
  const recoveryTimeoutRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      setRecoveryAttempts(0)
    }

    const handleOffline = () => {
      setIsOnline(false)
      startRecoveryAttempts()
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      
      if (recoveryTimeoutRef.current) {
        clearTimeout(recoveryTimeoutRef.current)
      }
    }
  }, [])

  const startRecoveryAttempts = useCallback(() => {
    let attempts = 0
    const maxAttempts = 5
    const baseDelay = 2000

    const attemptRecovery = async () => {
      attempts++
      setRecoveryAttempts(attempts)

      try {
        // 尝试发送一个简单的网络请求
        const response = await fetch('/api/health', {
          method: 'HEAD',
          cache: 'no-cache'
        })

        if (response.ok) {
          setIsOnline(true)
          setRecoveryAttempts(0)
          return
        }
      } catch (error) {
        // 网络仍然不可用
      }

      if (attempts < maxAttempts) {
        const delay = baseDelay * Math.pow(2, attempts - 1)
        recoveryTimeoutRef.current = setTimeout(attemptRecovery, delay)
      }
    }

    // 延迟开始恢复尝试
    recoveryTimeoutRef.current = setTimeout(attemptRecovery, 1000)
  }, [])

  return {
    isOnline,
    recoveryAttempts,
    isRecovering: recoveryAttempts > 0
  }
}

/**
 * 网络恢复指示器
 */
export const NetworkRecoveryIndicator: React.FC<{
  className?: string
}> = ({ className }) => {
  const { isOnline, recoveryAttempts, isRecovering } = useNetworkRecovery()

  if (isOnline) {
    return (
      <div className={cn(
        "flex items-center gap-2 text-sm text-green-600",
        className
      )}>
        <CheckCircle className="w-4 h-4" />
        <span>网络连接正常</span>
      </div>
    )
  }

  return (
    <div className={cn(
      "flex items-center gap-2 text-sm text-orange-600",
      className
    )}>
      {isRecovering ? (
        <>
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>正在恢复连接... (尝试 {recoveryAttempts})</span>
        </>
      ) : (
        <>
          <WifiOff className="w-4 h-4" />
          <span>网络连接已断开</span>
        </>
      )}
    </div>
  )
}

/**
 * 断路器模式Hook
 */
export const useCircuitBreaker = (
  threshold: number = 5,
  timeout: number = 60000
) => {
  const [state, setState] = useState<'CLOSED' | 'OPEN' | 'HALF_OPEN'>('CLOSED')
  const [failureCount, setFailureCount] = useState(0)
  const [lastFailureTime, setLastFailureTime] = useState(0)

  const execute = useCallback(async <T,>(fn: () => Promise<T>): Promise<T> => {
    const now = Date.now()

    // 如果断路器打开且超时时间已过，尝试半开状态
    if (state === 'OPEN' && now - lastFailureTime > timeout) {
      setState('HALF_OPEN')
    }

    // 如果断路器打开，拒绝请求
    if (state === 'OPEN') {
      throw new Error('Circuit breaker is OPEN')
    }

    try {
      const result = await fn()
      
      // 成功时重置断路器
      if (state === 'HALF_OPEN') {
        setState('CLOSED')
        setFailureCount(0)
      }
      
      return result
    } catch (error) {
      // 失败时增加计数
      const newFailureCount = failureCount + 1
      setFailureCount(newFailureCount)
      setLastFailureTime(now)

      // 达到阈值时打开断路器
      if (newFailureCount >= threshold) {
        setState('OPEN')
      }

      throw error
    }
  }, [state, failureCount, lastFailureTime, threshold, timeout])

  const reset = useCallback(() => {
    setState('CLOSED')
    setFailureCount(0)
    setLastFailureTime(0)
  }, [])

  return {
    execute,
    reset,
    state,
    failureCount
  }
}

/**
 * 自动重试包装器组件
 */
export const AutoRetryWrapper: React.FC<{
  children: React.ReactNode
  retryConfig?: Partial<RetryConfig>
  fallback?: React.ReactNode
  onRetry?: () => void
}> = ({ 
  children, 
  retryConfig, 
  fallback,
  onRetry 
}) => {
  const [retryState, setRetryState] = useState<RetryState>({
    attempt: 0,
    isRetrying: false,
    lastError: null,
    nextRetryIn: 0,
    canRetry: true
  })

  const handleRetry = useCallback(() => {
    setRetryState(prev => ({
      ...prev,
      attempt: prev.attempt + 1,
      isRetrying: true,
      lastError: null
    }))

    onRetry?.()
  }, [onRetry])

  if (retryState.lastError && !retryState.isRetrying) {
    if (fallback) {
      return <>{fallback}</>
    }

    return (
      <RetryIndicator
        state={retryState}
        config={{ ...DEFAULT_RETRY_CONFIG, ...retryConfig }}
        onRetry={retryState.canRetry ? handleRetry : undefined}
      />
    )
  }

  return <>{children}</>
}
