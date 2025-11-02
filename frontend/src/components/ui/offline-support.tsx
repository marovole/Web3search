import React, { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  Download, 
  Upload,
  AlertCircle,
  CheckCircle
} from 'lucide-react'

/**
 * 网络状态类型
 */
export interface NetworkStatus {
  online: boolean
  effectiveType?: string
  downlink?: number
  rtt?: number
  saveData?: boolean
  type?: string
}

/**
 * 离线操作队列项
 */
interface OfflineOperation {
  id: string
  type: 'api' | 'mutation' | 'navigation'
  data: any
  timestamp: number
  retryCount: number
  maxRetries: number
}

/**
 * 网络状态Hook
 */
export const useNetworkStatus = () => {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>({
    online: navigator.onLine,
    effectiveType: '4g',
    downlink: 10,
    rtt: 100,
    saveData: false,
    type: 'unknown'
  })

  useEffect(() => {
    const updateOnlineStatus = () => {
      setNetworkStatus(prev => ({
        ...prev,
        online: navigator.onLine
      }))
    }

    const updateConnectionInfo = () => {
      if ('connection' in navigator) {
        const connection = (navigator as any).connection
        setNetworkStatus(prev => ({
          ...prev,
          effectiveType: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData,
          type: connection.type
        }))
      }
    }

    window.addEventListener('online', updateOnlineStatus)
    window.addEventListener('offline', updateOnlineStatus)
    
    updateConnectionInfo()

    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      connection.addEventListener('change', updateConnectionInfo)
    }

    return () => {
      window.removeEventListener('online', updateOnlineStatus)
      window.removeEventListener('offline', updateOnlineStatus)
      
      if ('connection' in navigator) {
        const connection = (navigator as any).connection
        connection.removeEventListener('change', updateConnectionInfo)
      }
    }
  }, [])

  return networkStatus
}

/**
 * 离线操作队列Hook
 */
