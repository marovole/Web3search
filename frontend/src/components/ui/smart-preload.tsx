import React, { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { useResourcePreload } from './optimized-image'

/**
 * 缓存策略类型
 */
export type CacheStrategy = 'memory' | 'localStorage' | 'sessionStorage' | 'indexedDB' | 'serviceWorker'

/**
 * 预加载优先级
 */
export type PreloadPriority = 'low' | 'medium' | 'high' | 'critical'

/**
 * 资源类型
 */
export type ResourceType = 'image' | 'script' | 'style' | 'font' | 'data' | 'route'

/**
 * 预加载配置
 */
export interface PreloadConfig {
  url: string
  type: ResourceType
  priority: PreloadPriority
  strategy?: CacheStrategy
  timeout?: number
  retryCount?: number
  dependencies?: string[]
}

/**
 * 缓存项接口
 */
interface CacheItem<T = any> {
  data: T
  timestamp: number
  expiresAt?: number
  accessCount: number
  lastAccessed: number
}

/**
 * 智能缓存管理器
 */
class SmartCacheManager {
  private memoryCache = new Map<string, CacheItem>()
  private readonly DEFAULT_TTL = 5 * 60 * 1000 // 5分钟
  private readonly MAX_MEMORY_ITEMS = 100

  /**
   * 设置缓存项
   */
  set<T>(key: string, data: T, ttl?: number): void {
    const now = Date.now()
    const expiresAt = ttl ? now + ttl : now + this.DEFAULT_TTL

    // 如果内存缓存已满，清理最久未访问的项
    if (this.memoryCache.size >= this.MAX_MEMORY_ITEMS) {
      this.evictLeastRecentlyUsed()
    }

    this.memoryCache.set(key, {
      data,
      timestamp: now,
      expiresAt,
      accessCount: 0,
      lastAccessed: now
    })
  }

  /**
   * 获取缓存项
   */
  get<T>(key: string): T | null {
    const item = this.memoryCache.get(key)
    
    if (!item) {
      return null
    }

    // 检查是否过期
    if (item.expiresAt && Date.now() > item.expiresAt) {
      this.memoryCache.delete(key)
      return null
    }

    // 更新访问统计
    item.accessCount++
    item.lastAccessed = Date.now()

    return item.data as T
  }

  /**
   * 删除缓存项
   */
  delete(key: string): boolean {
    return this.memoryCache.delete(key)
  }

  /**
   * 清空缓存
   */
  clear(): void {
    this.memoryCache.clear()
  }

  /**
   * 清理过期项
   */
  cleanup(): void {
    const now = Date.now()
    for (const [key, item] of this.memoryCache.entries()) {
      if (item.expiresAt && now > item.expiresAt) {
        this.memoryCache.delete(key)
      }
    }
  }

  /**
   * 驱逐最少使用的项
   */
  private evictLeastRecentlyUsed(): void {
    let oldestKey = ''
    let oldestTime = Date.now()

    for (const [key, item] of this.memoryCache.entries()) {
      if (item.lastAccessed < oldestTime) {
        oldestTime = item.lastAccessed
        oldestKey = key
      }
    }

    if (oldestKey) {
      this.memoryCache.delete(oldestKey)
    }
  }

  /**
   * 获取缓存统计
   */
  getStats() {
    return {
      size: this.memoryCache.size,
      maxSize: this.MAX_MEMORY_ITEMS,
      items: Array.from(this.memoryCache.entries()).map(([key, item]) => ({
        key,
        size: JSON.stringify(item.data).length,
        accessCount: item.accessCount,
        lastAccessed: item.lastAccessed,
        expiresAt: item.expiresAt
      }))
    }
  }
}

// 全局缓存管理器实例
const cacheManager = new SmartCacheManager()

/**
 * 静态资源预加载队列（与 `hooks/usePreloadRoutes` 的路由预加载区分）
 */
export const useAssetPreloadQueue = () => {
  const { preloadImage, preloadImages, preloadScript, preloadStylesheet } = useResourcePreload()
  const [preloadingQueue, setPreloadingQueue] = useState<PreloadConfig[]>([])
  const [completedPreloads, setCompletedPreloads] = useState<Set<string>>(new Set())
  const [failedPreloads, setFailedPreloads] = useState<Set<string>>(new Set())
  const isPreloading = useRef(false)

  /**
   * 添加预加载任务
   */
  const addPreloadTask = useCallback((config: PreloadConfig) => {
    setPreloadingQueue(prev => [...prev, config].sort((a, b) => {
      const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
      return priorityOrder[b.priority] - priorityOrder[a.priority]
    }))
  }, [])

  /**
   * 执行预加载
   */
  const executePreload = useCallback(async (config: PreloadConfig): Promise<void> => {
    const { url, type, timeout = 10000, retryCount = 3 } = config

    let attempts = 0
    while (attempts <= retryCount) {
      try {
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Preload timeout')), timeout)
        })

        let preloadPromise: Promise<void>

        switch (type) {
          case 'image':
            preloadPromise = preloadImage(url)
            break
          case 'script':
            preloadPromise = preloadScript(url)
            break
          case 'style':
            preloadPromise = preloadStylesheet(url)
            break
          default:
            preloadPromise = Promise.resolve()
        }

        await Promise.race([preloadPromise, timeoutPromise])
        
        setCompletedPreloads(prev => new Set(prev).add(url))
        return
      } catch (error) {
        attempts++
        if (attempts > retryCount) {
          setFailedPreloads(prev => new Set(prev).add(url))
          throw error
        }
        // 指数退避重试
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempts) * 1000))
      }
    }
  }, [preloadImage, preloadScript, preloadStylesheet])

  /**
   * 处理预加载队列
   */
  const processQueue = useCallback(async () => {
    if (isPreloading.current || preloadingQueue.length === 0) {
      return
    }

    isPreloading.current = true

    try {
      const config = preloadingQueue[0]
      await executePreload(config)
      
      setPreloadingQueue(prev => prev.slice(1))
    } catch (error) {
      console.error('Preload failed:', error)
      setPreloadingQueue(prev => prev.slice(1))
    } finally {
      isPreloading.current = false
    }
  }, [preloadingQueue, executePreload])

  // 自动处理队列
  useEffect(() => {
    if (preloadingQueue.length > 0 && !isPreloading.current) {
      processQueue()
    }
  }, [preloadingQueue, processQueue])

  /**
   * 预加载路由组件
   */
  const preloadRoute = useCallback((routePath: string, componentImport: () => Promise<any>) => {
    addPreloadTask({
      url: routePath,
      type: 'route',
      priority: 'medium'
    })

    // 缓存组件
    cacheManager.set(`route:${routePath}`, componentImport, 10 * 60 * 1000) // 10分钟
  }, [addPreloadTask])

  /**
   * 预加载关键资源
   */
  const preloadCriticalResources = useCallback((resources: string[]) => {
    resources.forEach(url => {
      addPreloadTask({
        url,
        type: 'image',
        priority: 'critical'
      })
    })
  }, [addPreloadTask])

  return {
    addPreloadTask,
    preloadRoute,
    preloadCriticalResources,
    preloadingQueue,
    completedPreloads,
    failedPreloads
  }
}

