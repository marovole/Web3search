/**
 * 报告历史记录页面
 * 展示用户查看过的所有报告
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useReportHistory } from '../hooks/useReportHistory'

const HistoryPage: React.FC = () => {
  const navigate = useNavigate()
  const { history, removeFromHistory, clearHistory } = useReportHistory()
  const [showClearConfirm, setShowClearConfirm] = useState(false)

  // 格式化时间显示
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    if (diffDays < 7) return `${diffDays}天前`
    return date.toLocaleDateString('zh-CN')
  }

  // 处理点击历史记录
  const handleClickHistory = (item: typeof history[0]) => {
    if (item.shareToken) {
      // 跳转到分享报告页面
      navigate(`/shared/${item.shareToken}`)
    } else {
      // 返回聊天页面
      navigate('/')
    }
  }

  // 处理清空历史
  const handleClearHistory = () => {
    if (showClearConfirm) {
      clearHistory()
      setShowClearConfirm(false)
    } else {
      setShowClearConfirm(true)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-gray-900">历史记录</h1>
          </div>

          {history.length > 0 && (
            <button
              onClick={handleClearHistory}
              className={`px-4 py-2 rounded-lg transition-colors ${
                showClearConfirm
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'text-red-600 hover:bg-red-50'
              }`}
            >
              {showClearConfirm ? '确认清空' : '清空历史'}
            </button>
          )}
        </div>
      </header>

      {/* 主内容区域 */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {history.length === 0 ? (
          // 空状态
          <div className="text-center py-20">
            <svg
              className="w-24 h-24 mx-auto text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">暂无历史记录</h2>
            <p className="text-gray-600 mb-6">开始搜索加密货币项目，查看AI分析报告</p>
            <button
              onClick={() => navigate('/')}
              className="btn-primary"
            >
              开始搜索
            </button>
          </div>
        ) : (
          // 历史记录列表
          <div className="space-y-4">
            {history.map((item) => (
              <div
                key={item.timestamp}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer group"
                onClick={() => handleClickHistory(item)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* 标题和符号 */}
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl font-bold text-gray-900">{item.symbol}</span>
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          item.reportType === 'deep_research'
                            ? 'bg-primary text-white'
                            : 'bg-gray-200 text-gray-700'
                        }`}
                      >
                        {item.reportType === 'deep_research' ? 'Deep Research' : 'Quick Chat'}
                      </span>
                    </div>

                    {/* 报告标题 */}
                    <h3 className="text-lg font-medium text-gray-900 mb-2 group-hover:text-primary transition-colors">
                      {item.title}
                    </h3>

                    {/* 时间 */}
                    <p className="text-sm text-gray-500">{formatTime(item.timestamp)}</p>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        removeFromHistory(item.timestamp)
                      }}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="删除记录"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>

                    <svg
                      className="w-6 h-6 text-gray-400 group-hover:text-primary transition-colors"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 取消清空确认 */}
        {showClearConfirm && (
          <div className="mt-4 text-center">
            <button
              onClick={() => setShowClearConfirm(false)}
              className="text-gray-600 hover:text-gray-900"
            >
              取消
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default HistoryPage
