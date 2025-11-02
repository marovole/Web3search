import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"
import { cn } from "@/lib/utils"
import { Check, RefreshCw, AlertCircle } from "lucide-react"

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn(
      "relative h-4 w-full overflow-hidden rounded-full bg-secondary",
      className
    )}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className="h-full w-full flex-1 bg-primary transition-all"
      style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
    />
  </ProgressPrimitive.Root>
))
Progress.displayName = ProgressPrimitive.Root.displayName

/**
 * 增强进度指示器属性
 */
export interface EnhancedProgressProps {
  value: number
  max?: number
  className?: string
  showLabel?: boolean
  showPercentage?: boolean
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'success' | 'warning' | 'error'
  animated?: boolean
  indeterminate?: boolean
}

/**
 * 增强进度指示器组件
 */
export const EnhancedProgress: React.FC<EnhancedProgressProps> = ({
  value,
  max = 100,
  className,
  showLabel = false,
  showPercentage = true,
  size = 'md',
  variant = 'default',
  animated = true,
  indeterminate = false
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))
  
  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }

  const variantClasses = {
    default: 'bg-primary',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500'
  }

  const labelVariantClasses = {
    default: 'text-primary',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600'
  }

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-muted-foreground">进度</span>
          <span className={cn("text-sm font-medium", labelVariantClasses[variant])}>
            {showPercentage ? `${Math.round(percentage)}%` : `${value}/${max}`}
          </span>
        </div>
      )}
      
      <div className={cn(
        "w-full bg-secondary rounded-full overflow-hidden",
        sizeClasses[size]
      )}>
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300 ease-out",
            variantClasses[variant],
            animated && "transition-all duration-300 ease-out",
            indeterminate && "animate-pulse"
          )}
          style={{
            width: indeterminate ? '100%' : `${percentage}%`,
            ...(indeterminate && {
              backgroundImage: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
              backgroundSize: '200% 100%',
              animation: 'shimmer 1.5s infinite'
            })
          }}
        />
      </div>
    </div>
  )
}

/**
 * 环形进度指示器
 */
