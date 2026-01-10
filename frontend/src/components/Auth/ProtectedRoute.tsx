import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredPlan?: 'pro' | 'team'
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredPlan }) => {
  const { isAuthenticated, loading, profile } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />
  }

  if (requiredPlan) {
    const planHierarchy = { free: 0, pro: 1, team: 2 }
    const userPlanLevel = planHierarchy[profile?.plan || 'free']
    const requiredLevel = planHierarchy[requiredPlan]

    if (userPlanLevel < requiredLevel) {
      return <Navigate to="/upgrade" state={{ requiredPlan }} replace />
    }
  }

  return <>{children}</>
}

export default ProtectedRoute
