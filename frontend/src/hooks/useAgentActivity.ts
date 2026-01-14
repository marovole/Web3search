/**
 * useAgentActivity Hook
 * Fetches agent dashboard stats and activity logs
 */

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import type {
  AgentDashboardStats,
  AgentRunSummary,
  AgentTaskStatus,
  AgentActivityEvent,
  AgentTaskType,
} from '../types/agent-activity'

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || ''

interface DashboardData {
  stats: AgentDashboardStats
  recentRuns: AgentRunSummary[]
  activeTasks: AgentTaskStatus[]
}

interface UseAgentActivityReturn {
  dashboard: DashboardData | null
  logs: AgentActivityEvent[]
  loading: boolean
  logsLoading: boolean
  error: string | null
  refresh: () => Promise<void>
  loadLogs: (filters?: { taskType?: AgentTaskType; taskId?: string }) => Promise<void>
  loadMoreLogs: () => Promise<void>
  hasMoreLogs: boolean
}

export function useAgentActivity(): UseAgentActivityReturn {
  const { token } = useAuth()
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [logs, setLogs] = useState<AgentActivityEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [logsLoading, setLogsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasMoreLogs, setHasMoreLogs] = useState(false)
  const [logsOffset, setLogsOffset] = useState(0)
  const [currentFilters, setCurrentFilters] = useState<{ taskType?: AgentTaskType; taskId?: string }>({})

  const fetchDashboard = useCallback(async () => {
    if (!token) return

    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE_URL}/api/v1/agents/activity/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      setDashboard({
        stats: data.stats,
        recentRuns: data.recent_runs || [],
        activeTasks: data.active_tasks || [],
      })
    } catch (err) {
      console.error('[useAgentActivity] Dashboard error:', err)
      setError(err instanceof Error ? err.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [token])

  const loadLogs = useCallback(async (filters: { taskType?: AgentTaskType; taskId?: string } = {}) => {
    if (!token) return

    try {
      setLogsLoading(true)
      setCurrentFilters(filters)
      setLogsOffset(0)

      const params = new URLSearchParams()
      if (filters.taskType) params.set('task_type', filters.taskType)
      if (filters.taskId) params.set('task_id', filters.taskId)
      params.set('limit', '50')
      params.set('offset', '0')

      const response = await fetch(`${API_BASE_URL}/api/v1/agents/activity/logs?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      setLogs(data.events || [])
      setHasMoreLogs(data.has_more || false)
      setLogsOffset(50)
    } catch (err) {
      console.error('[useAgentActivity] Logs error:', err)
    } finally {
      setLogsLoading(false)
    }
  }, [token])

  const loadMoreLogs = useCallback(async () => {
    if (!token || logsLoading || !hasMoreLogs) return

    try {
      setLogsLoading(true)

      const params = new URLSearchParams()
      if (currentFilters.taskType) params.set('task_type', currentFilters.taskType)
      if (currentFilters.taskId) params.set('task_id', currentFilters.taskId)
      params.set('limit', '50')
      params.set('offset', String(logsOffset))

      const response = await fetch(`${API_BASE_URL}/api/v1/agents/activity/logs?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      setLogs(prev => [...prev, ...(data.events || [])])
      setHasMoreLogs(data.has_more || false)
      setLogsOffset(prev => prev + 50)
    } catch (err) {
      console.error('[useAgentActivity] Load more logs error:', err)
    } finally {
      setLogsLoading(false)
    }
  }, [token, logsLoading, hasMoreLogs, logsOffset, currentFilters])

  const refresh = useCallback(async () => {
    await fetchDashboard()
  }, [fetchDashboard])

  // Initial fetch
  useEffect(() => {
    if (token) {
      fetchDashboard()
    }
  }, [token, fetchDashboard])

  return {
    dashboard,
    logs,
    loading,
    logsLoading,
    error,
    refresh,
    loadLogs,
    loadMoreLogs,
    hasMoreLogs,
  }
}

export default useAgentActivity
