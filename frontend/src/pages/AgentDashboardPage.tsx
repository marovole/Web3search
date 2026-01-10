/**
 * Agent Dashboard Page
 * Overview of agent tasks, activity logs, and statistics
 */

import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useAgentActivity } from '../hooks/useAgentActivity'
import {
  TASK_TYPE_LABELS,
  TASK_TYPE_ICONS,
  EVENT_TYPE_LABELS,
  STATUS_COLORS,
} from '../types/agent-activity'
import type { AgentTaskType, AgentActivityEvent } from '../types/agent-activity'

const AgentDashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const {
    dashboard,
    logs,
    loading,
    logsLoading,
    refresh,
    loadLogs,
  } = useAgentActivity()

  const [activeTab, setActiveTab] = useState<'overview' | 'logs'>('overview')
  const [selectedTaskType, setSelectedTaskType] = useState<AgentTaskType | ''>('')

  // Load logs when switching to logs tab
  useEffect(() => {
    if (activeTab === 'logs' && logs.length === 0) {
      loadLogs(selectedTaskType ? { taskType: selectedTaskType as AgentTaskType } : {})
    }
  }, [activeTab, logs.length, loadLogs, selectedTaskType])

  // Auth guard
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-gray-800 rounded-2xl shadow-xl p-8 text-center border border-gray-700">
          <h2 className="text-2xl font-bold text-white mb-2">Agent 仪表盘</h2>
          <p className="text-gray-400 mb-6">登录后查看您的 Agent 任务状态和执行日志。</p>
          <button
            onClick={() => navigate('/auth/login')}
            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors"
          >
            立即登录
          </button>
        </div>
      </div>
    )
  }

  const stats = dashboard?.stats

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800/80 backdrop-blur-sm border-b border-gray-700/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-xl font-bold text-white">Agent 仪表盘</h1>
              <p className="text-xs text-gray-400">监控和管理您的智能任务</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/agent-chat')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              AI 助手
            </button>
            <button
              onClick={refresh}
              disabled={loading}
              className="px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors"
            >
              <svg className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1 border-b border-gray-700/50">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                activeTab === 'overview'
                  ? 'text-white'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              概览
              {activeTab === 'overview' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                activeTab === 'logs'
                  ? 'text-white'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              执行日志
              {activeTab === 'logs' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {loading && !dashboard ? (
          <div className="flex items-center justify-center py-20">
            <svg className="w-8 h-8 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
        ) : activeTab === 'overview' ? (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="活动任务" value={stats?.active_tasks || 0} icon="✅" />
              <StatCard label="今日执行" value={stats?.runs_today || 0} icon="⚡" />
              <StatCard label="本周成功率" value={`${stats?.success_rate_7d || 100}%`} icon="📊" />
              <StatCard label="今日通知" value={stats?.notifications_sent_today || 0} icon="🔔" />
            </div>

            {/* Task Type Breakdown */}
            <div className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">任务类型</h2>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {Object.entries(TASK_TYPE_LABELS).map(([type, label]) => {
                  const typeStats = stats?.by_task_type?.[type as AgentTaskType]
                  return (
                    <div
                      key={type}
                      className="bg-gray-700/30 rounded-lg p-4 hover:bg-gray-700/50 transition-colors cursor-pointer"
                      onClick={() => navigate('/agents')}
                    >
                      <div className="text-2xl mb-2">{TASK_TYPE_ICONS[type as AgentTaskType]}</div>
                      <div className="text-sm font-medium text-white">{label}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {typeStats?.active || 0} 活动 / {typeStats?.count || 0} 总计
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Recent Runs */}
            <div className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">最近执行</h2>
              {dashboard?.recentRuns && dashboard.recentRuns.length > 0 ? (
                <div className="space-y-2">
                  {dashboard.recentRuns.slice(0, 5).map((run) => (
                    <div
                      key={run.id}
                      className="flex items-center justify-between p-3 bg-gray-700/20 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{TASK_TYPE_ICONS[run.task_type as AgentTaskType] || '📋'}</span>
                        <div>
                          <div className="text-sm font-medium text-white">{run.task_name}</div>
                          <div className="text-xs text-gray-400">{TASK_TYPE_LABELS[run.task_type as AgentTaskType] || run.task_type}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-xs px-2 py-1 rounded-full ${
                          run.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                          run.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {run.status === 'completed' ? '完成' : run.status === 'failed' ? '失败' : '运行中'}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {new Date(run.started_at).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400">
                  <p>暂无执行记录</p>
                  <button
                    onClick={() => navigate('/agent-chat')}
                    className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                  >
                    创建第一个任务
                  </button>
                </div>
              )}
            </div>

            {/* Active Tasks */}
            <div className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">活动任务</h2>
                <button
                  onClick={() => navigate('/agents')}
                  className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  查看全部 →
                </button>
              </div>
              {dashboard?.activeTasks && dashboard.activeTasks.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {dashboard.activeTasks.slice(0, 4).map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between p-4 bg-gray-700/20 rounded-lg hover:bg-gray-700/30 transition-colors cursor-pointer"
                      onClick={() => navigate('/agents')}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{TASK_TYPE_ICONS[task.type as AgentTaskType] || '📋'}</span>
                        <div>
                          <div className="text-sm font-medium text-white">{task.name}</div>
                          <div className="text-xs text-gray-400">
                            {task.run_count} 次执行
                          </div>
                        </div>
                      </div>
                      <div className={`w-2 h-2 rounded-full ${
                        task.status === 'active' ? 'bg-green-400' : 'bg-yellow-400'
                      }`} />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400">
                  <p>暂无活动任务</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Logs Tab */
          <div className="space-y-4">
            {/* Filter */}
            <div className="flex items-center gap-4">
              <select
                value={selectedTaskType}
                onChange={(e) => {
                  const value = e.target.value as AgentTaskType | ''
                  setSelectedTaskType(value)
                  loadLogs(value ? { taskType: value } : {})
                }}
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">全部类型</option>
                {Object.entries(TASK_TYPE_LABELS).map(([type, label]) => (
                  <option key={type} value={type}>{label}</option>
                ))}
              </select>
            </div>

            {/* Logs List */}
            {logsLoading && logs.length === 0 ? (
              <div className="flex items-center justify-center py-20">
                <svg className="w-8 h-8 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
            ) : logs.length > 0 ? (
              <div className="space-y-2">
                {logs.map((event: AgentActivityEvent) => (
                  <div
                    key={event.id}
                    className="flex items-start gap-4 p-4 bg-gray-800/50 border border-gray-700/50 rounded-lg"
                  >
                    <span className="text-xl flex-shrink-0">{TASK_TYPE_ICONS[event.task_type as AgentTaskType] || '📋'}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-white">{event.task_name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[event.status]}`}>
                          {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
                        </span>
                      </div>
                      <p className="text-sm text-gray-400 mt-1">{event.message}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        {new Date(event.created_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-20 text-gray-400">
                <p>暂无执行日志</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

// Stat Card Component
interface StatCardProps {
  label: string
  value: string | number
  icon: string
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon }) => (
  <div className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-4">
    <div className="flex items-center justify-between mb-2">
      <span className="text-2xl">{icon}</span>
    </div>
    <div className="text-2xl font-bold text-white">{value}</div>
    <div className="text-xs text-gray-400">{label}</div>
  </div>
)

export default AgentDashboardPage
