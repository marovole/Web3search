/**
 * Agent Intent Types
 * Defines the structure for parsing user natural language into agent tasks
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
  preferences?: PreferencesEntity
}

export interface TokenEntity {
  symbol: string
  name?: string
  coingeckoId?: string
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

export interface PreferencesEntity {
  riskTolerance?: 'conservative' | 'medium' | 'aggressive' | 'very_aggressive'
  investmentHorizon?: 'short' | 'medium' | 'long'
  sectors?: string[]
  chains?: string[]
}

export interface IntentParseResult {
  success: boolean
  intent?: ParsedIntent
  error?: string
  suggestions?: string[]
}

export interface TaskCreationResult {
  success: boolean
  taskId?: string
  taskType?: string
  message: string
  requiresConfirmation?: boolean
  confirmationDetails?: {
    intent: ParsedIntent
    previewConfig: Record<string, unknown>
  }
}

export interface ConversationMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  intent?: ParsedIntent
  taskResult?: TaskCreationResult
}

export interface ConversationContext {
  userId: string
  conversationId: string
  messages: ConversationMessage[]
  pendingIntent?: ParsedIntent
  lastActivity: string
}

export const INTENT_EXAMPLES: Record<IntentType, string[]> = {
  create_price_alert: [
    '当BTC跌破50000美元时提醒我',
    '提醒我ETH涨到4000',
    'SOL低于100刀通知我',
    '比特币突破6万提醒',
  ],
  create_risk_monitor: [
    '监控LUNA的风险',
    '帮我盯着SHIB的安全评分',
    '如果DOT风险升高通知我',
  ],
  create_news_brief: [
    '每天给我发送加密新闻摘要',
    '订阅BTC和ETH的新闻',
    '每小时推送我关注的币种新闻',
  ],
  create_portfolio_diagnosis: [
    '分析我的持仓',
    '诊断我的投资组合',
    '帮我检查持仓健康度',
  ],
  create_opportunity_finder: [
    '帮我发现投资机会',
    '推荐一些潜力币',
    '找一些适合我的项目',
  ],
  list_tasks: [
    '查看我的所有任务',
    '我有哪些监控在运行',
    '列出我的提醒',
  ],
  pause_task: [
    '暂停BTC价格提醒',
    '停止新闻推送',
    '暂停所有监控',
  ],
  resume_task: [
    '恢复BTC提醒',
    '继续新闻推送',
  ],
  delete_task: [
    '删除ETH价格提醒',
    '取消风险监控',
  ],
  check_price: [
    'BTC现在多少钱',
    '查一下ETH价格',
    'SOL涨了多少',
  ],
  check_portfolio: [
    '我的持仓现在值多少',
    '看看我的资产',
  ],
  get_recommendations: [
    '有什么推荐吗',
    '给我看看推荐',
  ],
  update_preferences: [
    '我想更激进一点',
    '调整我的风险偏好',
    '我只想看大盘币',
  ],
  unknown: [],
}

export const CONFIDENCE_THRESHOLD = 0.8

export function needsConfirmation(intent: ParsedIntent): boolean {
  if (intent.confidence < CONFIDENCE_THRESHOLD) {
    return true
  }
  
  const highRiskIntents: IntentType[] = [
    'delete_task',
    'pause_task',
  ]
  
  return highRiskIntents.includes(intent.type)
}

export function getIntentDescription(type: IntentType): string {
  const descriptions: Record<IntentType, string> = {
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
  return descriptions[type] || '未知操作'
}
