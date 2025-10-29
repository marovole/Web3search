import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

interface PreloadConfig {
  routes: string[]
  timeout?: number
  idleCallback?: boolean
}

/**
 * 路由预加载Hook
 * 在用户空闲时预加载可能访问的页面组件
 */
export function usePreloadRoutes(config: PreloadConfig) {
  const { routes, timeout = 2000, idleCallback = true } = config
  const location = useLocation()
  const preloadedRoutes = useRef<Set<string>>(new Set())

  useEffect(() => {
    // 预加载逻辑
    const preloadRoutes = () => {
      routes.forEach(route => {
        // 如果已经预加载过，跳过
        if (preloadedRoutes.current.has(route)) {
          return
        }

        // 如果当前就在这个路由，不需要预加载
        if (location.pathname === route) {
          return
        }

        // 开始预加载
        preloadedRoutes.current.add(route)

        // 根据路由路径动态导入对应组件
        const componentMap: Record<string, () => Promise<any>> = {
          '/': () => import('../pages/ChatPage'),
          '/shared': () => import('../pages/SharedReportPage'),
          '/history': () => import('../pages/HistoryPage'),
          '/watchlist': () => import('../pages/WatchlistPage'),
        }

        // 精确匹配或路径匹配
        const preloadKey = Object.keys(componentMap).find(key =>
          route === key || route.startsWith(key)
        )

        if (preloadKey) {
          // 使用setTimeout避免阻塞主线程
          setTimeout(() => {
            componentMap[preloadKey]().catch(error => {
              console.warn(`Failed to preload route ${route}:`, error)
            })
          }, timeout)
        }
      })
    }

    if (idleCallback && 'requestIdleCallback' in window) {
      // 使用requestIdleCallback在空闲时预加载
      const id = requestIdleCallback(preloadRoutes, { timeout: 5000 })
      return () => cancelIdleCallback(id)
    } else {
      // 降级方案：使用setTimeout
      const timer = setTimeout(preloadRoutes, timeout)
      return () => clearTimeout(timer)
    }
  }, [location.pathname, routes, timeout, idleCallback])
}

/**
 * 智能预加载策略
 * 根据用户行为预加载相关页面
 */
export function useSmartPreload() {
  const location = useLocation()

  useEffect(() => {
    // 根据当前路径预加载可能访问的页面
    let preloadTargets: string[] = []

    switch (location.pathname) {
      case '/':
        // 首页用户可能访问历史记录或监控列表
        preloadTargets = ['/history', '/watchlist']
        break
      case '/history':
        // 历史记录用户可能返回首页或查看监控列表
        preloadTargets = ['/watchlist', '/']
        break
      case '/watchlist':
        // 监控列表用户可能访问历史记录或返回首页
        preloadTargets = ['/history', '/']
        break
      case '/shared':
        // 分享页面用户可能访问首页
        preloadTargets = ['/']
        break
      default:
        // 默认预加载首页
        preloadTargets = ['/']
    }

    // 延迟预加载，避免影响当前页面加载
    const timer = setTimeout(() => {
      preloadTargets.forEach(route => {
        const componentMap: Record<string, () => Promise<any>> = {
          '/': () => import('../pages/ChatPage'),
          '/shared': () => import('../pages/SharedReportPage'),
          '/history': () => import('../pages/HistoryPage'),
          '/watchlist': () => import('../pages/WatchlistPage'),
        }

        const preloadKey = Object.keys(componentMap).find(key =>
          route === key || route.startsWith(key)
        )

        if (preloadKey) {
          componentMap[preloadKey]().catch(error => {
            console.warn(`Failed to preload route ${route}:`, error)
          })
        }
      })
    }, 3000) // 3秒后开始预加载

    return () => clearTimeout(timer)
  }, [location.pathname])
}

/**
 * 鼠标悬停预加载
 * 当用户悬停在链接上时立即预加载对应页面
 */
export function useHoverPreload() {
  useEffect(() => {
    const handleMouseEnter = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      const link = target.closest('a[href]')

      if (link) {
        const href = link.getAttribute('href')
        if (href && href.startsWith('/')) {
          // 立即预加载悬停的链接
          const componentMap: Record<string, () => Promise<any>> = {
            '/': () => import('../pages/ChatPage'),
            '/shared': () => import('../pages/SharedReportPage'),
            '/history': () => import('../pages/HistoryPage'),
            '/watchlist': () => import('../pages/WatchlistPage'),
          }

          const preloadKey = Object.keys(componentMap).find(key =>
            href === key || href.startsWith(key)
          )

          if (preloadKey) {
            componentMap[preloadKey]().catch(error => {
              console.warn(`Failed to preload route ${href}:`, error)
            })
          }
        }
      }
    }

    document.addEventListener('mouseenter', handleMouseEnter, true)
    return () => document.removeEventListener('mouseenter', handleMouseEnter, true)
  }, [])
}