/**
 * 缓存Hook
 */
// eslint-disable-next-line @typescript-eslint/naming-convention
export function useCache<T>(key: string, fetcher: () => Promise<T>, ttl?: number) {
  const [data, setData] = useState<T | null>(() => cacheManager.get<T>(key))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await fetcher()
      cacheManager.set(key, result, ttl)
      setData(result)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [key, fetcher, ttl])

  const refresh = useCallback(() => {
    cacheManager.delete(key)
    fetchData()
  }, [key, fetchData])

  useEffect(() => {
    if (!data) {
      fetchData()
    }
  }, [data, fetchData])

  return { data, loading, error, refresh }
}

/**
 * 网络感知预加载Hook
 */
export const useNetworkAwarePreload = () => {
  const [networkInfo, setNetworkInfo] = useState({
    effectiveType: '4g' as string,
    downlink: 10,
    rtt: 100,
    saveData: false
  })

  const { addPreloadTask } = useAssetPreloadQueue()

  useEffect(() => {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      
      const updateNetworkInfo = () => {
        setNetworkInfo({
          effectiveType: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData
        })
      }

      updateNetworkInfo()
      connection.addEventListener('change', updateNetworkInfo)

      return () => {
        connection.removeEventListener('change', updateNetworkInfo)
      }
    }
  }, [])

  const adaptivePreload = useCallback((config: PreloadConfig) => {
    // 根据网络状况调整预加载策略
    let adjustedConfig = { ...config }

    if (networkInfo.saveData) {
      // 省流量模式下只预加载关键资源
      if (config.priority !== 'critical') {
        return
      }
    }

    switch (networkInfo.effectiveType) {
      case 'slow-2g':
      case '2g':
        // 慢速网络：只预加载关键资源，增加超时时间
        if (config.priority !== 'critical') {
          return
        }
        adjustedConfig.timeout = 15000
        break
      case '3g':
        // 3G网络：优先预加载高优先级资源
        if (config.priority === 'low') {
          return
        }
        adjustedConfig.timeout = 12000
        break
      default:
        // 4G/快速网络：正常预加载
        adjustedConfig.timeout = 8000
    }

    addPreloadTask(adjustedConfig)
  }, [networkInfo, addPreloadTask])

  return {
    networkInfo,
    adaptivePreload
  }
}

/**
 * 预加载管理器组件
 */
export const PreloadManager: React.FC<{
  children: React.ReactNode
  resources?: PreloadConfig[]
}> = ({ children, resources = [] }) => {
  const { addPreloadTask, completedPreloads, failedPreloads } = useAssetPreloadQueue()

  useEffect(() => {
    resources.forEach(addPreloadTask)
  }, [resources, addPreloadTask])

  return <>{children}</>
}

/**
 * 缓存统计组件
 */
export const CacheStats: React.FC<{
  className?: string
}> = ({ className }) => {
  const [stats, setStats] = useState(cacheManager.getStats())

  useEffect(() => {
    const interval = setInterval(() => {
      setStats(cacheManager.getStats())
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className={cn("text-xs space-y-1 p-3 bg-muted rounded", className)}>
      <div>缓存项数: {stats.size}/{stats.maxSize}</div>
      <div>内存使用: {Math.round(stats.items.reduce((acc, item) => acc + item.size, 0) / 1024)}KB</div>
      <div>总访问次数: {stats.items.reduce((acc, item) => acc + item.accessCount, 0)}</div>
    </div>
  )
}
