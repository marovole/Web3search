import { useState, useCallback, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

export interface Notification {
  id: string
  user_id: string
  type: 'price_alert' | 'risk_alert' | 'news_brief' | 'portfolio_update' | 'system' | 'promo'
  title: string
  body: string
  data: Record<string, unknown>
  source_type: string | null
  source_id: string | null
  read_at: string | null
  dismissed_at: string | null
  priority: 'low' | 'normal' | 'high' | 'urgent'
  expires_at: string | null
  push_sent: boolean
  push_sent_at: string | null
  created_at: string
}

interface NotificationsState {
  notifications: Notification[]
  unreadCount: number
  total: number
  loading: boolean
  error: string | null
}

interface UseNotificationsOptions {
  autoRefresh?: boolean
  refreshInterval?: number
  initialFetch?: boolean
}

export function useNotifications(options: UseNotificationsOptions = {}) {
  const { autoRefresh = false, refreshInterval = 30000, initialFetch = true } = options
  const { session, isAuthenticated } = useAuth()
  
  const [state, setState] = useState<NotificationsState>({
    notifications: [],
    unreadCount: 0,
    total: 0,
    loading: false,
    error: null
  })

  const getAuthHeaders = useCallback(() => {
    if (!session?.access_token) return null
    return {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    }
  }, [session?.access_token])

  const apiUrl = import.meta.env?.VITE_API_BASE_URL || ''

  const fetchNotifications = useCallback(async (params?: {
    limit?: number
    offset?: number
    unreadOnly?: boolean
    type?: string
  }) => {
    const headers = getAuthHeaders()
    if (!headers) return

    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const searchParams = new URLSearchParams()
      if (params?.limit) searchParams.set('limit', params.limit.toString())
      if (params?.offset) searchParams.set('offset', params.offset.toString())
      if (params?.unreadOnly) searchParams.set('unread', 'true')
      if (params?.type) searchParams.set('type', params.type)

      const response = await fetch(
        `${apiUrl}/api/v1/notifications?${searchParams}`,
        { headers }
      )

      if (!response.ok) {
        throw new Error('Failed to fetch notifications')
      }

      const data = await response.json()
      setState(prev => ({
        ...prev,
        notifications: data.notifications,
        unreadCount: data.unread_count,
        total: data.total,
        loading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }))
    }
  }, [apiUrl, getAuthHeaders])

  const markAsRead = useCallback(async (id: string) => {
    const headers = getAuthHeaders()
    if (!headers) return false

    try {
      const response = await fetch(
        `${apiUrl}/api/v1/notifications/${id}/read`,
        { method: 'PATCH', headers }
      )

      if (!response.ok) return false

      setState(prev => ({
        ...prev,
        notifications: prev.notifications.map(n =>
          n.id === id ? { ...n, read_at: new Date().toISOString() } : n
        ),
        unreadCount: Math.max(0, prev.unreadCount - 1)
      }))

      return true
    } catch {
      return false
    }
  }, [apiUrl, getAuthHeaders])

  const markAllAsRead = useCallback(async () => {
    const headers = getAuthHeaders()
    if (!headers) return false

    try {
      const response = await fetch(
        `${apiUrl}/api/v1/notifications/read-all`,
        { method: 'POST', headers }
      )

      if (!response.ok) return false

      setState(prev => ({
        ...prev,
        notifications: prev.notifications.map(n => ({
          ...n,
          read_at: n.read_at || new Date().toISOString()
        })),
        unreadCount: 0
      }))

      return true
    } catch {
      return false
    }
  }, [apiUrl, getAuthHeaders])

  const dismissNotification = useCallback(async (id: string) => {
    const headers = getAuthHeaders()
    if (!headers) return false

    try {
      const response = await fetch(
        `${apiUrl}/api/v1/notifications/${id}/dismiss`,
        { method: 'PATCH', headers }
      )

      if (!response.ok) return false

      setState(prev => ({
        ...prev,
        notifications: prev.notifications.filter(n => n.id !== id),
        total: prev.total - 1,
        unreadCount: prev.notifications.find(n => n.id === id)?.read_at === null
          ? prev.unreadCount - 1
          : prev.unreadCount
      }))

      return true
    } catch {
      return false
    }
  }, [apiUrl, getAuthHeaders])

  const deleteNotification = useCallback(async (id: string) => {
    const headers = getAuthHeaders()
    if (!headers) return false

    try {
      const response = await fetch(
        `${apiUrl}/api/v1/notifications/${id}`,
        { method: 'DELETE', headers }
      )

      if (!response.ok) return false

      setState(prev => ({
        ...prev,
        notifications: prev.notifications.filter(n => n.id !== id),
        total: prev.total - 1,
        unreadCount: prev.notifications.find(n => n.id === id)?.read_at === null
          ? prev.unreadCount - 1
          : prev.unreadCount
      }))

      return true
    } catch {
      return false
    }
  }, [apiUrl, getAuthHeaders])

  // Initial fetch
  useEffect(() => {
    if (isAuthenticated && initialFetch) {
      fetchNotifications()
    }
  }, [isAuthenticated, initialFetch, fetchNotifications])

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || !isAuthenticated) return

    const interval = setInterval(() => {
      fetchNotifications()
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, isAuthenticated, refreshInterval, fetchNotifications])

  return {
    ...state,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    deleteNotification,
    refresh: () => fetchNotifications()
  }
}

export default useNotifications
