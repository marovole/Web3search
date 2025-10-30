import { useEffect, useState } from 'react'
import cacheVersionManager from '../utils/cacheVersionManager'

interface ServiceWorkerStatus {
  isSupported: boolean
  isRegistered: boolean
  isActivated: boolean
  registration: ServiceWorkerRegistration | null
  version: string | null
  error: string | null
}

/**
 * Service Worker管理Hook
 * 处理Service Worker的注册、更新和通信
 */
export function useServiceWorker() {
  const [status, setStatus] = useState<ServiceWorkerStatus>({
    isSupported: false,
    isRegistered: false,
    isActivated: false,
    registration: null,
    version: null,
    error: null,
  })

  const [updateAvailable, setUpdateAvailable] = useState(false)
  const [offline, setOffline] = useState(false)

  useEffect(() => {
    // 检查Service Worker支持
    if (!('serviceWorker' in navigator)) {
      console.warn('Service Worker not supported')
      setStatus(prev => ({ ...prev, isSupported: false }))
      return
    }

    setStatus(prev => ({ ...prev, isSupported: true }))

    // 注册Service Worker
    registerServiceWorker()

    // 监听网络状态
    const handleOnline = () => setOffline(false)
    const handleOffline = () => setOffline(true)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const registerServiceWorker = async () => {
    try {
      // 检查缓存版本
      const expectedVersion = '1.0.0'
      if (cacheVersionManager.shouldUpdateCache(expectedVersion)) {
        console.log('Cache version update needed, clearing old caches...')
        await cacheVersionManager.cleanupOldCaches()
      }

      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      })

      console.log('Service Worker registered:', registration)

      // 更新缓存版本信息
      cacheVersionManager.updateVersion(
        expectedVersion,
        'web3search-static-v1.0.0',
        'web3search-api-v1.0.0'
      )

      setStatus(prev => ({
        ...prev,
        isRegistered: true,
        registration,
      }))

      // 检查激活状态
      if (registration.active) {
        setStatus(prev => ({
          ...prev,
          isActivated: true,
        }))
        getVersion(registration)
      }

      // 监听Service Worker更新
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              setUpdateAvailable(true)
              console.log('New Service Worker available')
            }
          })
        }
      })

      // 监听Service Worker控制变化
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('Service Worker controller changed')
        window.location.reload()
      })

    } catch (error) {
      console.error('Service Worker registration failed:', error)
      setStatus(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error',
      }))
    }
  }

  const getVersion = async (registration: ServiceWorkerRegistration) => {
    try {
      if (registration.active) {
        const messageChannel = new MessageChannel()

        const getVersionPromise = new Promise<string>((resolve) => {
          messageChannel.port1.onmessage = (event) => {
            resolve(event.data.version)
          }
        })

        registration.active.postMessage(
          { type: 'GET_VERSION' },
          [messageChannel.port2]
        )

        const version = await getVersionPromise
        setStatus(prev => ({ ...prev, version }))
      }
    } catch (error) {
      console.error('Failed to get Service Worker version:', error)
    }
  }

  const activateUpdate = () => {
    if (status.registration?.waiting) {
      status.registration.waiting.postMessage({ type: 'SKIP_WAITING' })
    }
  }

  const clearCache = async () => {
    try {
      if (status.registration?.active) {
        const messageChannel = new MessageChannel()

        const clearCachePromise = new Promise<boolean>((resolve, reject) => {
          messageChannel.port1.onmessage = (event) => {
            if (event.data.success) {
              resolve(true)
            } else {
              reject(new Error(event.data.error))
            }
          }
        })

        status.registration.active.postMessage(
          { type: 'CLEAR_CACHE' },
          [messageChannel.port2]
        )

        await clearCachePromise
        console.log('Cache cleared successfully')
      }
    } catch (error) {
      console.error('Failed to clear cache:', error)
      throw error
    }
  }

  return {
    status,
    updateAvailable,
    offline,
    activateUpdate,
    clearCache,
  }
}

/**
 * 离线状态管理Hook
 */
export function useOfflineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [offlineSince, setOfflineSince] = useState<Date | null>(null)

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      setOfflineSince(null)
    }

    const handleOffline = () => {
      setIsOnline(false)
      setOfflineSince(new Date())
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return {
    isOnline,
    offlineSince,
  }
}