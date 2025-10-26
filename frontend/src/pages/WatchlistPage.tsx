/**
 * 项目监控列表页面
 * 展示用户收藏的加密货币项目
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWatchlist } from '../hooks/useWatchlist'
import api from '../services/api'

const WatchlistPage: React.FC = () => {
  const navigate = useNavigate()
  const { watchlist, removeFromWatchlist, clearWatchlist } = useWatchlist()
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [generatingReport, setGeneratingReport] = useState<string | null>(null)

  // 生成Deep Research报告
  const handleGenerateReport = async (symbol: string) => {
    try {
      setGeneratingReport(symbol)

      // 调用Deep Research API
      const response = await api.post('/api/v1/research/start', {
        symbol,
        project_name: watchlist.find((w) => w.symbol === symbol)?.name || symbol,
      })

      if (response.data.report_id) {
        // 跳转到分享页面查看报告
        const shareResponse = await api.post(`/api/v1/reports/${response.data.report_id}/share`, {
          expires_in_days: 7,
        })

        if (shareResponse.data.share_token) {
          navigate(`/shared/${shareResponse.data.share_token}`)
        }
      }
    } catch (error) {
      console.error('Failed to generate report:', error)
      alert('生成报告失败，请稍后重试')
    } finally {
      setGeneratingReport(null)
    }
  }

  // 处理清空监控列表
  const handleClearWatchlist = () => {
    if (showClearConfirm) {
      clearWatchlist()
      setShowClearConfirm(false)
    } else {
      setShowClearConfirm(true)
    }
  }

  // 格式化时间显示
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
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
            <h1 className="text-2xl font-bold text-gray-900">我的监控</h1>
            <span className="text-sm text-gray-500">
              {watchlist.length} / 20
            </span>
          </div>

          {watchlist.length > 0 && (
            <button
              onClick={handleClearWatchlist}
              className={`px-4 py-2 rounded-lg transition-colors ${
                showClearConfirm
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'text-red-600 hover:bg-red-50'
              }`}
            >
              {showClearConfirm ? '确认清空' : '清空监控'}
            </button>
          )}
        </div>
      </header>

      {/* 主内容区域 */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {watchlist.length === 0 ? (
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
                d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
              />
            </svg>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">暂无监控项目</h2>
            <p className="text-gray-600 mb-6">
              查看报告时点击星标按钮即可添加到监控列表
            </p>
            <button
              onClick={() => navigate('/')}
              className="btn-primary"
            >
              开始搜索
            </button>
          </div>
        ) : (
          // 监控列表网格
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {watchlist.map((item) => (
              <div
                key={item.symbol}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                {/* 项目信息 */}
                <div className="flex items-center gap-4 mb-4">
                  {item.icon && (
                    <img
                      src={item.icon}
                      alt={item.symbol}
                      className="w-12 h-12 rounded-full"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                      }}
                    />
                  )}
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900">{item.symbol}</h3>
                    <p className="text-sm text-gray-600">{item.name}</p>
                  </div>

                  {/* 删除按钮 */}
                  <button
                    onClick={() => removeFromWatchlist(item.symbol)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="从监控列表移除"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  </button>
                </div>

                {/* 添加日期 */}
                <p className="text-xs text-gray-500 mb-4">
                  添加于 {formatTime(item.addedAt)}
                </p>

                {/* 操作按钮 */}
                <button
                  onClick={() => handleGenerateReport(item.symbol)}
                  disabled={generatingReport === item.symbol}
                  className="w-full btn-primary flex items-center justify-center gap-2"
                >
                  {generatingReport === item.symbol ? (
                    <>
                      <svg
                        className="animate-spin h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                      生成中...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      生成Deep Research报告
                    </>
                  )}
                </button>
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

export default WatchlistPage
