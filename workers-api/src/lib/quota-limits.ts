export const QUOTA_LIMITS = {
  free: {
    watchlist: 5,
    agents: 2,
    daily_alerts: 10,
    daily_deep_research: 3,
    daily_quick_chat: 50,
    monthly_reports: 5,
  },
  pro: {
    watchlist: 50,
    agents: 20,
    daily_alerts: 100,
    daily_deep_research: 30,
    daily_quick_chat: 500,
    monthly_reports: 50,
  },
  team: {
    watchlist: 1000,
    agents: 100,
    daily_alerts: 500,
    daily_deep_research: 100,
    daily_quick_chat: 2000,
    monthly_reports: 200,
  },
} as const

export type Plan = keyof typeof QUOTA_LIMITS
export type QuotaType = keyof (typeof QUOTA_LIMITS)['free']

export function getQuotaLimit(plan: Plan, quotaType: QuotaType): number {
  return QUOTA_LIMITS[plan]?.[quotaType] ?? QUOTA_LIMITS.free[quotaType]
}

export function isQuotaExceeded(used: number, limit: number): boolean {
  return used >= limit
}
