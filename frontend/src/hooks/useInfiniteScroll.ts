import { useEffect, useRef, useCallback, useState } from 'react'

interface UseInfiniteScrollOptions {
  hasNextPage: boolean
  isFetching: boolean
  fetchNextPage: () => void
  threshold?: number
  enabled?: boolean
}

/**
 * 无限滚动 Hook
 * 使用 Intersection Observer API 检测滚动到底部时自动加载更多
 */
export function useInfiniteScroll({
  hasNextPage,
  isFetching,
  fetchNextPage,
  threshold = 0.1,
  enabled = true
}: UseInfiniteScrollOptions) {
  const [isIntersecting, setIsIntersecting] = useState(false)
  const observerTarget = useRef<HTMLDivElement>(null)

  const handleIntersect = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries
      setIsIntersecting(entry.isIntersecting)

      if (entry.isIntersecting && hasNextPage && !isFetching && enabled) {
        fetchNextPage()
      }
    },
    [hasNextPage, isFetching, fetchNextPage, enabled]
  )

  useEffect(() => {
    const target = observerTarget.current
    if (!target || !enabled) return

    const observer = new IntersectionObserver(handleIntersect, {
      threshold,
      rootMargin: '100px' // 提前 100px 开始加载
    })

    observer.observe(target)

    return () => {
      observer.unobserve(target)
    }
  }, [handleIntersect, threshold, enabled])

  return {
    observerTarget,
    isIntersecting
  }
}

export default useInfiniteScroll

