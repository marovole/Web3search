import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'

export interface Holding {
  id: string
  user_id: string
  token_id: string
  symbol: string
  name: string
  quantity: number
  coingecko_id?: string
  logo_url?: string
  avg_buy_price?: number
  total_cost_basis?: number
  notes?: string
  tags?: string[]
  acquisition_date?: string
  is_staked: boolean
  staking_platform?: string
  staking_apy?: number
  created_at: string
  updated_at: string
}

export interface HoldingWithValue extends Holding {
  price_usd?: number
  value_usd?: number
  change_24h?: number
}

export interface PortfolioSummary {
  total_value_usd: number
  holdings_count: number
  holdings: Array<{
    symbol: string
    name: string
    quantity: number
    price_usd?: number
    value_usd?: number
    change_24h?: number
  }>
}

interface UseHoldingsReturn {
  holdings: Holding[]
  summary: PortfolioSummary | null
  loading: boolean
  error: string | null
  createHolding: (holding: {
    token_id: string
    symbol: string
    name: string
    quantity: number
    coingecko_id?: string
    logo_url?: string
    avg_buy_price?: number
    total_cost_basis?: number
    notes?: string
    tags?: string[]
    acquisition_date?: string
    is_staked?: boolean
    staking_platform?: string
    staking_apy?: number
  }) => Promise<Holding | null>
  updateHolding: (id: string, updates: Partial<Omit<Holding, 'id' | 'user_id' | 'created_at' | 'updated_at'>>) => Promise<boolean>
  deleteHolding: (id: string) => Promise<boolean>
  fetchSummary: () => Promise<void>
  refresh: () => Promise<void>
}

export const useHoldings = (): UseHoldingsReturn => {
  const { isAuthenticated, session } = useAuth()
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const getAuthHeaders = useCallback(() => {
    if (session?.access_token) {
      return { Authorization: `Bearer ${session.access_token}` }
    }
    return {}
  }, [session])

  const fetchHoldings = useCallback(async () => {
    if (!isAuthenticated) {
      setHoldings([])
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/api/v1/holdings', { headers: getAuthHeaders() })
      setHoldings(response.data.holdings || [])
    } catch (err) {
      console.error('[Holdings] Failed to fetch:', err)
      setError('Failed to load holdings')
      setHoldings([])
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, getAuthHeaders])

  const fetchSummary = useCallback(async () => {
    if (!isAuthenticated) {
      setSummary(null)
      return
    }

    try {
      const response = await api.get('/api/v1/holdings/summary', { headers: getAuthHeaders() })
      setSummary(response.data)
    } catch (err) {
      console.error('[Holdings] Failed to fetch summary:', err)
    }
  }, [isAuthenticated, getAuthHeaders])

  useEffect(() => {
    fetchHoldings()
  }, [fetchHoldings])

  const createHolding = useCallback(
    async (holding: {
      token_id: string
      symbol: string
      name: string
      quantity: number
      coingecko_id?: string
      logo_url?: string
      avg_buy_price?: number
      total_cost_basis?: number
      notes?: string
      tags?: string[]
      acquisition_date?: string
      is_staked?: boolean
      staking_platform?: string
      staking_apy?: number
    }): Promise<Holding | null> => {
      if (!isAuthenticated) {
        setError('Please sign in to add holdings')
        return null
      }

      try {
        const response = await api.post('/api/v1/holdings', holding, { headers: getAuthHeaders() })
        if (response.data.holding) {
          setHoldings((prev) => [response.data.holding, ...prev])
          return response.data.holding
        }
        return null
      } catch (err) {
        const errorMessage = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error
          ?.message
        setError(errorMessage || 'Failed to add holding')
        return null
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const updateHolding = useCallback(
    async (
      id: string,
      updates: Partial<Omit<Holding, 'id' | 'user_id' | 'created_at' | 'updated_at'>>
    ): Promise<boolean> => {
      if (!isAuthenticated) return false

      try {
        const response = await api.patch(`/api/v1/holdings/${id}`, updates, { headers: getAuthHeaders() })
        if (response.data.holding) {
          setHoldings((prev) => prev.map((h) => (h.id === id ? response.data.holding : h)))
          return true
        }
        return false
      } catch (err) {
        console.error('[Holdings] Failed to update:', err)
        setError('Failed to update holding')
        return false
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  const deleteHolding = useCallback(
    async (id: string): Promise<boolean> => {
      if (!isAuthenticated) return false

      try {
        await api.delete(`/api/v1/holdings/${id}`, { headers: getAuthHeaders() })
        setHoldings((prev) => prev.filter((h) => h.id !== id))
        return true
      } catch (err) {
        console.error('[Holdings] Failed to delete:', err)
        setError('Failed to delete holding')
        return false
      }
    },
    [isAuthenticated, getAuthHeaders]
  )

  return {
    holdings,
    summary,
    loading,
    error,
    createHolding,
    updateHolding,
    deleteHolding,
    fetchSummary,
    refresh: fetchHoldings,
  }
}
