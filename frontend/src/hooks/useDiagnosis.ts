import { useState, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'

export interface PortfolioDiagnosis {
  id: string
  user_id: string
  task_id?: string
  run_id?: string
  diagnosis_date: string
  overall_health_score: number
  diversification_score: number
  risk_score: number
  performance_score: number
  summary: string
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  sector_allocation: Record<string, number>
  correlation_analysis: Record<string, unknown>
  risk_factors: Array<{ factor: string; severity: string; description: string }>
  performance_vs_benchmarks: Record<string, unknown>
  full_report?: string
  created_at: string
}

export interface PortfolioSnapshot {
  snapshot_date: string
  total_value_usd: number
  total_pnl_usd?: number
  total_pnl_percent?: number
  holdings_count: number
}

interface UseDiagnosisReturn {
  latestDiagnosis: PortfolioDiagnosis | null
  diagnoses: PortfolioDiagnosis[]
  snapshots: PortfolioSnapshot[]
  loading: boolean
  error: string | null
  fetchLatest: () => Promise<void>
  fetchAll: (limit?: number) => Promise<void>
  fetchSnapshots: (days?: number) => Promise<void>
}

export const useDiagnosis = (): UseDiagnosisReturn => {
  const { isAuthenticated, session } = useAuth()
  const [latestDiagnosis, setLatestDiagnosis] = useState<PortfolioDiagnosis | null>(null)
  const [diagnoses, setDiagnoses] = useState<PortfolioDiagnosis[]>([])
  const [snapshots, setSnapshots] = useState<PortfolioSnapshot[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getAuthHeaders = useCallback(() => {
    if (session?.access_token) {
      return { Authorization: `Bearer ${session.access_token}` }
    }
    return {}
  }, [session])

  const fetchLatest = useCallback(async () => {
    if (!isAuthenticated) {
      setLatestDiagnosis(null)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/api/v1/diagnoses/latest', { headers: getAuthHeaders() })
      setLatestDiagnosis(response.data.diagnosis)
    } catch (err) {
      console.error('[Diagnosis] Failed to fetch latest:', err)
      setError('Failed to load diagnosis')
      setLatestDiagnosis(null)
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, getAuthHeaders])

  const fetchAll = useCallback(async (limit = 10) => {
    if (!isAuthenticated) {
      setDiagnoses([])
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await api.get(`/api/v1/diagnoses?limit=${limit}`, { headers: getAuthHeaders() })
      setDiagnoses(response.data.diagnoses || [])
    } catch (err) {
      console.error('[Diagnosis] Failed to fetch all:', err)
      setError('Failed to load diagnoses')
      setDiagnoses([])
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, getAuthHeaders])

  const fetchSnapshots = useCallback(async (days = 30) => {
    if (!isAuthenticated) {
      setSnapshots([])
      return
    }

    try {
      const response = await api.get(`/api/v1/diagnoses/snapshots?days=${days}`, { headers: getAuthHeaders() })
      setSnapshots(response.data.snapshots || [])
    } catch (err) {
      console.error('[Diagnosis] Failed to fetch snapshots:', err)
    }
  }, [isAuthenticated, getAuthHeaders])

  return {
    latestDiagnosis,
    diagnoses,
    snapshots,
    loading,
    error,
    fetchLatest,
    fetchAll,
    fetchSnapshots,
  }
}
