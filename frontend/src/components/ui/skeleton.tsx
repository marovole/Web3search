import React from 'react'
import { cn } from '@/lib/utils'

/**
 * 骨架屏组件接口
 */
export interface SkeletonProps {
  className?: string
  children?: React.ReactNode
}

/**
 * 基础骨架屏元素
 */
export const Skeleton: React.FC<SkeletonProps> = ({ className, ...props }) => {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className
      )}
      {...props}
    />
  )
}

/**
 * 头像骨架屏
 */
export const AvatarSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <Skeleton
      className={cn(
        "h-10 w-10 rounded-full",
        className
      )}
    />
  )
}

/**
 * 文本骨架屏
 */
export const TextSkeleton: React.FC<{ 
  lines?: number
  className?: string 
  lineClassName?: string
}> = ({ 
  lines = 3, 
  className,
  lineClassName
}) => {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton
          key={i}
          className={cn(
            "h-4",
            i === lines - 1 && "w-3/4",
            lineClassName
          )}
        />
      ))}
    </div>
  )
}

/**
 * 标题骨架屏
 */
export const TitleSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <Skeleton className={cn("h-6 w-1/3 mb-4", className)} />
  )
}

/**
 * 按钮骨架屏
 */
export const ButtonSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <Skeleton className={cn("h-10 w-20", className)} />
  )
}

/**
 * 输入框骨架屏
 */
export const InputSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <div className={cn("space-y-2", className)}>
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-4 w-1/4" />
    </div>
  )
}

/**
 * 卡片骨架屏
 */
export const CardSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <div className={cn(
      "rounded-lg border bg-card p-4 space-y-4",
      className
    )}>
      <div className="flex items-center space-x-4">
        <AvatarSkeleton />
        <div className="flex-1">
          <TitleSkeleton />
          <TextSkeleton lines={2} />
        </div>
      </div>
      <TextSkeleton lines={3} />
    </div>
  )
}

/**
 * 聊天消息骨架屏
 */
export const ChatMessageSkeleton: React.FC<{ 
  isUser?: boolean
  className?: string 
}> = ({ 
  isUser = false,
  className 
}) => {
  return (
    <div className={cn(
      "flex gap-3 p-4",
      isUser && "flex-row-reverse",
      className
    )}>
      <AvatarSkeleton />
      <div className={cn(
        "flex-1 space-y-2 max-w-[80%]",
        isUser && "items-end"
      )}>
        <Skeleton className={cn(
          "h-4 w-20",
          isUser && "w-16"
        )} />
        <div className={cn(
          "rounded-lg p-3 space-y-2",
          isUser ? "bg-primary/20" : "bg-muted"
        )}>
          <TextSkeleton lines={3} lineClassName="h-4" />
        </div>
      </div>
    </div>
  )
}

/**
 * 聊天界面骨架屏
 */
export const ChatSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* 聊天头部 */}
      <div className="border-b p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <AvatarSkeleton />
            <div>
              <Skeleton className="h-5 w-32 mb-2" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
          <ButtonSkeleton />
        </div>
      </div>

      {/* 聊天消息区域 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <ChatMessageSkeleton />
        <ChatMessageSkeleton isUser />
        <ChatMessageSkeleton />
      </div>

      {/* 输入区域 */}
      <div className="border-t p-4">
        <InputSkeleton />
      </div>
    </div>
  )
}

/**
 * 搜索结果骨架屏
 */
export const SearchSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <div className={cn("space-y-4", className)}>
      {/* 搜索框 */}
      <InputSkeleton />
      
      {/* 搜索结果列表 */}
      <div className="space-y-3">
        {Array.from({ length: 5 }, (_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    </div>
  )
}

/**
 * 历史记录骨架屏
 */
export const HistorySkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <div className={cn("space-y-4", className)}>
      <TitleSkeleton />
      <div className="space-y-3">
        {Array.from({ length: 3 }, (_, i) => (
          <div key={i} className="border rounded-lg p-4 space-y-3">
            <div className="flex justify-between items-start">
              <TextSkeleton lines={2} />
              <Skeleton className="h-8 w-20" />
            </div>
            <TextSkeleton lines={1} />
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * 设置页面骨架屏
 */
export const SettingsSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <div className={cn("space-y-6", className)}>
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="space-y-4">
          <TitleSkeleton />
          <div className="space-y-3">
            {Array.from({ length: 2 }, (_, j) => (
              <div key={j} className="flex items-center justify-between p-3 border rounded">
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-48" />
                </div>
                <Skeleton className="h-6 w-16" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * 报告页面骨架屏
 */
export const ReportSkeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <div className={cn("space-y-6", className)}>
      {/* 报告头部 */}
      <div className="space-y-3">
        <TitleSkeleton />
        <TextSkeleton lines={2} />
      </div>

      {/* 报告内容 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 图表区域 */}
        <div className="space-y-4">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-48 w-full" />
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

/**
 * 自适应骨架屏 - 根据页面类型自动选择合适的骨架屏
 */
export const AdaptiveSkeleton: React.FC<{
  pageType: 'chat' | 'search' | 'history' | 'settings' | 'report'
  className?: string
}> = ({ pageType, className }) => {
  const skeletonComponents = {
    chat: ChatSkeleton,
    search: SearchSkeleton,
    history: HistorySkeleton,
    settings: SettingsSkeleton,
    report: ReportSkeleton
  }

  const SkeletonComponent = skeletonComponents[pageType]
  return <SkeletonComponent className={className} />
}
