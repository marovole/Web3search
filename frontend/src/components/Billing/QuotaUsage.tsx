import React from 'react'
import { AlertCircle, TrendingUp, Zap, Eye, Bot, Bell, FileText, MessageSquare } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

interface QuotaItem {
  label: string
  used: number
  limit: number
  icon: React.ElementType
  period?: 'daily' | 'monthly' | 'total'
}

interface QuotaUsageProps {
  className?: string
  compact?: boolean
  showUpgradePrompt?: boolean
}

export const QuotaUsage: React.FC<QuotaUsageProps> = ({
  className,
  compact = false,
  showUpgradePrompt = true
}) => {
  const { quota, profile } = useAuth()
  const navigate = useNavigate()

  if (!quota) {
    return null
  }

  const items: QuotaItem[] = [
    {
      label: 'Watchlist',
      used: quota.watchlist.used,
      limit: quota.watchlist.limit,
      icon: Eye,
      period: 'total'
    },
    {
      label: 'Active Agents',
      used: quota.agents.used,
      limit: quota.agents.limit,
      icon: Bot,
      period: 'total'
    },
    {
      label: 'Daily Alerts',
      used: quota.daily.alerts.used,
      limit: quota.daily.alerts.limit,
      icon: Bell,
      period: 'daily'
    },
    {
      label: 'Deep Research',
      used: quota.daily.deep_research.used,
      limit: quota.daily.deep_research.limit,
      icon: FileText,
      period: 'daily'
    },
    {
      label: 'Quick Chat',
      used: quota.daily.quick_chat.used,
      limit: quota.daily.quick_chat.limit,
      icon: MessageSquare,
      period: 'daily'
    },
    {
      label: 'Monthly Reports',
      used: quota.monthly.reports.used,
      limit: quota.monthly.reports.limit,
      icon: TrendingUp,
      period: 'monthly'
    }
  ]

  const getPercentage = (used: number, limit: number) => {
    if (limit === 0) return 0
    return Math.min(100, Math.round((used / limit) * 100))
  }

  const getColorClass = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500'
    if (percentage >= 70) return 'bg-yellow-500'
    return 'bg-primary'
  }

  const getTextColorClass = (percentage: number) => {
    if (percentage >= 90) return 'text-red-500'
    if (percentage >= 70) return 'text-yellow-500'
    return 'text-primary'
  }

  const hasNearLimit = items.some(item => getPercentage(item.used, item.limit) >= 80)
  const hasExhausted = items.some(item => item.used >= item.limit)

  const formatLimit = (limit: number) => {
    if (limit >= 1000) return `${limit >= 10000 ? 'Unlimited' : limit.toLocaleString()}`
    return limit.toString()
  }

  if (compact) {
    // Compact view for sidebar or header
    return (
      <div className={cn("space-y-2", className)}>
        {items.slice(0, 4).map((item) => {
          const percentage = getPercentage(item.used, item.limit)
          const Icon = item.icon
          
          return (
            <div key={item.label} className="flex items-center gap-2">
              <Icon className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn("h-full transition-all duration-300", getColorClass(percentage))}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
              <span className={cn("text-[10px] font-medium shrink-0", getTextColorClass(percentage))}>
                {item.used}/{formatLimit(item.limit)}
              </span>
            </div>
          )
        })}
        {showUpgradePrompt && hasNearLimit && profile?.plan === 'free' && (
          <Button
            size="sm"
            variant="ghost"
            className="w-full h-7 text-xs text-primary hover:text-primary"
            onClick={() => navigate('/upgrade')}
          >
            <Zap className="w-3 h-3 mr-1" />
            Upgrade for more
          </Button>
        )}
      </div>
    )
  }

  // Full view
  return (
    <div className={cn("rounded-xl border bg-card p-6", className)}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold">Usage & Limits</h3>
          <p className="text-sm text-muted-foreground">
            {profile?.plan === 'free' ? 'Free' : profile?.plan === 'pro' ? 'Pro' : 'Team'} Plan
          </p>
        </div>
        {quota.resets && (
          <div className="text-right text-xs text-muted-foreground">
            <p>Daily reset: {new Date(quota.resets.daily).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
            <p>Monthly reset: {new Date(quota.resets.monthly).toLocaleDateString([], { month: 'short', day: 'numeric' })}</p>
          </div>
        )}
      </div>

      {hasExhausted && (
        <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-500">Quota exhausted</p>
            <p className="text-xs text-red-500/80 mt-1">
              You've reached one or more limits. Upgrade to continue using all features.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {items.map((item) => {
          const percentage = getPercentage(item.used, item.limit)
          const Icon = item.icon
          const isExhausted = item.used >= item.limit

          return (
            <div
              key={item.label}
              className={cn(
                "p-4 rounded-lg border transition-colors",
                isExhausted ? "border-red-500/30 bg-red-500/5" : "border-border bg-muted/30"
              )}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={cn(
                    "p-2 rounded-lg",
                    isExhausted ? "bg-red-500/10 text-red-500" : "bg-primary/10 text-primary"
                  )}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                      {item.period === 'daily' ? 'Daily' : item.period === 'monthly' ? 'Monthly' : 'Total'}
                    </p>
                  </div>
                </div>
                <span className={cn("text-sm font-semibold", getTextColorClass(percentage))}>
                  {item.used} / {formatLimit(item.limit)}
                </span>
              </div>
              
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full transition-all duration-500 rounded-full",
                    getColorClass(percentage)
                  )}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              
              {percentage >= 80 && !isExhausted && (
                <p className="text-[10px] text-yellow-500 mt-2 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  Approaching limit
                </p>
              )}
            </div>
          )
        })}
      </div>

      {showUpgradePrompt && profile?.plan !== 'team' && (hasNearLimit || hasExhausted) && (
        <div className="mt-6 pt-6 border-t flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Need more capacity?</p>
            <p className="text-xs text-muted-foreground">
              Upgrade to {profile?.plan === 'free' ? 'Pro' : 'Team'} for higher limits
            </p>
          </div>
          <Button onClick={() => navigate('/upgrade')} className="gap-2">
            <Zap className="w-4 h-4" />
            Upgrade Now
          </Button>
        </div>
      )}
    </div>
  )
}

export default QuotaUsage
