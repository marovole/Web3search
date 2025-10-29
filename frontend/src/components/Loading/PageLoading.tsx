import React from 'react'
import { Loader } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PageLoadingProps {
  className?: string
  message?: string
}

/**
 * 页面加载状态组件
 * 用于路由懒加载时的加载指示
 */
export function PageLoading({ className, message = "加载中..." }: PageLoadingProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center min-h-[60vh] p-8",
      className
    )}>
      <div className="flex flex-col items-center gap-4">
        <Loader className="h-8 w-8 animate-spin text-primary" />
        <div className="text-center">
          <p className="text-sm font-medium text-foreground">{message}</p>
          <p className="text-xs text-muted-foreground mt-1">请稍候...</p>
        </div>
      </div>
    </div>
  )
}

/**
 * 骨架屏加载组件
 * 用于页面内容加载时的占位符
 */
export function SkeletonLoading() {
  return (
    <div className="min-h-[60vh] p-6 space-y-4 animate-pulse">
      <div className="space-y-2">
        <div className="h-4 bg-muted rounded w-3/4"></div>
        <div className="h-4 bg-muted rounded w-1/2"></div>
      </div>
      <div className="space-y-2">
        <div className="h-8 bg-muted rounded w-full"></div>
        <div className="h-8 bg-muted rounded w-full"></div>
        <div className="h-8 bg-muted rounded w-2/3"></div>
      </div>
      <div className="space-y-2">
        <div className="h-4 bg-muted rounded w-full"></div>
        <div className="h-4 bg-muted rounded w-full"></div>
        <div className="h-4 bg-muted rounded w-4/5"></div>
      </div>
    </div>
  )
}

/**
 * 聊天页面专用的加载组件
 */
export function ChatLoading() {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="text-center space-y-4">
        <Loader className="h-12 w-12 animate-spin text-primary mx-auto" />
        <div>
          <p className="font-medium">准备聊天界面</p>
          <p className="text-sm text-muted-foreground">正在初始化AI助手...</p>
        </div>
      </div>
    </div>
  )
}

/**
 * 报告页面专用的加载组件
 */
export function ReportLoading() {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="text-center space-y-4">
        <Loader className="h-12 w-12 animate-spin text-primary mx-auto" />
        <div>
          <p className="font-medium">生成报告中</p>
          <p className="text-sm text-muted-foreground">正在分析数据...</p>
        </div>
      </div>
    </div>
  )
}