import React, { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface ResponsiveChartProps {
  title: string
  description?: string
  children: React.ReactNode
  className?: string
  height?: number
}

/**
 * 响应式图表容器
 * 自动适配容器宽度，优化移动端显示
 */
export function ResponsiveChart({
  title,
  description,
  children,
  className,
  height = 300
}: ResponsiveChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // 响应式处理逻辑
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const resizeObserver = new ResizeObserver(() => {
      // 触发重绘事件
      container.dispatchEvent(new CustomEvent('chart:resize'))
    })

    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className={cn(
        "w-full bg-card rounded-lg border border-border p-4",
        "hover:shadow-md transition-shadow",
        className
      )}
      style={{ height: 'auto' }}
    >
      {/* 图表标题 */}
      <div className="mb-4">
        <h3 className="text-base font-semibold">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        )}
      </div>

      {/* 图表内容 */}
      <div
        className="relative overflow-hidden"
        style={{ height: 'auto' }}
      >
        {children}
      </div>
    </div>
  )
}

interface ChartLegendProps {
  items: Array<{
    label: string
    color: string
    value?: string | number
  }>
  className?: string
}

/**
 * 响应式图表图例
 * 在移动端自动换行
 */
export function ChartLegend({ items, className }: ChartLegendProps) {
  return (
    <div className={cn(
      "flex flex-wrap gap-x-4 gap-y-2 mt-4",
      "text-sm",
      className
    )}>
      {items.map((item, index) => (
        <div key={index} className="flex items-center gap-2">
          <span
            className="w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-muted-foreground">{item.label}</span>
          {item.value !== undefined && (
            <span className="font-medium text-foreground">{item.value}</span>
          )}
        </div>
      ))}
    </div>
  )
}

interface SimpleBarChartProps {
  data: Array<{
    label: string
    value: number
    color?: string
  }>
  maxValue?: number
  className?: string
}

/**
 * 简单响应式柱状图
 * 适配移动端显示
 */
export function SimpleBarChart({
  data,
  maxValue,
  className
}: SimpleBarChartProps) {
  const max = maxValue || Math.max(...data.map(d => d.value))

  return (
    <div className={cn("space-y-3", className)}>
      {data.map((item, index) => {
        const percentage = (item.value / max) * 100

        return (
          <div key={index} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium truncate flex-1">{item.label}</span>
              <span className="text-muted-foreground ml-2">{item.value}</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="h-full rounded-full"
                style={{ backgroundColor: item.color || 'var(--primary)' }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

interface SimpleLineChartProps {
  data: Array<{
    label: string
    value: number
  }>
  className?: string
}

/**
 * 简单响应式折线图
 * 适配移动端显示
 */
export function SimpleLineChart({
  data,
  className
}: SimpleLineChartProps) {
  const max = Math.max(...data.map(d => d.value))
  const min = Math.min(...data.map(d => d.value))
  const range = max - min || 1

  const points = data.map((item, index) => {
    const x = (index / (data.length - 1)) * 100
    const y = 100 - ((item.value - min) / range) * 100
    return `${x},${y}`
  }).join(' ')

  return (
    <div className={cn("relative h-48", className)}>
      <svg
        className="w-full h-full"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        {/* 网格线 */}
        <defs>
          <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.1"/>
          </pattern>
        </defs>
        <rect width="100" height="100" fill="url(#grid)" />

        {/* 折线 */}
        <polyline
          points={points}
          fill="none"
          stroke="var(--primary)"
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
        />

        {/* 数据点 */}
        {data.map((item, index) => {
          const x = (index / (data.length - 1)) * 100
          const y = 100 - ((item.value - min) / range) * 100
          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r="1.5"
              fill="var(--primary)"
            />
          )
        })}
      </svg>

      {/* X轴标签（简化显示） */}
      <div className="flex justify-between mt-2 text-xs text-muted-foreground">
        <span>{data[0]?.label}</span>
        <span>{data[data.length - 1]?.label}</span>
      </div>
    </div>
  )
}
