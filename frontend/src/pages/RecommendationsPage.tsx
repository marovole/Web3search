import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useRecommendations } from '../hooks/useRecommendations'
import RecommendationCard from '../components/Recommendations/RecommendationCard'

const RecommendationsPage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const {
    recommendations,
    loading,
    error,
    total,
    fetchRecommendations,
    submitFeedback,
    dismissRecommendation
  } = useRecommendations()

  const [statusFilter, setStatusFilter] = useState('active')

  useEffect(() => {
    if (isAuthenticated) {
      fetchRecommendations(statusFilter)
    }
  }, [isAuthenticated, statusFilter, fetchRecommendations])

  const handleLike = async (id: string) => {
    try {
      await submitFeedback(id, 'like')
    } catch {
      console.error('Failed to submit feedback')
    }
  }

  const handleDislike = async (id: string) => {
    try {
      await submitFeedback(id, 'dislike')
    } catch {
      console.error('Failed to submit feedback')
    }
  }

  const handleDismiss = async (id: string) => {
    try {
      await dismissRecommendation(id)
    } catch {
      console.error('Failed to dismiss')
    }
  }

  if (!isAuthenticated && !loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">需要登录</h2>
          <p className="text-gray-600 mb-6">
            登录后查看 AI 为您发现的投资机会。
          </p>
          <button
            onClick={() => navigate('/auth/login')}
            className="w-full px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
          >
            立即登录
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
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
            <div>
              <h1 className="text-2xl font-bold text-gray-900">投资机会</h1>
              <p className="text-xs text-gray-500 mt-1">
                {loading ? '加载中...' : `共 ${total} 个推荐`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="active">待查看</option>
              <option value="liked">已喜欢</option>
              <option value="all">全部</option>
            </select>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {loading && recommendations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <svg className="animate-spin w-10 h-10 text-indigo-600 mb-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <p className="text-gray-500">正在加载推荐...</p>
          </div>
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-600">{error}</p>
            <button
              onClick={() => fetchRecommendations(statusFilter)}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              重试
            </button>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-xl border border-gray-200 border-dashed">
            <div className="w-24 h-24 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">暂无推荐</h2>
            <p className="text-gray-600 mb-4 max-w-md mx-auto">
              AI 会根据您的偏好和市场热度，每周为您发现新的投资机会。
            </p>
            <p className="text-sm text-gray-500">
              下次推荐将在每周三上午10点生成。
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.map((rec) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                onLike={handleLike}
                onDislike={handleDislike}
                onDismiss={handleDismiss}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

export default RecommendationsPage
