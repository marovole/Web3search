import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

interface PreloadConfig {
  routes: string[]
  timeout?: number
  idleCallback?: boolean
}

/**
 * Ordered longest-prefix-first so `/agent-chat` wins over `/agents` and `/` is last.
 */
const ROUTE_PRELOAD_MODULES: ReadonlyArray<[string, () => Promise<unknown>]> = [
  ['/agent-dashboard', () => import('../pages/AgentDashboardPage')],
  ['/agent-chat', () => import('../pages/AgentChatPage')],
  ['/assistant', () => import('../pages/AgentChatPage')],
  ['/shared', () => import('../pages/SharedReportPage')],
  ['/recommendations', () => import('../pages/RecommendationsPage')],
  ['/notifications', () => import('../pages/NotificationsPage')],
  ['/github', () => import('../pages/GitHubSearchPage')],
  ['/history', () => import('../pages/HistoryPage')],
  ['/watchlist', () => import('../pages/WatchlistPage')],
  ['/settings', () => import('../pages/SettingsPage')],
  ['/search', () => import('../pages/SearchPage')],
  ['/reports', () => import('../pages/ReportsPage')],
  ['/portfolio', () => import('../pages/HoldingsPage')],
  ['/holdings', () => import('../pages/HoldingsPage')],
  ['/analytics', () => import('../pages/AnalyticsPage')],
  ['/agents', () => import('../pages/AgentsPage')],
  ['/upgrade', () => import('../pages/UpgradePage')],
  ['/discover', () => import('../pages/RecommendationsPage')],
  ['/chat', () => import('../pages/ChatPage')],
  ['/', () => import('../pages/ChatPage')],
]

export function preloadRouteModule(path: string): Promise<unknown> | undefined {
  const normalized = path.startsWith('/') ? path : `/${path}`
  const match = ROUTE_PRELOAD_MODULES.find(([prefix]) => {
    if (prefix === '/') {
      return normalized === '/' || normalized === ''
    }
    return normalized === prefix || normalized.startsWith(`${prefix}/`)
  })
  return match?.[1]()
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
    const preloadRoutes = () => {
      routes.forEach((route) => {
        if (preloadedRoutes.current.has(route)) {
          return
        }

        if (location.pathname === route) {
          return
        }

        preloadedRoutes.current.add(route)

        setTimeout(() => {
          preloadRouteModule(route)?.catch((error: unknown) => {
            console.warn(`Failed to preload route ${route}:`, error)
          })
        }, timeout)
      })
    }

    if (idleCallback && 'requestIdleCallback' in window) {
      const id = requestIdleCallback(preloadRoutes, { timeout: 5000 })
      return () => cancelIdleCallback(id)
    }
    const timer = setTimeout(preloadRoutes, timeout)
    return () => clearTimeout(timer)
  }, [location.pathname, routes, timeout, idleCallback])
}

/**
 * 智能预加载策略
 * 根据用户行为预加载可能访问的页面
 * 此hook必须在Router内部使用
 */
export function useSmartPreload() {
  const location = useLocation()

  useEffect(() => {
    let preloadTimer: ReturnType<typeof window.setTimeout> | undefined
    const initTimer = window.setTimeout(() => {
      let preloadTargets: string[] = []

      switch (location.pathname) {
        case '/':
        case '/chat':
          preloadTargets = ['/history', '/watchlist', '/search', '/settings']
          break
        case '/history':
          preloadTargets = ['/', '/watchlist', '/search']
          break
        case '/watchlist':
          preloadTargets = ['/', '/history', '/agents']
          break
        case '/shared':
          preloadTargets = ['/', '/history']
          break
        case '/search':
        case '/github':
          preloadTargets = ['/', '/reports', '/history']
          break
        case '/settings':
          preloadTargets = ['/', '/notifications', '/upgrade']
          break
        case '/agents':
        case '/agent-chat':
        case '/assistant':
          preloadTargets = ['/', '/agent-dashboard', '/analytics']
          break
        default:
          preloadTargets = ['/', '/settings', '/search']
      }

      preloadTimer = window.setTimeout(() => {
        try {
          preloadTargets.forEach((route) => {
            preloadRouteModule(route)?.catch((error: unknown) => {
              console.warn(`Failed to preload route ${route}:`, error)
            })
          })
        } catch (error) {
          console.warn('Error during route preloading:', error)
        }
      }, 3000)
    }, 100)

    return () => {
      window.clearTimeout(initTimer)
      if (preloadTimer !== undefined) {
        window.clearTimeout(preloadTimer)
      }
    }
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
          preloadRouteModule(href)?.catch((error: unknown) => {
            console.warn(`Failed to preload route ${href}:`, error)
          })
        }
      }
    }

    document.addEventListener('mouseenter', handleMouseEnter, true)
    return () => document.removeEventListener('mouseenter', handleMouseEnter, true)
  }, [])
}
