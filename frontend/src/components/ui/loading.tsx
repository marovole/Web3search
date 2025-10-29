import * as React from "react"
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

export { Loading, Skeleton, CardSkeleton, MessageSkeleton }