import { useEffect, useState } from 'react'

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
 * 使用vite-plugin-pwa的registerSW进行Service Worker管理
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
    // 原生注册/获取现有 Service Worker
    const ensureRegistration = async () => {
      try {
        // 如果已经注册，直接使用现有 registration
        const existing = await navigator.serviceWorker.getRegistration()
        let registration = existing || null
        if (!registration) {
          registration = await navigator.serviceWorker.register('/sw.js')
        }

        setStatus(prev => ({
          ...prev,
          isRegistered: true,
          registration,
        }))

        if (registration.active) {
          setStatus(prev => ({
            ...prev,
            isActivated: true,
            version: registration.active?.scriptURL || null,
          }))
        }

        // 监听更新
        registration.addEventListener('updatefound', () => {
          const newWorker = registration!.installing
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                setUpdateAvailable(true)
                console.log('New Service Worker available')
              }
            })
          }
        })
      } catch (error) {
        console.error('Service Worker registration failed:', error)
        setStatus(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Unknown error',
        }))
      }
    }
    ensureRegistration()

    // 监听网络状态
    const handleOnline = () => setOffline(false)
    const handleOffline = () => setOffline(true)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // 监听Service Worker控制变化
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      console.log('Service Worker controller changed')
      window.location.reload()
    })

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const activateUpdate = () => {
    if (status.registration?.waiting) {
      status.registration.waiting.postMessage({ type: 'SKIP_WAITING' })
    }
    // 重新加载页面以应用更新
    window.location.reload()
  }

  const clearCache = async () => {
    try {
      if ('caches' in window) {
        const cacheNames = await caches.keys()
        await Promise.all(cacheNames.map(name => caches.delete(name)))
        console.log('Cache cleared successfully')
        // 重新加载页面
        window.location.reload()
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
