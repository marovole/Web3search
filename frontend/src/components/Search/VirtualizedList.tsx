import React, { useRef, useMemo } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { motion } from 'framer-motion'

interface VirtualizedListProps<T> {
  items: T[]
  renderItem: (item: T, index: number) => React.ReactNode
  estimateSize?: number
  overscan?: number
  className?: string
  containerClassName?: string
  enableVirtualization?: boolean
}

/**
 * 虚拟滚动列表组件
 * 当项目数量超过阈值时自动启用虚拟滚动以优化性能
 */
export function VirtualizedList<T>({
  items,
  renderItem,
  estimateSize = 200,
  overscan = 5,
  className = '',
  containerClassName = '',
  enableVirtualization = true
}: VirtualizedListProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null)

  // 计算是否启用虚拟滚动（当项目数量 > 100 时）
  const shouldVirtualize = enableVirtualization && items.length > 100

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    overscan
  })

  // 如果不需要虚拟滚动，直接渲染所有项目
  if (!shouldVirtualize) {
    return (
      <div className={containerClassName}>
        <div className={className}>
          {items.map((item, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.02 }}
            >
              {renderItem(item, index)}
            </motion.div>
          ))}
        </div>
      </div>
    )
  }

  // 虚拟滚动渲染
  const virtualItems = virtualizer.getVirtualItems()

  return (
    <div
      ref={parentRef}
      className={`overflow-auto ${containerClassName}`}
      style={{ height: '100%', width: '100%' }}
    >
      <div
        className={className}
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative'
        }}
      >
        {virtualItems.map((virtualItem) => {
          const item = items[virtualItem.index]
          if (item === undefined) return null
          return (
            <div
              key={virtualItem.key}
              data-index={virtualItem.index}
              ref={virtualizer.measureElement}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`
              }}
            >
              {renderItem(item, virtualItem.index)}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default VirtualizedList

