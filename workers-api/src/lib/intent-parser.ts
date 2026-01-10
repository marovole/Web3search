/**
 * Intent Parser for Conversational Agent
 * Parses natural language into structured agent intents
 */

import type { Env } from '../types/env'
import { createOpenRouterClient } from './openrouter'
import type {
  IntentType,
  ParsedIntent,
  IntentEntities,
  IntentParseResult,
  TokenEntity,
  PriceConditionEntity,
  PercentChangeEntity,
  CONFIDENCE_THRESHOLD,
  needsConfirmation,
} from '../types/agent-intent'

const INTENT_PARSER_PROMPT = `你是一个加密货币投资助手的意图解析器。分析用户的自然语言输入，识别他们想要执行的操作。

## 可识别的意图类型

1. **create_price_alert** - 创建价格提醒
   - 触发词: 提醒、通知、告诉我、当...时、跌破、涨到、突破
   - 需要提取: 代币符号、价格条件(above/below)、目标价格

2. **create_risk_monitor** - 创建风险监控
   - 触发词: 监控风险、盯着、安全评分、风险升高
   - 需要提取: 代币符号

3. **create_news_brief** - 订阅新闻速报
   - 触发词: 新闻、资讯、推送、订阅、每天/每小时
   - 需要提取: 代币符号(可选)、频率

4. **create_portfolio_diagnosis** - 持仓诊断
   - 触发词: 分析持仓、诊断组合、检查健康度
   
5. **create_opportunity_finder** - 机会发现
   - 触发词: 发现机会、推荐、潜力币、适合我

6. **list_tasks** - 查看任务
   - 触发词: 查看任务、列出、有哪些

7. **pause_task** / **resume_task** / **delete_task** - 任务管理
   - 触发词: 暂停、停止、恢复、继续、删除、取消

8. **check_price** - 查询价格
   - 触发词: 多少钱、价格、涨了多少

9. **check_portfolio** - 查看持仓
   - 触发词: 我的持仓、我的资产、值多少

10. **get_recommendations** - 获取推荐
    - 触发词: 有什么推荐、给我看看

11. **update_preferences** - 更新偏好
    - 触发词: 更激进、调整偏好、风险偏好

12. **unknown** - 无法识别

## 代币符号识别

常见代币:
- BTC/比特币/Bitcoin
- ETH/以太坊/Ethereum  
- SOL/Solana
- BNB/币安币
- XRP/瑞波
- ADA/艾达/Cardano
- DOGE/狗狗币
- DOT/波卡/Polkadot
- MATIC/Polygon
- SHIB/柴犬币
- AVAX/雪崩
- LINK/Chainlink
- UNI/Uniswap
- ATOM/Cosmos

## 输出格式

返回JSON格式:
{
  "intent_type": "意图类型",
  "confidence": 0.0-1.0的置信度,
  "entities": {
    "tokens": [{"symbol": "BTC", "confidence": 0.95}],
    "price_condition": {"type": "below", "value": 50000, "currency": "usd"},
    "percent_change": {"type": "decrease", "value": 10, "period": "24h"},
    "frequency": "daily",
    "task_id": null
  },
  "requires_confirmation": true/false,
  "confirmation_message": "确认消息(如需要)"
}

注意:
- confidence低于0.8时设置requires_confirmation为true
- 如果意图不明确，返回unknown并在confirmation_message中询问用户
- 价格单位默认为USD，除非明确指定BTC或ETH
- 时间周期默认为24h`

interface LLMIntentResponse {
  intent_type: string
  confidence: number
  entities: {
    tokens?: Array<{ symbol: string; confidence: number }>
    price_condition?: { type: string; value: number; currency: string }
    percent_change?: { type: string; value: number; period: string }
    frequency?: string
    task_id?: string
  }
  requires_confirmation: boolean
  confirmation_message?: string
}