export const useOfflineQueue = () => {
  const [queue, setQueue] = useState<OfflineOperation[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const { online } = useNetworkStatus()

  // 从localStorage恢复队列
  useEffect(() => {
    try {
      const savedQueue = localStorage.getItem('offlineQueue')
      if (savedQueue) {
        setQueue(JSON.parse(savedQueue))
      }
    } catch (error) {
      console.error('Failed to restore offline queue:', error)
    }
  }, [])

  // 保存队列到localStorage
  useEffect(() => {
    try {
      localStorage.setItem('offlineQueue', JSON.stringify(queue))
    } catch (error) {
      console.error('Failed to save offline queue:', error)
    }
  }, [queue])

  // 添加操作到队列
  const addToQueue = useCallback((operation: Omit<OfflineOperation, 'id' | 'timestamp' | 'retryCount'>) => {
    const newOperation: OfflineOperation = {
      ...operation,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      retryCount: 0
    }

    setQueue(prev => [...prev, newOperation])
  }, [])

  // 处理队列中的操作
  const processQueue = useCallback(async () => {
    if (!online || isProcessing || queue.length === 0) {
      return
    }

    setIsProcessing(true)

    try {
      const operation = queue[0]
      
      // 执行操作（这里需要根据实际业务逻辑实现）
      switch (operation.type) {
        case 'api':
          // 执行API调用
          break
        case 'mutation':
          // 执行数据变更
          break
        case 'navigation':
          // 执行导航
          break
      }

      // 移除已完成的操作
      setQueue(prev => prev.slice(1))
    } catch (error) {
      console.error('Failed to process offline operation:', error)
      
      // 更新重试次数
      setQueue(prev => {
        const updated = [...prev]
        if (updated[0]) {
          updated[0].retryCount++
          
          // 如果超过最大重试次数，移除操作
          if (updated[0].retryCount >= updated[0].maxRetries) {
            return prev.slice(1)
          }
        }
        return updated
      })
    } finally {
      setIsProcessing(false)
    }
  }, [online, isProcessing, queue])

  // 网络恢复时自动处理队列
  useEffect(() => {
    if (online && queue.length > 0 && !isProcessing) {
      processQueue()
    }
  }, [online, queue.length, isProcessing, processQueue])

  // 清空队列
  const clearQueue = useCallback(() => {
    setQueue([])
    localStorage.removeItem('offlineQueue')
  }, [])

  return {
    queue,
    addToQueue,
    processQueue,
    clearQueue,
    isProcessing
  }
}

/**
 * 离线存储Hook
 */
export const useOfflineStorage = () => {
  const [isSupported, setIsSupported] = useState(false)

  useEffect(() => {
    setIsSupported('serviceWorker' in navigator && 'caches' in window)
  }, [])

  const storeData = useCallback(async (key: string, data: any): Promise<void> => {
    if (!isSupported) {
      // 降级到localStorage
      localStorage.setItem(`offline_${key}`, JSON.stringify(data))
      return
    }

    try {
      const cache = await caches.open('offline-data')
      const response = new Response(JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' }
      })
      await cache.put(`/offline-data/${key}`, response)
    } catch (error) {
      console.error('Failed to store data offline:', error)
      // 降级到localStorage
      localStorage.setItem(`offline_${key}`, JSON.stringify(data))
    }
  }, [isSupported])

  const getData = useCallback(async (key: string): Promise<any> => {
    if (!isSupported) {
      // 从localStorage获取
      const data = localStorage.getItem(`offline_${key}`)
      return data ? JSON.parse(data) : null
    }

    try {
      const cache = await caches.open('offline-data')
      const response = await cache.match(`/offline-data/${key}`)
      return response ? await response.json() : null
    } catch (error) {
      console.error('Failed to get offline data:', error)
      // 降级到localStorage
      const data = localStorage.getItem(`offline_${key}`)
      return data ? JSON.parse(data) : null
    }
  }, [isSupported])

  const removeData = useCallback(async (key: string): Promise<void> => {
    if (!isSupported) {
      localStorage.removeItem(`offline_${key}`)
      return
    }

    try {
      const cache = await caches.open('offline-data')
      await cache.delete(`/offline-data/${key}`)
    } catch (error) {
      console.error('Failed to remove offline data:', error)
      localStorage.removeItem(`offline_${key}`)
    }
  }, [isSupported])

  const clearAllData = useCallback(async (): Promise<void> => {
    if (!isSupported) {
      // 清除所有offline_开头的localStorage项
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('offline_')) {
          localStorage.removeItem(key)
        }
      })
      return
    }

    try {
      await caches.delete('offline-data')
    } catch (error) {
      console.error('Failed to clear offline data:', error)
    }
  }, [isSupported])

  return {
    storeData,
    getData,
    removeData,
    clearAllData,
    isSupported
  }
}

/**
 * 网络状态指示器组件
 */
export const NetworkIndicator: React.FC<{
  className?: string
  showDetails?: boolean
}> = ({ className, showDetails = false }) => {
  const networkStatus = useNetworkStatus()
  const [showAlert, setShowAlert] = useState(false)

  useEffect(() => {
    if (!networkStatus.online) {
      setShowAlert(true)
    }
  }, [networkStatus.online])

  if (networkStatus.online && showAlert) {
    // 网络恢复3秒后隐藏提示
    const timer = setTimeout(() => setShowAlert(false), 3000)
    return () => clearTimeout(timer)
  }

  if (!showAlert) {
    return null
  }

  return (
    <Alert className={cn(
      "fixed top-4 right-4 z-50 max-w-sm animate-slide-in",
      networkStatus.online ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50",
      className
    )}>
      <div className="flex items-center gap-2">
        {networkStatus.online ? (
          <Wifi className="h-4 w-4 text-green-600" />
        ) : (
          <WifiOff className="h-4 w-4 text-red-600" />
        )}
        <AlertDescription className={cn(
          "text-sm",
          networkStatus.online ? "text-green-800" : "text-red-800"
        )}>
          {networkStatus.online ? '网络已恢复' : '网络连接已断开'}
        </AlertDescription>
      </div>
      
      {showDetails && !networkStatus.online && (
        <div className="mt-2 text-xs text-red-600">
          <div>类型: {networkStatus.effectiveType || '未知'}</div>
          <div>省流量: {networkStatus.saveData ? '是' : '否'}</div>
        </div>
      )}
    </Alert>
  )
}

