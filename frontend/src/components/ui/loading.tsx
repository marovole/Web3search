import * as React from "react"
import { createContext, useContext, useState, useCallback } from "react"
import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"
import { Card } from "./card"

interface LoadingProps {
  className?: string
  size?: "sm" | "md" | "lg"
  text?: string
}

const Loading = React.forwardRef<HTMLDivElement, LoadingProps>(
  ({ className, size = "md", text, ...props }, ref) => {
    const sizeClasses = {
      sm: "w-4 h-4",
      md: "w-6 h-6",
      lg: "w-8 h-8"
    }

    return (
      <div
        ref={ref}
        className={cn("flex items-center justify-center gap-2", className)}
        {...props}
      >
        <Loader2 className={cn("animate-spin", sizeClasses[size])} />
        {text && <span className="text-sm text-muted-foreground">{text}</span>}
      </div>
    )
  }
)
Loading.displayName = "Loading"

// 骨架屏组件
interface SkeletonProps {
  className?: string
  lines?: number
  animate?: boolean
}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, lines = 1, animate = true, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("space-y-2", className)} {...props}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-4 bg-muted rounded-md",
              animate && "animate-pulse",
              i === lines - 1 && lines > 1 && "w-3/4"
            )}
          />
        ))}
      </div>
    )
  }
)
Skeleton.displayName = "Skeleton"

// 卡片骨架屏
const CardSkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <Card ref={ref} className={cn("p-6", className)} {...props}>
        <div className="space-y-3">
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-4 w-full" lines={3} />
        </div>
      </Card>
    )
  }
)
CardSkeleton.displayName = "CardSkeleton"

// 消息气泡骨架屏
const MessageSkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "flex gap-3 max-w-[80%] animate-fade-in",
          className
        )}
        {...props}
      >
        <div className="w-8 h-8 bg-muted rounded-full animate-pulse" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton lines={2} />
        </div>
      </div>
    )
  }
)
MessageSkeleton.displayName = "MessageSkeleton"

// 头像骨架屏
export const AvatarSkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("w-10 h-10 bg-muted rounded-full animate-pulse", className)}
        {...props}
      />
    )
  }
)
AvatarSkeleton.displayName = "AvatarSkeleton"

// 输入框骨架屏
export const InputSkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("space-y-2", className)} {...props}>
        <div className="h-10 bg-muted rounded-md animate-pulse" />
        <div className="h-4 bg-muted rounded w-1/4 animate-pulse" />
      </div>
    )
  }
)
InputSkeleton.displayName = "InputSkeleton"

// 聊天界面骨架屏
export const ChatSkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("flex flex-col h-full", className)} {...props}>
        {/* 聊天头部 */}
        <div className="border-b p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <AvatarSkeleton />
              <div className="space-y-2">
                <div className="h-5 w-32 bg-muted rounded animate-pulse" />
                <div className="h-3 w-24 bg-muted rounded animate-pulse" />
              </div>
            </div>
            <div className="h-10 w-20 bg-muted rounded animate-pulse" />
          </div>
        </div>

        {/* 聊天消息区域 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <MessageSkeleton />
          <div className="flex gap-3 max-w-[80%] flex-row-reverse">
            <AvatarSkeleton />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-20 bg-muted rounded animate-pulse" />
              <div className="rounded-lg p-3 bg-primary/20 space-y-2">
                <Skeleton lines={3} />
              </div>
            </div>
          </div>
          <MessageSkeleton />
        </div>

        {/* 输入区域 */}
        <div className="border-t p-4">
          <InputSkeleton />
        </div>
      </div>
    )
  }
)
ChatSkeleton.displayName = "ChatSkeleton"

// 搜索结果骨架屏
export const SearchSkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("space-y-4", className)} {...props}>
        {/* 搜索框 */}
        <InputSkeleton />
        
        {/* 搜索结果列表 */}
        <div className="space-y-3">
          {Array.from({ length: 5 }, (_, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-muted rounded-lg animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-1/3 bg-muted rounded animate-pulse" />
                  <div className="h-3 w-2/3 bg-muted rounded animate-pulse" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    )
  }
)
SearchSkeleton.displayName = "SearchSkeleton"

// 历史记录骨架屏
export const HistorySkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("space-y-4", className)} {...props}>
        <div className="h-6 w-1/3 bg-muted rounded animate-pulse mb-4" />
        <div className="space-y-3">
          {Array.from({ length: 3 }, (_, i) => (
            <Card key={i} className="p-4">
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <Skeleton lines={2} />
                  <div className="h-8 w-20 bg-muted rounded animate-pulse" />
                </div>
                <Skeleton lines={1} />
              </div>
            </Card>
          ))}
        </div>
      </div>
    )
  }
)
HistorySkeleton.displayName = "HistorySkeleton"

