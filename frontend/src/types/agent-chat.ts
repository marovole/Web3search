/**
 * Agent Chat Types
 * Frontend types for conversational AI chat interface
 */

export type IntentType = 
  | 'create_price_alert'
  | 'create_risk_monitor'
  | 'create_news_brief'
  | 'create_portfolio_diagnosis'
  | 'create_opportunity_finder'
  | 'list_tasks'
  | 'pause_task'
  | 'resume_task'
  | 'delete_task'
  | 'check_price'
  | 'check_portfolio'
  | 'get_recommendations'
  | 'update_preferences'
  | 'unknown'

export interface ParsedIntent {
  type: IntentType
  confidence: number
  entities: IntentEntities
  originalText: string
  requiresConfirmation: boolean
  confirmationMessage?: string
}

export interface IntentEntities {
  tokens?: TokenEntity[]
  priceCondition?: PriceConditionEntity
  percentChange?: PercentChangeEntity
  timeframe?: TimeframeEntity
  riskThreshold?: number
  frequency?: 'hourly' | 'daily' | 'weekly'
  taskId?: string
}

export interface TokenEntity {
  symbol: string
  name?: string
  confidence: number
}

export interface PriceConditionEntity {
  type: 'above' | 'below' | 'crosses'
  value: number
  currency: 'usd' | 'btc' | 'eth'
}

export interface PercentChangeEntity {
  type: 'increase' | 'decrease' | 'change'
  value: number
  period: '1h' | '24h' | '7d' | '30d'
}

export interface TimeframeEntity {
  type: 'once' | 'recurring'
  duration?: number
  unit?: 'minutes' | 'hours' | 'days' | 'weeks'
}

export interface TaskCreationResult {
  success: boolean
  taskId?: string
  taskType?: string
  message: string
}

export interface AgentChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  intent?: ParsedIntent
  taskResult?: TaskCreationResult
  isStreaming?: boolean
  requiresConfirmation?: boolean
  confirmationDetails?: {
    intentType: IntentType
    entities: IntentEntities
    previewConfig: Record<string, unknown>
  }
}

export interface AgentConversation {
  conversationId: string
  messages: AgentChatMessage[]
  lastActivity: Date
}

export interface SendMessageResponse {
  conversationId: string
  message: string
  intent?: ParsedIntent
  taskResult?: TaskCreationResult
  requiresConfirmation?: boolean
  requiresMoreInfo?: boolean
  missingFields?: string[]
  suggestions?: string[]
  confirmationDetails?: {
    intentType: IntentType
    entities: IntentEntities
    previewConfig: Record<string, unknown>
  }
}

// SSE Event Types
export interface AgentSSEEvent {
  event: 'start' | 'thinking' | 'intent' | 'confirmation' | 'executing' | 'result' | 'message' | 'error' | 'done'
  data: string
}

export const INTENT_DESCRIPTIONS: Record<IntentType, string> = {
  create_price_alert: '创建价格提醒',
  create_risk_monitor: '创建风险监控',
  create_news_brief: '订阅新闻速报',
  create_portfolio_diagnosis: '执行持仓诊断',
  create_opportunity_finder: '开启机会发现',
  list_tasks: '查看任务列表',
  pause_task: '暂停任务',
  resume_task: '恢复任务',
  delete_task: '删除任务',
  check_price: '查询价格',
  check_portfolio: '查看持仓',
  get_recommendations: '获取推荐',
  update_preferences: '更新偏好设置',
  unknown: '未知意图',
}

export const EXAMPLE_PROMPTS = [
  '当BTC跌破50000美元时提醒我',
  '帮我监控ETH的风险变化',
  '分析一下我的持仓',
  '有什么推荐的项目吗',
  'BTC现在多少钱',
  '查看我的所有任务',
]
