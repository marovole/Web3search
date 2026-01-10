import { useState, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'

export interface Recommendation {
  id: string
  user_id: string
  task_id?: string
  run_id?: string
  token_id: string
  symbol: string
  name: string
  coingecko_id?: string
  logo_url?: string
  recommendation_type: string
  confidence_score: number
  match_reasons: string[]
  market_data: {
    current_price?: number
    market_cap?: number
    market_cap_rank?: number
    price_change_24h?: number
    price_change_7d?: number
    volume_24h?: number
  }
  ai_analysis?: string
  risk_level: string
  potential_upside?: number
  potential_downside?: number
  time_horizon?: string
  status: string
  user_feedback?: string
  feedback_at?: string
  feedback_notes?: string
  viewed_at?: string
  expires_at?: string
  batch_id?: string
  batch_position?: number
  created_at: string
}

export interface UserPreferences {
  user_id: string
  risk_tolerance: string
  investment_horizon: string
  preferred_sectors: string[]
  excluded_sectors: string[]
  preferred_chains: string[]
  min_market_cap: string
  interest_tags: string[]
  notification_enabled: boolean
  discovery_frequency: string
  max_recommendations_per_batch: number
}

interface UseRecommendationsReturn {
  recommendations: Recommendation[]
  latestRecommendations: Recommendation[]
  preferences: UserPreferences | null
  loading: boolean
  error: string | null
  total: number
  fetchRecommendations: (status?: string, limit?: number, offset?: number) => Promise<void>
  fetchLatest: () => Promise<void>
  fetchPreferences: () => Promise<void>
  updatePreferences: (prefs: Partial<UserPreferences>) => Promise<void>
  submitFeedback: (id: string, feedback: string, notes?: string) => Promise<void>
  dismissRecommendation: (id: string) => Promise<void>
}

export const useRecommendations = (): UseRecommendationsReturn => {
  const { isAuthenticated, session } = useAuth()
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [latestRecommendations, setLatestRecommendations] = useState<Recommendation[]>([])
  const [preferences, setPreferences] = useState<UserPreferences | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  const getAuthHeaders = useCallback(() => {
    if (session?.access_token) {
      return { Authorization: `Bearer ${session.access_token}` }
    }
    return {}
  }, [session])

  const fetchRecommendations = useCallback(async (
    status = 'active',
    limit = 20,
    offset = 0
  ) => {
    if (!isAuthenticated) {
      setRecommendations([])
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await api.get(
        `/api/v1/recommendations?status=${status}&limit=${limit}&offset=${offset}`,
        { headers: getAuthHeaders() }
      )
      setRecommendations(response.data.recommendations || [])
      setTotal(response.data.total || 0)
    } catch (err) {
      console.error('[Recommendations] Failed to fetch:', err)
      setError('Failed to load recommendations')
      setRecommendations([])
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, getAuthHeaders])

  const fetchLatest = useCallback(async () => {
    if (!isAuthenticated) {
      setLatestRecommendations([])
      return
    }

    try {
      setLoading(true)
      const response = await api.get('/api/v1/recommendations/latest', { headers: getAuthHeaders() })
      setLatestRecommendations(response.data.recommendations || [])
    } catch (err) {
      console.error('[Recommendations] Failed to fetch latest:', err)
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, getAuthHeaders])

  const fetchPreferences = useCallback(async () => {
    if (!isAuthenticated) {
      setPreferences(null)
      return
    }

    try {
      const response = await api.get('/api/v1/recommendations/preferences', { headers: getAuthHeaders() })
      setPreferences(response.data.preferences)
    } catch (err) {
      console.error('[Recommendations] Failed to fetch preferences:', err)
    }
  }, [isAuthenticated, getAuthHeaders])

  const updatePreferences = useCallback(async (prefs: Partial<UserPreferences>) => {
    if (!isAuthenticated) return

    try {
      setLoading(true)
      const response = await api.put('/api/v1/recommendations/preferences', prefs, { headers: getAuthHeaders() })
      setPreferences(response.data.preferences)
    } catch (err) {
      console.error('[Recommendations] Failed to update preferences:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, getAuthHeaders])

  const submitFeedback = useCallback(async (id: string, feedback: string, notes?: string) => {
    if (!isAuthenticated) return

    try {
      await api.patch(
        `/api/v1/recommendations/${id}/feedback`,
        { feedback, notes },
        { headers: getAuthHeaders() }
      )

      setRecommendations(prev => prev.map(r => 
        r.id === id ? { ...r, user_feedback: feedback, status: feedback === 'like' ? 'liked' : 'disliked' } : r
      ))
      setLatestRecommendations(prev => prev.map(r => 
        r.id === id ? { ...r, user_feedback: feedback, status: feedback === 'like' ? 'liked' : 'disliked' } : r
      ))
    } catch (err) {
      console.error('[Recommendations] Failed to submit feedback:', err)
      throw err
    }
  }, [isAuthenticated, getAuthHeaders])

  const dismissRecommendation = useCallback(async (id: string) => {
    if (!isAuthenticated) return

    try {
      await api.delete(`/api/v1/recommendations/${id}`, { headers: getAuthHeaders() })
      
      setRecommendations(prev => prev.filter(r => r.id !== id))
      setLatestRecommendations(prev => prev.filter(r => r.id !== id))
    } catch (err) {
      console.error('[Recommendations] Failed to dismiss:', err)
      throw err
    }
  }, [isAuthenticated, getAuthHeaders])

  return {
    recommendations,
    latestRecommendations,
    preferences,
    loading,
    error,
    total,
    fetchRecommendations,
    fetchLatest,
    fetchPreferences,
    updatePreferences,
    submitFeedback,
    dismissRecommendation,
  }
}