// 设置页面骨架屏
export const SettingsSkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("space-y-6", className)} {...props}>
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="space-y-4">
            <div className="h-6 w-1/3 bg-muted rounded animate-pulse" />
            <div className="space-y-3">
              {Array.from({ length: 2 }, (_, j) => (
                <div key={j} className="flex items-center justify-between p-3 border rounded">
                  <div className="space-y-2">
                    <div className="h-4 w-32 bg-muted rounded animate-pulse" />
                    <div className="h-3 w-48 bg-muted rounded animate-pulse" />
                  </div>
                  <div className="h-6 w-16 bg-muted rounded animate-pulse" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }
)
SettingsSkeleton.displayName = "SettingsSkeleton"

// 报告页面骨架屏
export const ReportSkeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("space-y-6", className)} {...props}>
        {/* 报告头部 */}
        <div className="space-y-3">
          <div className="h-6 w-1/3 bg-muted rounded animate-pulse" />
          <Skeleton lines={2} />
        </div>

        {/* 报告内容 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 图表区域 */}
          <div className="space-y-4">
            <div className="h-64 w-full bg-muted rounded animate-pulse" />
            <div className="h-48 w-full bg-muted rounded animate-pulse" />
          </div>
          
          {/* 数据区域 */}
          <div className="space-y-4">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    )
  }
)
ReportSkeleton.displayName = "ReportSkeleton"

// 加载状态类型
export type LoadingType = 
  | 'page' 
  | 'component' 
  | 'button' 
  | 'form' 
  | 'chat' 
  | 'search' 
  | 'upload'
  | 'download'

// 加载状态配置
export interface LoadingState {
  id: string
  type: LoadingType
  message?: string
  progress?: number
  showProgress?: boolean
  overlay?: boolean
  skeleton?: boolean
}

// 加载上下文接口
interface LoadingContextType {
  loadingStates: Map<string, LoadingState>
  startLoading: (state: LoadingState) => void
  stopLoading: (id: string) => void
  updateLoading: (id: string, updates: Partial<LoadingState>) => void
  isLoading: (id?: string) => boolean
  getLoadingState: (id: string) => LoadingState | undefined
  clearAllLoading: () => void
}

// 加载上下文
const LoadingContext = createContext<LoadingContextType | undefined>(undefined)

// 加载状态管理提供者
export const LoadingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [loadingStates, setLoadingStates] = useState<Map<string, LoadingState>>(new Map())

  const startLoading = useCallback((state: LoadingState) => {
    setLoadingStates(prev => new Map(prev).set(state.id, state))
  }, [])

  const stopLoading = useCallback((id: string) => {
    setLoadingStates(prev => {
      const newMap = new Map(prev)
      newMap.delete(id)
      return newMap
    })
  }, [])

  const updateLoading = useCallback((id: string, updates: Partial<LoadingState>) => {
    setLoadingStates(prev => {
      const current = prev.get(id)
      if (!current) return prev
      
      const newMap = new Map(prev)
      newMap.set(id, { ...current, ...updates })
      return newMap
    })
  }, [])

  const isLoading = useCallback((id?: string) => {
    if (id) {
      return loadingStates.has(id)
    }
    return loadingStates.size > 0
  }, [loadingStates])

  const getLoadingState = useCallback((id: string) => {
    return loadingStates.get(id)
  }, [loadingStates])

  const clearAllLoading = useCallback(() => {
    setLoadingStates(new Map())
  }, [])

  return (
    <LoadingContext.Provider value={{
      loadingStates,
      startLoading,
      stopLoading,
      updateLoading,
      isLoading,
      getLoadingState,
      clearAllLoading
    }}>
      {children}
    </LoadingContext.Provider>
  )
}

// 使用加载状态的Hook
export const useLoading = () => {
  const context = useContext(LoadingContext)
  if (!context) {
    throw new Error('useLoading must be used within a LoadingProvider')
  }
  return context
}

// 简化的加载Hook - 用于单个组件
export const useSimpleLoading = (id: string, initialState?: Partial<LoadingState>) => {
  const { startLoading, stopLoading, updateLoading, isLoading, getLoadingState } = useLoading()

  const start = useCallback((overrides?: Partial<LoadingState>) => {
    startLoading({ 
      id, 
      type: 'component',
      ...initialState,
      ...overrides 
    })
  }, [id, initialState, startLoading])

  const stop = useCallback(() => {
    stopLoading(id)
  }, [id, stopLoading])

  const update = useCallback((updates: Partial<LoadingState>) => {
    updateLoading(id, updates)
  }, [id, updateLoading])

  return {
    start,
    stop,
    update,
    isLoading: isLoading(id),
    state: getLoadingState(id)
  }
}

// 进度条组件
export const ProgressBar: React.FC<{
  progress: number
  className?: string
  showLabel?: boolean
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error'
}> = ({ 
  progress, 
  className,
  showLabel = false,
  color = 'primary'
}) => {
  const colorClasses = {
    primary: 'bg-primary',
    secondary: 'bg-secondary',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500'
  }

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="flex justify-between text-sm text-muted-foreground mb-2">
          <span>进度</span>
          <span>{Math.round(progress)}%</span>
        </div>
      )}
      <div className="w-full bg-secondary rounded-full h-2">
        <div 
          className={cn(
            "h-2 rounded-full transition-all duration-300 ease-out",
            colorClasses[color]
          )}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>
    </div>
  )
}

// 骨架屏组件映射 - 提取到模块级别避免每次渲染重新创建
const skeletonComponents = {
  chat: ChatSkeleton,
  search: SearchSkeleton,
  history: HistorySkeleton,
  settings: SettingsSkeleton,
  report: ReportSkeleton
} as const

// 自适应骨架屏 - 根据页面类型自动选择合适的骨架屏
export const AdaptiveSkeleton: React.FC<{
  pageType: keyof typeof skeletonComponents
  className?: string
}> = ({ pageType, className }) => {
  const SkeletonComponent = skeletonComponents[pageType]
  return <SkeletonComponent className={className} />
}

export { Loading, Skeleton, CardSkeleton, MessageSkeleton }