/**
 * 缓存版本管理器
 * 管理Service Worker缓存版本和更新策略
 */

interface CacheVersion {
  version: string
  timestamp: number
  staticCache: string
  apiCache: string
}

class CacheVersionManager {
  private readonly VERSION_KEY = 'sw-cache-version'
  private readonly VERSION_CHECK_INTERVAL = 24 * 60 * 60 * 1000 // 24小时检查一次

  /**
   * 获取当前缓存版本
   */
  getCurrentVersion(): CacheVersion | null {
    try {
      const stored = localStorage.getItem(this.VERSION_KEY)
      if (stored) {
        return JSON.parse(stored)
      }
    } catch (error) {
      console.error('Failed to get cache version:', error)
    }
    return null
  }

  /**
   * 设置缓存版本
   */
  setVersion(version: CacheVersion): void {
    try {
      localStorage.setItem(this.VERSION_KEY, JSON.stringify(version))
    } catch (error) {
      console.error('Failed to set cache version:', error)
    }
  }

  /**
   * 检查是否需要更新缓存
   */
  shouldUpdateCache(newVersion: string): boolean {
    const current = this.getCurrentVersion()
    
    if (!current) {
      return true // 没有版本信息，需要初始化
    }

    if (current.version !== newVersion) {
      return true // 版本不匹配，需要更新
    }

    // 检查是否超过检查间隔
    const now = Date.now()
    if (now - current.timestamp > this.VERSION_CHECK_INTERVAL) {
      return true // 超过检查间隔，需要更新
    }

    return false
  }

  /**
   * 更新缓存版本
   */
  updateVersion(version: string, staticCache: string, apiCache: string): void {
    const versionInfo: CacheVersion = {
      version,
      timestamp: Date.now(),
      staticCache,
      apiCache,
    }
    this.setVersion(versionInfo)
  }

  /**
   * 清理过期缓存
   */
  async cleanupOldCaches(): Promise<void> {
    try {
      if ('caches' in window) {
        const cacheNames = await caches.keys()
        const current = this.getCurrentVersion()
        
        if (current) {
          const validCaches = new Set([current.staticCache, current.apiCache])
          
          for (const cacheName of cacheNames) {
            if (!validCaches.has(cacheName)) {
              console.log('Cleaning up old cache:', cacheName)
              await caches.delete(cacheName)
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to cleanup old caches:', error)
    }
  }

  /**
   * 获取缓存统计信息
   */
  async getCacheStats(): Promise<{
    totalSize: number
    cacheCount: number
    cacheNames: string[]
  }> {
    try {
      if (!('caches' in window)) {
        return { totalSize: 0, cacheCount: 0, cacheNames: [] }
      }

      const cacheNames = await caches.keys()
      let totalSize = 0

      for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName)
        const keys = await cache.keys()
        
        for (const request of keys) {
          const response = await cache.match(request)
          if (response) {
            const blob = await response.blob()
            totalSize += blob.size
          }
        }
      }

      return {
        totalSize,
        cacheCount: cacheNames.length,
        cacheNames,
      }
    } catch (error) {
      console.error('Failed to get cache stats:', error)
      return { totalSize: 0, cacheCount: 0, cacheNames: [] }
    }
  }
}

// 创建全局实例
const cacheVersionManager = new CacheVersionManager()

export default cacheVersionManager
export { CacheVersionManager }
export type { CacheVersion }

