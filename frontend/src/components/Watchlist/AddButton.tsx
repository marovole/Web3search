/**
 * 添加到监控列表按钮组件
 * 集成到报告查看器中
 */

import React, { useState } from 'react'
import { useWatchlist } from '../../hooks/useWatchlist'

interface AddButtonProps {
  symbol: string
  name?: string
  icon?: string
}

const AddButton: React.FC<AddButtonProps> = ({ symbol, name, icon }) => {
  const { isInWatchlist, addToWatchlist, removeFromWatchlist } = useWatchlist()
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')

  const inWatchlist = isInWatchlist(symbol)

  const showToastMessage = (message: string) => {
    setToastMessage(message)
    setShowToast(true)
    setTimeout(() => setShowToast(false), 3000)
  }

  const handleToggleWatchlist = () => {
    if (inWatchlist) {
      // 从监控列表移除
      removeFromWatchlist(symbol)
      showToastMessage(`已从监控列表移除 ${symbol}`)
    } else {
      // 添加到监控列表
      try {
        addToWatchlist({
          symbol,
          name: name || symbol,
          icon,
        })
        showToastMessage(`已添加 ${symbol} 到监控列表`)
      } catch (error) {
        showToastMessage('添加失败：监控列表已满（最多20个）')
      }
    }
  }

  return (
    <>
      <button
        onClick={handleToggleWatchlist}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
          inWatchlist
            ? 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100 border border-yellow-300'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
        }`}
        title={inWatchlist ? '从监控列表移除' : '添加到监控列表'}
      >
        {/* 星标图标 */}
        <svg
          className="w-5 h-5"
          fill={inWatchlist ? 'currentColor' : 'none'}
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
          />
        </svg>
        <span className="text-sm font-medium">
          {inWatchlist ? '已监控' : '添加监控'}
        </span>
      </button>

      {/* Toast 通知 */}
      {showToast && (
        <div className="fixed bottom-4 right-4 bg-gray-900 text-white px-6 py-3 rounded-lg shadow-lg animate-fade-in z-50">
          {toastMessage}
        </div>
      )}
    </>
  )
}

export default AddButton