export async function parseAgentIntent(
  env: Env,
  userMessage: string,
  conversationHistory?: Array<{ role: string; content: string }>
): Promise<IntentParseResult> {
  try {
    const quickMatch = tryQuickMatch(userMessage)
    if (quickMatch && quickMatch.confidence >= 0.9) {
      return { success: true, intent: quickMatch }
    }

    const openrouter = createOpenRouterClient(env)
    
    const messages = [
      { role: 'system' as const, content: INTENT_PARSER_PROMPT },
      ...(conversationHistory || []).slice(-4).map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content
      })),
      { role: 'user' as const, content: userMessage }
    ]

    const response = await openrouter.request({
      model: 'deepseek/deepseek-chat',
      messages,
      max_tokens: 500,
      temperature: 0.1
    })

    const data = await response.json() as { choices: Array<{ message: { content: string } }> }
    const content = data.choices[0]?.message?.content || ''

    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (!jsonMatch) {
      return {
        success: false,
        error: 'Failed to parse intent',
        suggestions: ['请用更清晰的方式描述您想要做什么']
      }
    }

    const parsed = JSON.parse(jsonMatch[0]) as LLMIntentResponse

    const intent: ParsedIntent = {
      type: (parsed.intent_type || 'unknown') as IntentType,
      confidence: parsed.confidence || 0.5,
      entities: mapEntities(parsed.entities),
      originalText: userMessage,
      requiresConfirmation: parsed.requires_confirmation || parsed.confidence < 0.8,
      confirmationMessage: parsed.confirmation_message
    }

    return { success: true, intent }

  } catch (error) {
    console.error('[IntentParser] Parse error:', error)
    return {
      success: false,
      error: 'Intent parsing failed',
      suggestions: ['请重新描述您的需求']
    }
  }
}

function mapEntities(raw: LLMIntentResponse['entities']): IntentEntities {
  const entities: IntentEntities = {}

  if (raw.tokens && raw.tokens.length > 0) {
    entities.tokens = raw.tokens.map(t => ({
      symbol: t.symbol.toUpperCase(),
      confidence: t.confidence
    }))
  }

  if (raw.price_condition) {
    entities.priceCondition = {
      type: raw.price_condition.type as 'above' | 'below' | 'crosses',
      value: raw.price_condition.value,
      currency: (raw.price_condition.currency || 'usd') as 'usd' | 'btc' | 'eth'
    }
  }

  if (raw.percent_change) {
    entities.percentChange = {
      type: raw.percent_change.type as 'increase' | 'decrease' | 'change',
      value: raw.percent_change.value,
      period: (raw.percent_change.period || '24h') as '1h' | '24h' | '7d' | '30d'
    }
  }

  if (raw.frequency) {
    entities.frequency = raw.frequency as 'hourly' | 'daily' | 'weekly'
  }

  if (raw.task_id) {
    entities.taskId = raw.task_id
  }

  return entities
}

function tryQuickMatch(text: string): ParsedIntent | null {
  const normalized = text.toLowerCase().trim()

  if (/查看.*(任务|提醒|监控)/.test(normalized) || /我有哪些/.test(normalized)) {
    return {
      type: 'list_tasks',
      confidence: 0.95,
      entities: {},
      originalText: text,
      requiresConfirmation: false
    }
  }

  if (/我的(持仓|资产|组合)/.test(normalized) || /值多少/.test(normalized)) {
    return {
      type: 'check_portfolio',
      confidence: 0.95,
      entities: {},
      originalText: text,
      requiresConfirmation: false
    }
  }

  if (/有什么推荐/.test(normalized) || /给我.*推荐/.test(normalized)) {
    return {
      type: 'get_recommendations',
      confidence: 0.9,
      entities: {},
      originalText: text,
      requiresConfirmation: false
    }
  }

  const priceAlertMatch = normalized.match(/(btc|eth|sol|bnb|xrp|ada|doge|dot|matic|shib|avax|link|uni|atom|比特币|以太坊).*(跌破|低于|涨到|突破|超过).*?(\d+(?:\.\d+)?)/i)
  if (priceAlertMatch) {
    const tokenMap: Record<string, string> = {
      '比特币': 'BTC', '以太坊': 'ETH',
      'btc': 'BTC', 'eth': 'ETH', 'sol': 'SOL', 'bnb': 'BNB',
      'xrp': 'XRP', 'ada': 'ADA', 'doge': 'DOGE', 'dot': 'DOT',
      'matic': 'MATIC', 'shib': 'SHIB', 'avax': 'AVAX',
      'link': 'LINK', 'uni': 'UNI', 'atom': 'ATOM'
    }
    const symbol = tokenMap[priceAlertMatch[1].toLowerCase()] || priceAlertMatch[1].toUpperCase()
    const conditionWord = priceAlertMatch[2]
    const price = parseFloat(priceAlertMatch[3])
    const conditionType = ['跌破', '低于'].includes(conditionWord) ? 'below' : 'above'

    return {
      type: 'create_price_alert',
      confidence: 0.92,
      entities: {
        tokens: [{ symbol, confidence: 0.95 }],
        priceCondition: { type: conditionType, value: price, currency: 'usd' }
      },
      originalText: text,
      requiresConfirmation: false
    }
  }

  const priceCheckMatch = normalized.match(/(btc|eth|sol|bnb|比特币|以太坊).*(多少钱|价格|现价)/i)
  if (priceCheckMatch) {
    const tokenMap: Record<string, string> = { '比特币': 'BTC', '以太坊': 'ETH' }
    const symbol = tokenMap[priceCheckMatch[1]] || priceCheckMatch[1].toUpperCase()
    return {
      type: 'check_price',
      confidence: 0.95,
      entities: { tokens: [{ symbol, confidence: 0.95 }] },
      originalText: text,
      requiresConfirmation: false
    }
  }

  return null
}

