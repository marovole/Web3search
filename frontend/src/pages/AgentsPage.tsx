/**
 * AI Agents Task Management Page
 * Manage automated research and monitoring tasks
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAgentTasks, AgentTask } from '../hooks/useAgentTasks'
import { useAuth } from '../contexts/AuthContext'
import { CreateTaskModal } from '../components/Agents'
import { QuickPriceAlertCard } from '@/components/Agents/QuickPriceAlertCard'

const AgentsPage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const {
    tasks,
    loading,
    pauseTask,
    resumeTask,
    deleteTask,
    createTask
  } = useAgentTasks()

  const [processingId, setProcessingId] = useState<string | null>(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  // Quick Price Alert Card State
  const [alertSymbol, setAlertSymbol] = useState('')
  const [alertThreshold, setAlertThreshold] = useState('')
  const [alertError, setAlertError] = useState<string | null>(null)
  const [isAlertSubmitting, setIsAlertSubmitting] = useState(false)

  // 1. Task Type Icons & Labels
  const getTaskTypeInfo = (type: AgentTask['task_type']) => {
    switch (type) {
      case 'price_alert':
        return {
          label: '价格预警',
          icon: (
            <svg aria-hidden="true" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          ),
          color: 'text-yellow-600 bg-yellow-50'
        }
      case 'risk_monitor':
        return {
          label: '风险监控',
          icon: (
            <svg aria-hidden="true" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          ),
          color: 'text-red-600 bg-red-50'
        }
      case 'news_brief':
        return {
          label: '新闻速报',
          icon: (
            <svg aria-hidden="true" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
            </svg>
          ),
          color: 'text-blue-600 bg-blue-50'
        }
      case 'portfolio_health':
        return {
          label: '持仓诊断',
          icon: (
            <svg aria-hidden="true" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          ),
          color: 'text-purple-600 bg-purple-50'
        }
      case 'opportunity_finder':
        return {
          label: '机会发现',
          icon: (
            <svg aria-hidden="true" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          ),
          color: 'text-amber-600 bg-amber-50'
        }
      default:
        return {
          label: '自定义',
          icon: (
            <svg aria-hidden="true" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          ),
          color: 'text-gray-600 bg-gray-50'
        }
    }
  }

  // 2. Status Badge Helper
  const getStatusBadge = (status: AgentTask['status']) => {
    switch (status) {
      case 'active':
        return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">运行中</span>
      case 'paused':
        return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">已暂停</span>
      case 'completed':
        return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">已完成</span>
      case 'cancelled':
        return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">已取消</span>
      default:
        return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">{status}</span>
    }
  }

  // 3. Handlers
  const handleToggleStatus = async (task: AgentTask) => {
    try {
      setProcessingId(task.id)
      if (task.status === 'active') {
        await pauseTask(task.id)
      } else {
        await resumeTask(task.id)
      }
    } finally {
      setProcessingId(null)
    }
  }

  const handleDelete = async (id: string) => {
    if (window.confirm('确定要删除这个任务吗？此操作无法撤销。')) {
      try {
        setProcessingId(id)
        await deleteTask(id)
      } finally {
        setProcessingId(null)
      }
    }
  }

  const handleOpenCreateModal = () => {
    setIsCreateModalOpen(true)
  }

  // Quick Price Alert Handlers
  const handleAlertSubmit = async () => {
    setAlertError(null)

    const symbol = alertSymbol.trim().toUpperCase()
    const thresholdValue = Number.parseFloat(alertThreshold)

    if (!symbol) {
      setAlertError('请输入代币符号')
      return
    }

    if (!Number.isFinite(thresholdValue) || thresholdValue <= 0) {
      setAlertError('请输入有效的目标价格')
      return
    }

    setIsAlertSubmitting(true)

    try {
      const task = await createTask({
        name: `${symbol} 跌破 $${thresholdValue}`,
        description: `提醒我当 ${symbol} 跌破 $${thresholdValue}`,
        type: 'price_alert',
        config: {
          token: symbol,
          condition: 'below',
          target_price: thresholdValue
        }
      })

      if (!task) {
        setAlertError('创建价格预警失败，请重试')
        return
      }

      setAlertSymbol('')
      setAlertThreshold('')
    } catch (error) {
      setAlertError(error instanceof Error ? error.message : '创建价格预警失败')
    } finally {
      setIsAlertSubmitting(false)
    }
  }

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return '-'
    return new Date(timestamp).toLocaleString('zh-CN', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // 4. Auth Check View
  if (!isAuthenticated && !loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg aria-hidden="true" className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">需要登录</h2>
          <p className="text-gray-600 mb-6">
            请登录后管理您的 AI 智能体任务。登录后您可以创建价格预警、风险监控等自动化任务。
          </p>
          <button type="button"
            onClick={() => navigate('/auth/login')}
            className="w-full btn-primary py-3 rounded-lg font-medium"
          >
            立即登录
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button type="button"
              onClick={() => navigate('/')}
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg aria-hidden="true" className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI 智能体任务</h1>
              <p className="text-xs text-gray-500 mt-1">
                {loading ? '加载中...' : `共 ${tasks.length} 个任务`}
              </p>
            </div>
          </div>

          <button type="button"
            onClick={handleOpenCreateModal}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 shadow-sm"
          >
            <svg aria-hidden="true" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建任务
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Quick Price Alert Card - Placed above task list */}
        <div className="mb-8 max-w-md">
          <QuickPriceAlertCard
            symbol={alertSymbol}
            threshold={alertThreshold}
            onSymbolChange={(value) => {
              setAlertSymbol(value)
              setAlertError(null)
            }}
            onThresholdChange={(value) => {
              setAlertThreshold(value)
              setAlertError(null)
            }}
            onSubmit={handleAlertSubmit}
            isSubmitting={isAlertSubmitting}
            error={alertError}
          />
        </div>

        {loading ? (
          // Loading State
          <div className="flex flex-col items-center justify-center py-20">
            <svg aria-hidden="true" className="animate-spin w-10 h-10 text-blue-600 mb-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <p className="text-gray-500">正在加载任务列表...</p>
          </div>
        ) : tasks.length === 0 ? (
          // Empty State
          <div className="text-center py-20">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg aria-hidden="true" className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">暂无智能体任务</h2>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              创建一个 AI 智能体来帮您自动监控价格、分析风险或搜集新闻。全天候 24/7 运行，不错过任何机会。
            </p>
            <button type="button"
              onClick={handleOpenCreateModal}
              className="btn-primary text-lg px-8 py-3"
            >
              创建第一个任务
            </button>
          </div>
        ) : (
          // Task Grid
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tasks.map((task) => {
              const typeInfo = getTaskTypeInfo(task.task_type)
              const isProcessing = processingId === task.id
              
              return (
                <div
                  key={task.id}
                  className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 transition-all hover:shadow-md ${
                    task.status === 'paused' ? 'opacity-75' : ''
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${typeInfo.color}`}>
                        {typeInfo.icon}
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-900 line-clamp-1" title={task.name}>
                          {task.name}
                        </h3>
                        <div className="text-xs text-gray-500 flex items-center gap-1">
                          {typeInfo.label}
                        </div>
                      </div>
                    </div>
                    {getStatusBadge(task.status)}
                  </div>

                  {/* Card Body */}
                  <div className="space-y-3 mb-6">
                    <p className="text-sm text-gray-600 line-clamp-2 min-h-[2.5rem]">
                      {task.description || '暂无描述'}
                    </p>
                    
                    <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-500">上次运行</span>
                        <span className="font-medium text-gray-900">{formatTime(task.last_run_at)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">下次运行</span>
                        <span className="font-medium text-gray-900">{formatTime(task.next_run_at)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">运行次数</span>
                        <span className="font-medium text-gray-900">
                          {task.run_count} (成功 {task.success_count})
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Card Footer Actions */}
                  <div className="flex items-center gap-3 pt-4 border-t border-gray-100">
                    <button type="button"
                      onClick={() => handleToggleStatus(task)}
                      disabled={isProcessing}
                      className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
                        task.status === 'active'
                          ? 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100'
                          : 'bg-green-50 text-green-700 hover:bg-green-100'
                      }`}
                    >
                      {isProcessing ? (
                        <svg aria-hidden="true" className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                      ) : task.status === 'active' ? (
                        <>
                          <svg aria-hidden="true" className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          暂停
                        </>
                      ) : (
                        <>
                          <svg aria-hidden="true" className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          恢复
                        </>
                      )}
                    </button>
                    
                    <button type="button"
                      onClick={() => handleDelete(task.id)}
                      disabled={isProcessing}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="删除任务"
                    >
                      <svg aria-hidden="true" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>

      <CreateTaskModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  )
}

export default AgentsPage
