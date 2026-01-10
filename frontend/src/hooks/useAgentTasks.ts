import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'

export interface AgentTask {
  id: string
  user_id: string
  name: string
  description?: string
  task_type: 'price_alert' | 'risk_monitor' | 'news_brief' | 'portfolio_health' | 'opportunity_finder' | 'custom'
  config: Record<string, unknown>
  schedule?: string
  status: 'active' | 'paused' | 'completed' | 'cancelled'
  next_run_at?: string
  last_run_at?: string
  run_count: number
  success_count: number
  failure_count: number
  created_at: string
  updated_at: string
}

export interface AgentRun {
  id: string
  task_id: string
  status: 'running' | 'completed' | 'failed'
  input: Record<string, unknown>
  output?: Record<string, unknown>
  steps?: Array<{ type: string; content: string; timestamp: string }>
  tokens_used?: number
  duration_ms?: number
  error_message?: string
  started_at: string
  completed_at?: string
}

interface UseAgentTasksReturn {
  tasks: AgentTask[]
  loading: boolean
  error: string | null
  createTask: (task: {
    name: string
    description?: string
    type: AgentTask['task_type']
    config: Record<string, unknown>
    schedule?: string
  }) => Promise<AgentTask | null>
  updateTask: (id: string, updates: Partial<Pick<AgentTask, 'name' | 'description' | 'config' | 'schedule'>>) => Promise<boolean>
  deleteTask: (id: string) => Promise<boolean>
  pauseTask: (id: string) => Promise<boolean>
  resumeTask: (id: string) => Promise<boolean>
  getTaskRuns: (id: string) => Promise<AgentRun[]>
  refresh: () => Promise<void>
}

export const useAgentTasks = (): UseAgentTasksReturn => {
  const { isAuthenticated, session } = useAuth()
  const [tasks, setTasks] = useState<AgentTask[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const getAuthHeaders = useCallback(() => {
    if (session?.access_token) {
      return { Authorization: `Bearer ${session.access_token}` }
    }
    return {}
  }, [session])

  const fetchTasks = useCallback(async () => {
    if (!isAuthenticated) {
      setTasks([])
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/api/v1/agents/tasks', { headers: getAuthHeaders() })
      setTasks(response.data.tasks || [])
    } catch (err) {
      console.error('[AgentTasks] Failed to fetch:', err)
      setError('Failed to load agent tasks')
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, getAuthHeaders])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const createTask = useCallback(
    async (task: {
      name: string
      description?: string
      type: AgentTask['task_type']
      config: Record<string, unknown>
      schedule?: string
    }): Promise<AgentTask | null> => {
      if (!isAuthenticated) {
        setError('Please sign in to create agent tasks')
        return null
      }

      try {
        const response = await api.post('/api/v1/agents/tasks', task, { headers: getAuthHeaders() })
        if (response.data.task) {
          setTasks((prev) => [response.data.task, ...prev])
          return response.data.task
        }
        return null
      } catch (err) {
        const errorMessage = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error
          ?.message
        setError(errorMessage || 'Failed to create agent task')
        return null
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const updateTask = useCallback(
    async (
      id: string,
      updates: Partial<Pick<AgentTask, 'name' | 'description' | 'config' | 'schedule'>>
    ): Promise<boolean> => {
      if (!isAuthenticated) return false

      try {
        const response = await api.patch(`/api/v1/agents/tasks/${id}`, updates, { headers: getAuthHeaders() })
        if (response.data.task) {
          setTasks((prev) => prev.map((t) => (t.id === id ? response.data.task : t)))
          return true
        }
        return false
      } catch (err) {
        console.error('[AgentTasks] Failed to update:', err)
        setError('Failed to update agent task')
        return false
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const deleteTask = useCallback(
    async (id: string): Promise<boolean> => {
      if (!isAuthenticated) return false

      try {
        await api.delete(`/api/v1/agents/tasks/${id}`, { headers: getAuthHeaders() })
        setTasks((prev) => prev.filter((t) => t.id !== id))
        return true
      } catch (err) {
        console.error('[AgentTasks] Failed to delete:', err)
        setError('Failed to delete agent task')
        return false
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const pauseTask = useCallback(
    async (id: string): Promise<boolean> => {
      if (!isAuthenticated) return false

      try {
        const response = await api.post(`/api/v1/agents/tasks/${id}/pause`, {}, { headers: getAuthHeaders() })
        if (response.data.task) {
          setTasks((prev) => prev.map((t) => (t.id === id ? response.data.task : t)))
          return true
        }
        return false
      } catch (err) {
        console.error('[AgentTasks] Failed to pause:', err)
        setError('Failed to pause agent task')
        return false
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const resumeTask = useCallback(
    async (id: string): Promise<boolean> => {
      if (!isAuthenticated) return false

      try {
        const response = await api.post(`/api/v1/agents/tasks/${id}/resume`, {}, { headers: getAuthHeaders() })
        if (response.data.task) {
          setTasks((prev) => prev.map((t) => (t.id === id ? response.data.task : t)))
          return true
        }
        return false
      } catch (err) {
        console.error('[AgentTasks] Failed to resume:', err)
        setError('Failed to resume agent task')
        return false
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const getTaskRuns = useCallback(
    async (id: string): Promise<AgentRun[]> => {
      if (!isAuthenticated) return []

      try {
        const response = await api.get(`/api/v1/agents/tasks/${id}/runs`, { headers: getAuthHeaders() })
        return response.data.runs || []
      } catch (err) {
        console.error('[AgentTasks] Failed to fetch runs:', err)
        return []
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  return {
    tasks,
    loading,
    error,
    createTask,
    updateTask,
    deleteTask,
    pauseTask,
    resumeTask,
    getTaskRuns,
    refresh: fetchTasks,
  }
}
