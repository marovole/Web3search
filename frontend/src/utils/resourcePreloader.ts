/**
 * 资源预加载管理器
 * 管理关键资源的预加载和预连接
 */

class ResourcePreloader {
  private preloadedLinks: Set<string> = new Set()
  private preconnectedDomains: Set<string> = new Set()

  /**
   * DNS预连接
   */
  preconnect(url: string, crossOrigin: boolean = false) {
    if (this.preconnectedDomains.has(url)) return

    const domain = new URL(url).origin
    const link = document.createElement('link')
    link.rel = 'preconnect'
    link.href = domain
    if (crossOrigin) {
      link.crossOrigin = 'anonymous'
    }
    document.head.appendChild(link)
    this.preconnectedDomains.add(domain)
  }

  /**
   * DNS预解析
   */
  dnsPrefetch(url: string) {
    const domain = new URL(url).origin
    if (this.preconnectedDomains.has(domain)) return

    const link = document.createElement('link')
    link.rel = 'dns-prefetch'
    link.href = domain
    document.head.appendChild(link)
  }

  /**
   * 预加载资源
   */
  preload(resource: string, options: { as?: string; type?: string; crossorigin?: boolean } = {}) {
    if (this.preloadedLinks.has(resource)) return

    const link = document.createElement('link')
    link.rel = 'preload'
    link.href = resource
    if (options.as) link.as = options.as
    if (options.type) link.type = options.type
    if (options.crossorigin) link.crossOrigin = 'anonymous'
    document.head.appendChild(link)
    this.preloadedLinks.add(resource)
  }

  /**
   * 预获取资源（低优先级）
   */
  prefetch(resource: string) {
    if (this.preloadedLinks.has(resource)) return

    const link = document.createElement('link')
    link.rel = 'prefetch'
    link.href = resource
    document.head.appendChild(link)
    this.preloadedLinks.add(resource)
  }

  /**
   * 预加载下一可能访问的页面
   */
  prefetchRoute(route: string) {
    this.prefetch(route)
  }

  /**
   * 初始化关键资源预加载
   */
  initialize() {
    // DNS预连接API服务器
    const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    if (apiUrl) {
      this.preconnect(apiUrl, true)
    }

    // 预加载关键字体（如果有）
    // this.preload('/fonts/inter.woff2', { as: 'font', type: 'font/woff2', crossorigin: true })

    // 使用requestIdleCallback延迟预加载非关键资源
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        // 预加载可能访问的路由
        const possibleRoutes = ['/history', '/watchlist', '/settings']
        possibleRoutes.forEach(route => {
          this.prefetchRoute(route)
        })
      }, { timeout: 2000 })
    }
  }
}

// 创建全局实例
const resourcePreloader = new ResourcePreloader()

// 自动初始化
if (typeof window !== 'undefined') {
  // 立即执行关键预连接
  resourcePreloader.initialize()

  // 页面加载完成后预加载更多资源
  window.addEventListener('load', () => {
    // 延迟预加载，避免影响当前页面
    setTimeout(() => {
      resourcePreloader.initialize()
    }, 1000)
  })
}

export default resourcePreloader
export { ResourcePreloader }

