import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'

export interface ApiWatchlistItem {
  id: string
  user_id: string
  token_id: string
  symbol: string
  name: string
  coingecko_id?: string
  logo_url?: string
  notes?: string
  tags: string[]
  alert_settings: Record<string, unknown>
  position: number
  created_at: string
  updated_at: string
}

interface UseApiWatchlistReturn {
  watchlist: ApiWatchlistItem[]
  loading: boolean
  error: string | null
  addToWatchlist: (item: {
    token_id: string
    symbol: string
    name: string
    coingecko_id?: string
    logo_url?: string
    notes?: string
    tags?: string[]
  }) => Promise<boolean>
  removeFromWatchlist: (id: string) => Promise<boolean>
  updateWatchlistItem: (
    id: string,
    updates: { notes?: string; tags?: string[]; alert_settings?: Record<string, unknown> }
  ) => Promise<boolean>
  isInWatchlist: (symbol: string) => boolean
  clearWatchlist: () => Promise<boolean>
  refresh: () => Promise<void>
}

export const useApiWatchlist = (): UseApiWatchlistReturn => {
  const { isAuthenticated, session } = useAuth()
  const [watchlist, setWatchlist] = useState<ApiWatchlistItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const getAuthHeaders = useCallback(() => {
    if (session?.access_token) {
      return { Authorization: `Bearer ${session.access_token}` }
    }
    return {}
  }, [session])

  const fetchWatchlist = useCallback(async () => {
    if (!isAuthenticated) {
      setWatchlist([])
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/api/v1/watchlist', { headers: getAuthHeaders() })
      setWatchlist(response.data.watchlist || [])
    } catch (err) {
      console.error('[Watchlist] Failed to fetch:', err)
      setError('Failed to load watchlist')
      setWatchlist([])
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, getAuthHeaders])

  useEffect(() => {
    fetchWatchlist()
  }, [fetchWatchlist])

  const addToWatchlist = useCallback(
    async (item: {
      token_id: string
      symbol: string
      name: string
      coingecko_id?: string
      logo_url?: string
      notes?: string
      tags?: string[]
    }): Promise<boolean> => {
      if (!isAuthenticated) {
        setError('Please sign in to add items to watchlist')
        return false
      }

      try {
        const response = await api.post('/api/v1/watchlist', item, { headers: getAuthHeaders() })
        if (response.data.item) {
          setWatchlist((prev) => [...prev, response.data.item])
          return true
        }
        return false
      } catch (err) {
        const errorMessage = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error
          ?.message
        setError(errorMessage || 'Failed to add to watchlist')
        return false
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const removeFromWatchlist = useCallback(
    async (id: string): Promise<boolean> => {
      if (!isAuthenticated) return false

      try {
        await api.delete(`/api/v1/watchlist/${id}`, { headers: getAuthHeaders() })
        setWatchlist((prev) => prev.filter((item) => item.id !== id))
        return true
      } catch (err) {
        console.error('[Watchlist] Failed to remove:', err)
        setError('Failed to remove from watchlist')
        return false
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const updateWatchlistItem = useCallback(
    async (
      id: string,
      updates: { notes?: string; tags?: string[]; alert_settings?: Record<string, unknown> }
    ): Promise<boolean> => {
      if (!isAuthenticated) return false

      try {
        const response = await api.patch(`/api/v1/watchlist/${id}`, updates, { headers: getAuthHeaders() })
        if (response.data.item) {
          setWatchlist((prev) => prev.map((item) => (item.id === id ? response.data.item : item)))
          return true
        }
        return false
      } catch (err) {
        console.error('[Watchlist] Failed to update:', err)
        setError('Failed to update watchlist item')
        return false
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const isInWatchlist = useCallback(
    (symbol: string): boolean => {
      return watchlist.some((item) => item.symbol.toLowerCase() === symbol.toLowerCase())
    },
    [watchlist]
  )

  const clearWatchlist = useCallback(async (): Promise<boolean> => {
    if (!isAuthenticated) return false

    try {
      for (const item of watchlist) {
        await api.delete(`/api/v1/watchlist/${item.id}`, { headers: getAuthHeaders() })
      }
      setWatchlist([])
      return true
    } catch (err) {
      console.error('[Watchlist] Failed to clear:', err)
      setError('Failed to clear watchlist')
      return false
    }
  }, [isAuthenticated, watchlist, getAuthHeaders])

  return {
    watchlist,
    loading,
    error,
    addToWatchlist,
    removeFromWatchlist,
    updateWatchlistItem,
    isInWatchlist,
    clearWatchlist,
    refresh: fetchWatchlist,
  }
}