export function validateIntentConditions(intent: ParsedIntent): { valid: boolean; errors: string[] } {
  const errors: string[] = []

  switch (intent.type) {
    case 'create_price_alert':
      if (!intent.entities.tokens || intent.entities.tokens.length === 0) {
        errors.push('请指定要监控的代币')
      }
      if (!intent.entities.priceCondition) {
        errors.push('请指定价格条件（涨到/跌破多少）')
      }
      break

    case 'create_risk_monitor':
      if (!intent.entities.tokens || intent.entities.tokens.length === 0) {
        errors.push('请指定要监控风险的代币')
      }
      break

    case 'pause_task':
    case 'resume_task':
    case 'delete_task':
      break

    case 'check_price':
      if (!intent.entities.tokens || intent.entities.tokens.length === 0) {
        errors.push('请指定要查询的代币')
      }
      break
  }

  return { valid: errors.length === 0, errors }
}

export function buildTaskConfig(intent: ParsedIntent): Record<string, unknown> {
  switch (intent.type) {
    case 'create_price_alert':
      return {
        token_id: intent.entities.tokens?.[0]?.symbol.toLowerCase(),
        symbol: intent.entities.tokens?.[0]?.symbol,
        condition: {
          type: intent.entities.priceCondition?.type || 'below',
          value: intent.entities.priceCondition?.value,
          currency: intent.entities.priceCondition?.currency || 'usd'
        },
        enabled: true
      }

    case 'create_risk_monitor':
      return {
        tokens: intent.entities.tokens?.map(t => ({
          token_id: t.symbol.toLowerCase(),
          symbol: t.symbol
        })) || [],
        threshold: intent.entities.riskThreshold || 70,
        enabled: true
      }

    case 'create_news_brief':
      return {
        enabled: true,
        frequency: intent.entities.frequency || 'daily',
        include_watchlist: true,
        max_articles: 10,
        language: 'zh'
      }

    case 'create_portfolio_diagnosis':
      return {
        enabled: true,
        frequency: 'weekly'
      }

    case 'create_opportunity_finder':
      return {
        enabled: true,
        frequency: 'weekly',
        max_recommendations: 5,
        include_trending: true,
        include_sector_match: true,
        include_similar: true
      }

    default:
      return {}
  }
}

export function getIntentTaskType(intentType: IntentType): string | null {
  const mapping: Partial<Record<IntentType, string>> = {
    create_price_alert: 'price_alert',
    create_risk_monitor: 'risk_monitor',
    create_news_brief: 'news_brief',
    create_portfolio_diagnosis: 'portfolio_health',
    create_opportunity_finder: 'opportunity_finder'
  }
  return mapping[intentType] || null
}

export function generateConfirmationMessage(intent: ParsedIntent): string {
  switch (intent.type) {
    case 'create_price_alert': {
      const token = intent.entities.tokens?.[0]?.symbol || '代币'
      const condition = intent.entities.priceCondition
      const conditionText = condition?.type === 'below' ? '跌破' : '涨到'
      return `确认创建提醒：当 ${token} ${conditionText} $${condition?.value} 时通知您？`
    }

    case 'create_risk_monitor': {
      const tokens = intent.entities.tokens?.map(t => t.symbol).join('、') || '代币'
      return `确认开始监控 ${tokens} 的风险评分变化？`
    }

    case 'create_news_brief': {
      const freq = intent.entities.frequency === 'hourly' ? '每小时' : 
                   intent.entities.frequency === 'daily' ? '每天' : '每周'
      return `确认订阅${freq}新闻速报？`
    }

    case 'delete_task':
      return '确认删除该任务？此操作不可恢复。'

    case 'pause_task':
      return '确认暂停该任务？'

    default:
      return '确认执行此操作？'
  }
}
