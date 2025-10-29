import React, { useState, useEffect } from 'react'

const OfflineIndicator: React.FC = () => {
  const [isOnline, setIsOnline] = useState(true)
  const [showOfflineMessage, setShowOfflineMessage] = useState(false)

  useEffect(() => {
    // 初始化网络状态
    setIsOnline(navigator.onLine)

    // 监听网络状态变化
    const handleOnline = () => {
      setIsOnline(true)
      setShowOfflineMessage(false)
    }

    const handleOffline = () => {
      setIsOnline(false)
      setShowOfflineMessage(true)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // 如果在线且不需要显示离线消息，则不渲染
  if (isOnline && !showOfflineMessage) {
    return null
  }

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-50 transform transition-transform duration-300 ${
        isOnline ? 'translate-y-0' : 'translate-y-0'
      }`}
    >
      <div
        className={`${
          isOnline ? 'bg-green-500' : 'bg-orange-500'
        } text-white text-center py-2 px-4 text-sm font-medium shadow-lg`}
      >
        {isOnline ? (
          <div className="flex items-center justify-center gap-2">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            网络连接已恢复
          </div>
        ) : (
          <div className="flex items-center justify-center gap-2">
            <svg
              className="w-4 h-4 animate-pulse"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            网络连接已断开，请检查网络设置
          </div>
        )}
      </div>

      {/* 为固定导航栏添加顶部间距 */}
      {!isOnline && <div className="h-10"></div>}
    </div>
  )
}

export default OfflineIndicator