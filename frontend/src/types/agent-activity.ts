/**
 * Agent Activity Log Types
 * Types for tracking and displaying agent execution events
 */

// ============================================================================
// Event Types
// ============================================================================

export type AgentEventType =
  | 'task_started'
  | 'task_completed'
  | 'task_failed'
  | 'condition_checked'
  | 'condition_triggered'
  | 'notification_sent'
  | 'api_called'
  | 'error_occurred'
  | 'scheduled_run'
  | 'manual_run'

export type AgentTaskType =
  | 'price_alert'
  | 'risk_monitor'
  | 'news_brief'
  | 'portfolio_health'
  | 'opportunity_finder'

// ============================================================================
// Activity Event
// ============================================================================

export interface AgentActivityEvent {
  id: string
  task_id: string
  task_type: AgentTaskType
  task_name: string
  event_type: AgentEventType
  status: 'success' | 'warning' | 'error' | 'info'
  message: string
  details?: Record<string, unknown>
  created_at: string
}

// ============================================================================
// Run Summary
// ============================================================================

export interface AgentRunSummary {
  id: string
  task_id: string
  task_type: AgentTaskType
  task_name: string
  started_at: string
  completed_at?: string
  status: 'running' | 'completed' | 'failed'
  events_count: number
  trigger: 'scheduled' | 'manual' | 'condition'
  result_summary?: string
  error_message?: string
}

// ============================================================================
// Dashboard Stats
// ============================================================================

export interface AgentDashboardStats {
  total_tasks: number
  active_tasks: number
  paused_tasks: number
  runs_today: number
  runs_this_week: number
  notifications_sent_today: number
  alerts_triggered_today: number
  success_rate_7d: number
  by_task_type: Record<AgentTaskType, {
    count: number
    active: number
    last_run?: string
  }>
}

// ============================================================================
// Task Status
// ============================================================================

export interface AgentTaskStatus {
  id: string
  name: string
  type: AgentTaskType
  status: 'active' | 'paused' | 'error'
  last_run_at?: string
  next_run_at?: string
  last_run_status?: 'success' | 'error'
  run_count: number
  trigger_count: number
  created_at: string
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ActivityLogResponse {
  events: AgentActivityEvent[]
  total: number
  has_more: boolean
}

export interface DashboardResponse {
  stats: AgentDashboardStats
  recent_runs: AgentRunSummary[]
  active_tasks: AgentTaskStatus[]
}

// ============================================================================
// Filter Options
// ============================================================================

export interface ActivityLogFilters {
  task_type?: AgentTaskType
  task_id?: string
  event_type?: AgentEventType
  status?: 'success' | 'warning' | 'error' | 'info'
  from_date?: string
  to_date?: string
  limit?: number
  offset?: number
}

// ============================================================================
// Constants
// ============================================================================

export const EVENT_TYPE_LABELS: Record<AgentEventType, string> = {
  task_started: '任务开始',
  task_completed: '任务完成',
  task_failed: '任务失败',
  condition_checked: '条件检查',
  condition_triggered: '条件触发',
  notification_sent: '通知发送',
  api_called: 'API 调用',
  error_occurred: '发生错误',
  scheduled_run: '定时执行',
  manual_run: '手动执行',
}

export const TASK_TYPE_LABELS: Record<AgentTaskType, string> = {
  price_alert: '价格提醒',
  risk_monitor: '风险监控',
  news_brief: '新闻速报',
  portfolio_health: '持仓诊断',
  opportunity_finder: '机会发现',
}

export const TASK_TYPE_ICONS: Record<AgentTaskType, string> = {
  price_alert: '📊',
  risk_monitor: '⚠️',
  news_brief: '📰',
  portfolio_health: '🏥',
  opportunity_finder: '💡',
}

export const STATUS_COLORS: Record<string, string> = {
  success: 'text-green-400 bg-green-500/10',
  warning: 'text-yellow-400 bg-yellow-500/10',
  error: 'text-red-400 bg-red-500/10',
  info: 'text-blue-400 bg-blue-500/10',
}
