import React, { lazy, Suspense } from 'react'
import { SkeletonLoader } from '../Loading/SkeletonLoader'
import componentPriorityManager from '../../utils/componentPriorityManager'

// 懒加载framer-motion组件（大型动画库）
const LazyFramerMotion = lazy(() => import('framer-motion').then(module => ({
  default: ({ children, ...props }: any) => {
    const MotionDiv = module.motion.div
    return <MotionDiv {...props}>{children}</MotionDiv>
  }
})))

// 懒加载recharts组件（大型图表库）
const LazyRecharts = lazy(() => import('recharts').then(module => ({
  default: module
})))

// 懒加载react-syntax-highlighter（代码高亮库）
const LazySyntaxHighlighter = lazy(() => import('react-syntax-highlighter').then(module => ({
  default: module.Prism || module.default
})))

/**
 * 懒加载包装器组件
 * 为大型第三方库提供懒加载和错误边界
 */
export function LazyComponentWrapper({
  children,
  fallback = <SkeletonLoader type="card" />,
  componentName,
}: {
  children: React.ReactNode
  fallback?: React.ReactNode
  componentName?: string
}) {
  // 记录组件加载时间
  React.useEffect(() => {
    if (componentName) {
      const startTime = performance.now()
      const timer = setTimeout(() => {
        const loadTime = performance.now() - startTime
        componentPriorityManager.recordUsage(componentName, loadTime)
      }, 100)

      return () => clearTimeout(timer)
    }
  }, [componentName])

  return (
    <Suspense fallback={fallback}>
      {children}
    </Suspense>
  )
}

/**
 * 按需加载图表组件
 */
export function LazyChart({ children }: { children: React.ReactNode }) {
  return (
    <LazyComponentWrapper fallback={<SkeletonLoader type="card" />}>
      {children}
    </LazyComponentWrapper>
  )
}

/**
 * 按需加载代码高亮组件
 */
export function LazyCodeBlock({ children }: { children: React.ReactNode }) {
  return (
    <LazyComponentWrapper fallback={<SkeletonLoader type="input" />}>
      {children}
    </LazyComponentWrapper>
  )
}