/**
 * 离线页面组件
 */
export const OfflinePage: React.FC<{
  onRetry?: () => void
  className?: string
}> = ({ onRetry, className }) => {
  const { queue, clearQueue } = useOfflineQueue()
  const [retryCount, setRetryCount] = useState(0)

  const handleRetry = () => {
    setRetryCount(prev => prev + 1)
    onRetry?.()
  }

  return (
    <div className={cn(
      "flex flex-col items-center justify-center min-h-screen p-8 bg-background",
      className
    )}>
      <Card className="w-full max-w-md p-6 text-center space-y-4">
        <WifiOff className="w-16 h-16 text-muted-foreground mx-auto" />
        
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            离线模式
          </h1>
          <p className="text-muted-foreground">
            您当前处于离线状态。部分功能可能无法使用。
          </p>
        </div>

        {queue.length > 0 && (
          <div className="text-sm text-muted-foreground">
            <p>待同步操作: {queue.length}</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearQueue}
              className="mt-2"
            >
              清空队列
            </Button>
          </div>
        )}

        <div className="space-y-2">
          <Button onClick={handleRetry} className="w-full">
            <RefreshCw className="w-4 h-4 mr-2" />
            重试连接
          </Button>
          
          {retryCount > 2 && (
            <p className="text-xs text-muted-foreground">
              已重试 {retryCount} 次
            </p>
          )}
        </div>

        <div className="text-xs text-muted-foreground space-y-1">
          <p>• 您的数据将在网络恢复后自动同步</p>
          <p>• 部分页面可能仍可正常使用</p>
          <p>• 请检查您的网络连接</p>
        </div>
      </Card>
    </div>
  )
}

/**
 * 离线同步状态组件
 */
export const OfflineSyncStatus: React.FC<{
  className?: string
}> = ({ className }) => {
  const { queue, isProcessing } = useOfflineQueue()
  const { online } = useNetworkStatus()

  if (queue.length === 0 && online) {
    return (
      <div className={cn("flex items-center gap-2 text-green-600", className)}>
        <CheckCircle className="w-4 h-4" />
        <span className="text-sm">已同步</span>
      </div>
    )
  }

  if (isProcessing) {
    return (
      <div className={cn("flex items-center gap-2 text-blue-600", className)}>
        <RefreshCw className="w-4 h-4 animate-spin" />
        <span className="text-sm">同步中...</span>
      </div>
    )
  }

  if (queue.length > 0) {
    return (
      <div className={cn("flex items-center gap-2 text-orange-600", className)}>
        <Upload className="w-4 h-4" />
        <span className="text-sm">待同步 ({queue.length})</span>
      </div>
    )
  }

  return (
    <div className={cn("flex items-center gap-2 text-red-600", className)}>
      <WifiOff className="w-4 h-4" />
      <span className="text-sm">离线</span>
    </div>
  )
}

/**
 * 离线模式Provider
 */
export const OfflineProvider: React.FC<{
  children: React.ReactNode
}> = ({ children }) => {
  const networkStatus = useNetworkStatus()

  return (
    <>
      {children}
      <NetworkIndicator />
      
      {!networkStatus.online && (
        <div className="fixed bottom-4 left-4 z-40">
          <OfflineSyncStatus />
        </div>
      )}
    </>
  )
}