export const CircularProgress: React.FC<{
  value: number
  max?: number
  size?: number
  strokeWidth?: number
  className?: string
  showPercentage?: boolean
  variant?: 'default' | 'success' | 'warning' | 'error'
}> = ({
  value,
  max = 100,
  size = 120,
  strokeWidth = 8,
  className,
  showPercentage = true,
  variant = 'default'
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  const variantColors = {
    default: 'text-primary',
    success: 'text-green-500',
    warning: 'text-yellow-500',
    error: 'text-red-500'
  }

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* 背景圆 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-muted opacity-20"
        />
        {/* 进度圆 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={cn(
            "transition-all duration-300 ease-out",
            variantColors[variant]
          )}
          strokeLinecap="round"
        />
      </svg>
      
      {showPercentage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-semibold text-foreground">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
    </div>
  )
}

/**
 * 步骤进度指示器
 */
export const StepProgress: React.FC<{
  steps: Array<{
    id: string
    title: string
    status: 'pending' | 'current' | 'completed' | 'error'
  }>
  className?: string
  size?: 'sm' | 'md' | 'lg'
}> = ({ steps, className, size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-10 h-10 text-base'
  }

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <Check className="w-3 h-3" />
      case 'error':
        return <AlertCircle className="w-3 h-3" />
      case 'current':
        return <RefreshCw className="w-3 h-3 animate-spin" />
      default:
        return null
    }
  }

  const getStepClasses = (status: string) => {
    const baseClasses = cn(
      "flex items-center justify-center rounded-full border-2 font-medium transition-all duration-200",
      sizeClasses[size]
    )

    switch (status) {
      case 'completed':
        return cn(baseClasses, "bg-green-500 border-green-500 text-white")
      case 'error':
        return cn(baseClasses, "bg-red-500 border-red-500 text-white")
      case 'current':
        return cn(baseClasses, "bg-primary border-primary text-white")
      default:
        return cn(baseClasses, "bg-background border-muted-foreground text-muted-foreground")
    }
  }

  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center">
            <div className="flex flex-col items-center">
              <div className={getStepClasses(step.status)}>
                {getStepIcon(step.status) || (
                  <span>{index + 1}</span>
                )}
              </div>
              <span className="mt-2 text-xs text-center max-w-20 text-muted-foreground">
                {step.title}
              </span>
            </div>
            
            {/* 连接线 */}
            {index < steps.length - 1 && (
              <div className={cn(
                "flex-1 h-0.5 mx-2 transition-all duration-200",
                step.status === 'completed' ? "bg-green-500" : "bg-muted"
              )} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * 乐观更新Hook
 */
export const useOptimisticUpdate = <T,>(
  initialValue: T,
  updateFn: (newValue: T) => Promise<T>
) => {
  const [value, setValue] = React.useState<T>(initialValue)
  const [optimisticValue, setOptimisticValue] = React.useState<T>(initialValue)
  const [isUpdating, setIsUpdating] = React.useState(false)
  const [error, setError] = React.useState<Error | null>(null)

  const update = React.useCallback(async (newValue: T) => {
    try {
      setIsUpdating(true)
      setError(null)
      
      // 立即更新UI（乐观更新）
      setOptimisticValue(newValue)
      
      // 执行实际更新
      const result = await updateFn(newValue)
      
      // 更新实际值
      setValue(result)
      setOptimisticValue(result)
      
      return result
    } catch (err) {
      setError(err as Error)
      // 回滚到原始值
      setOptimisticValue(value)
      throw err
    } finally {
      setIsUpdating(false)
    }
  }, [value, updateFn])

  const reset = React.useCallback(() => {
    setOptimisticValue(value)
    setError(null)
  }, [value])

  return {
    value: optimisticValue,
    actualValue: value,
    update,
    reset,
    isUpdating,
    error
  }
}

/**
 * 文件上传进度Hook
 */
export const useFileUploadProgress = () => {
  const [progress, setProgress] = React.useState(0)
  const [isUploading, setIsUploading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const uploadFile = React.useCallback(async (
    file: File,
    uploadFn: (file: File, onProgress: (progress: number) => void) => Promise<void>
  ) => {
    try {
      setIsUploading(true)
      setProgress(0)
      setError(null)

      await uploadFn(file, (progressValue) => {
        setProgress(progressValue)
      })

      setProgress(100)
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败')
      throw err
    } finally {
      setIsUploading(false)
    }
  }, [])

  const reset = React.useCallback(() => {
    setProgress(0)
    setIsUploading(false)
    setError(null)
  }, [])

  return {
    progress,
    isUploading,
    error,
    uploadFile,
    reset
  }
}

/**
 * 任务进度Hook
 */
export const useTaskProgress = (taskId: string) => {
  const [progress, setProgress] = React.useState(0)
  const [status, setStatus] = React.useState<'idle' | 'running' | 'completed' | 'error'>('idle')
  const [message, setMessage] = React.useState<string>('')
  const [error, setError] = React.useState<string | null>(null)

  const startTask = React.useCallback((initialMessage?: string) => {
    setProgress(0)
    setStatus('running')
    setMessage(initialMessage || '任务进行中...')
    setError(null)
  }, [])

  const updateProgress = React.useCallback((newProgress: number, newMessage?: string) => {
    setProgress(Math.min(100, Math.max(0, newProgress)))
    if (newMessage) {
      setMessage(newMessage)
    }
  }, [])

  const completeTask = React.useCallback((completionMessage?: string) => {
    setProgress(100)
    setStatus('completed')
    setMessage(completionMessage || '任务完成')
    setError(null)
  }, [])

  const failTask = React.useCallback((errorMessage: string) => {
    setStatus('error')
    setError(errorMessage)
    setMessage(errorMessage)
  }, [])

  const reset = React.useCallback(() => {
    setProgress(0)
    setStatus('idle')
    setMessage('')
    setError(null)
  }, [])

  return {
    progress,
    status,
    message,
    error,
    startTask,
    updateProgress,
    completeTask,
    failTask,
    reset
  }
}

/**
 * 添加动画样式
 */
React.useEffect(() => {
  const style = document.createElement('style')
  style.textContent = `
    @keyframes shimmer {
      0% {
        background-position: -200% 0;
      }
      100% {
        background-position: 200% 0;
      }
    }
  `
  if (!document.head.querySelector('style[data-progress-animation]')) {
    style.setAttribute('data-progress-animation', 'true')
    document.head.appendChild(style)
  }
  
  return () => {
    const existingStyle = document.head.querySelector('style[data-progress-animation]')
    if (existingStyle) {
      document.head.removeChild(existingStyle)
    }
  }
}, [])

export { Progress }
