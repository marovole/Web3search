import { Hono } from 'hono'
import { streamSSE } from 'hono/streaming'
import type { Env } from '../types/env'
import { authMiddleware, getCurrentUser } from '../middlewares/auth'
import { getSupabaseClient } from '../lib/supabase'
import { 
  parseAgentIntent, 
  validateIntentConditions, 
  buildTaskConfig,
  getIntentTaskType,
  generateConfirmationMessage
} from '../lib/intent-parser'
import type { 
  ParsedIntent, 
  ConversationMessage, 
  TaskCreationResult 
} from '../types/agent-intent'
import { createOpenRouterClient } from '../lib/openrouter'

const app = new Hono<{ Bindings: Env }>()

app.post('/', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const body = await c.req.json<{
    message: string
    conversationId?: string
    confirmIntent?: boolean
  }>()

  if (!body.message?.trim()) {
    return c.json({ error: { code: 'INVALID_INPUT', message: 'Message is required', status: 400 } }, 400)
  }

  const supabase = getSupabaseClient(c.env, true)
  const conversationId = body.conversationId || crypto.randomUUID()

  let conversationHistory: Array<{ role: string; content: string }> = []
  
  if (body.conversationId) {
    const { data: messages } = await supabase
      .from('agent_conversations')
      .select('role, content')
      .eq('conversation_id', body.conversationId)
      .eq('user_id', user.id)
      .order('created_at', { ascending: true })
      .limit(10)
    
    if (messages) {
      conversationHistory = messages as unknown as { role: string; content: string }[]
    }
  }

  const parseResult = await parseAgentIntent(c.env, body.message, conversationHistory)

  if (!parseResult.success || !parseResult.intent) {
    const responseMessage = parseResult.error || '抱歉，我没有理解您的意思。您可以尝试说：\n- "当BTC跌破50000时提醒我"\n- "监控ETH的风险"\n- "查看我的持仓"'
    
    await saveMessages(supabase, user.id, conversationId, body.message, responseMessage)
    
    return c.json({
      conversationId,
      message: responseMessage,
      intent: null,
      suggestions: parseResult.suggestions
    })
  }

  const intent = parseResult.intent

  const validation = validateIntentConditions(intent)
  if (!validation.valid) {
    const responseMessage = `需要更多信息：\n${validation.errors.map(e => `• ${e}`).join('\n')}`
    await saveMessages(supabase, user.id, conversationId, body.message, responseMessage, intent)
    
    return c.json({
      conversationId,
      message: responseMessage,
      intent,
      requiresMoreInfo: true,
      missingFields: validation.errors
    })
  }

  if (intent.requiresConfirmation && !body.confirmIntent) {
    const confirmMessage = generateConfirmationMessage(intent)
    await saveMessages(supabase, user.id, conversationId, body.message, confirmMessage, intent)
    
    return c.json({
      conversationId,
      message: confirmMessage,
      intent,
      requiresConfirmation: true,
      confirmationDetails: {
        intentType: intent.type,
        entities: intent.entities,
        previewConfig: buildTaskConfig(intent)
      }
    })
  }

  const taskResult = await executeIntent(c.env, user.id, intent, supabase)

  await saveMessages(supabase, user.id, conversationId, body.message, taskResult.message, intent, taskResult)

  return c.json({
    conversationId,
    message: taskResult.message,
    intent,
    taskResult
  })
})

app.get('/stream', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const message = c.req.query('message')
  const conversationId = c.req.query('conversationId') || crypto.randomUUID()

  if (!message?.trim()) {
    return c.json({ error: { code: 'INVALID_INPUT', message: 'Message is required', status: 400 } }, 400)
  }

  return streamSSE(c, async (stream) => {
    try {
      await stream.writeSSE({ event: 'start', data: JSON.stringify({ conversationId }) })

      await stream.writeSSE({ event: 'thinking', data: '正在理解您的意图...' })

      const parseResult = await parseAgentIntent(c.env, message)

      if (!parseResult.success || !parseResult.intent) {
        await stream.writeSSE({ 
          event: 'message', 
          data: JSON.stringify({
            content: '抱歉，我没有理解您的意思。请用更清晰的方式描述。',
            suggestions: parseResult.suggestions
          })
        })
        await stream.writeSSE({ event: 'done', data: '' })
        return
      }

      const intent = parseResult.intent
      await stream.writeSSE({ 
        event: 'intent', 
        data: JSON.stringify({
          type: intent.type,
          confidence: intent.confidence,
          entities: intent.entities
        })
      })

      const validation = validateIntentConditions(intent)
      if (!validation.valid) {
        await stream.writeSSE({
          event: 'message',
          data: JSON.stringify({
            content: `需要更多信息：\n${validation.errors.join('\n')}`,
            requiresMoreInfo: true
          })
        })
        await stream.writeSSE({ event: 'done', data: '' })
        return
      }

      if (intent.requiresConfirmation) {
        await stream.writeSSE({
          event: 'confirmation',
          data: JSON.stringify({
            message: generateConfirmationMessage(intent),
            previewConfig: buildTaskConfig(intent)
          })
        })
        await stream.writeSSE({ event: 'done', data: '' })
        return
      }

      await stream.writeSSE({ event: 'executing', data: '正在执行...' })

      const supabase = getSupabaseClient(c.env, true)
      const taskResult = await executeIntent(c.env, user.id, intent, supabase)

      await stream.writeSSE({
        event: 'result',
        data: JSON.stringify(taskResult)
      })

      await stream.writeSSE({ event: 'done', data: '' })

    } catch (error) {
      console.error('[Conversation Stream] Error:', error)
      await stream.writeSSE({
        event: 'error',
        data: JSON.stringify({ message: '处理过程中出现错误' })
      })
    }
  })
})

app.get('/history', authMiddleware(), async (c) => {
  const user = getCurrentUser(c)
  if (!user) {
    return c.json({ error: { code: 'NOT_AUTHENTICATED', message: 'Not authenticated', status: 401 } }, 401)
  }

  const supabase = getSupabaseClient(c.env, true)
  const conversationId = c.req.query('conversationId')
  const limit = Math.min(parseInt(c.req.query('limit') || '50'), 100)

  let query = supabase
    .from('agent_conversations')
    .select('*')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .limit(limit)

  if (conversationId) {
    query = query.eq('conversation_id', conversationId)
  }

  const { data, error } = await query

  if (error) {
    return c.json({ error: { code: 'DB_ERROR', message: error.message, status: 500 } }, 500)
  }

  return c.json({ messages: data || [] })
})

async function saveMessages(
  supabase: ReturnType<typeof getSupabaseClient>,
  userId: string,
  conversationId: string,
  userMessage: string,
  assistantMessage: string,
  intent?: ParsedIntent,
  taskResult?: TaskCreationResult
): Promise<void> {
  const messages = [
    {
      user_id: userId,
      conversation_id: conversationId,
      role: 'user',
      content: userMessage
    },
    {
      user_id: userId,
      conversation_id: conversationId,
      role: 'assistant',
      content: assistantMessage,
      intent: intent ? JSON.stringify(intent) : null,
      task_result: taskResult ? JSON.stringify(taskResult) : null
    }
  ]

  await supabase.from('agent_conversations').insert(messages)
}

async function executeIntent(
  env: Env,
  userId: string,
  intent: ParsedIntent,
  supabase: ReturnType<typeof getSupabaseClient>
): Promise<TaskCreationResult> {
  const taskType = getIntentTaskType(intent.type)

  if (taskType) {
    const config = buildTaskConfig(intent)
    const taskName = generateTaskName(intent)

    const { data: task, error } = await supabase
      .from('agent_tasks')
      .insert({
        user_id: userId,
        name: taskName,
        type: taskType,
        task_type: taskType,
        status: 'active',
        config
      })
      .select()
      .single()

    if (error || !task) {
      return {
        success: false,
        message: `创建任务失败: ${error?.message || 'Unknown error'}`
      }
    }

    const taskData = task as { id: string }
    return {
      success: true,
      taskId: taskData.id,
      taskType,
      message: generateSuccessMessage(intent, taskData.id)
    }
  }

  switch (intent.type) {
    case 'list_tasks': {
      const { data: tasks } = await supabase
        .from('agent_tasks')
        .select('id, name, type, status, created_at')
        .eq('user_id', userId)
        .eq('status', 'active')
        .order('created_at', { ascending: false })
        .limit(10)

      if (!tasks || tasks.length === 0) {
        return { success: true, message: '您目前没有活动的任务。' }
      }

      const taskList = tasks.map((t, i) => `${i + 1}. ${t.name} (${t.type})`).join('\n')
      return { success: true, message: `您的活动任务：\n${taskList}` }
    }

    case 'check_portfolio': {
      const { data: holdings } = await supabase
        .from('holdings')
        .select('symbol, quantity')
        .eq('user_id', userId)

      if (!holdings || holdings.length === 0) {
        return { success: true, message: '您还没有添加持仓。可以去持仓页面添加。' }
      }

      const holdingsList = holdings.map(h => `• ${h.symbol}: ${h.quantity}`).join('\n')
      return { success: true, message: `您的持仓：\n${holdingsList}` }
    }

    case 'get_recommendations': {
      const { data: recs } = await supabase
        .from('recommendations')
        .select('symbol, name, recommendation_type, confidence_score')
        .eq('user_id', userId)
        .eq('status', 'active')
        .order('created_at', { ascending: false })
        .limit(5)

      if (!recs || recs.length === 0) {
        return { success: true, message: '暂无新的推荐。系统会在每周三为您发现投资机会。' }
      }

      const recList = recs.map(r => `• ${r.symbol} - ${r.name} (置信度: ${r.confidence_score}%)`).join('\n')
      return { success: true, message: `最新推荐：\n${recList}` }
    }

    case 'check_price': {
      const symbol = intent.entities.tokens?.[0]?.symbol
      if (!symbol) {
        return { success: false, message: '请指定要查询的代币' }
      }

      try {
        const response = await fetch(
          `https://api.coingecko.com/api/v3/simple/price?ids=${symbol.toLowerCase()}&vs_currencies=usd&include_24hr_change=true`
        )
        const data = await response.json() as Record<string, { usd: number; usd_24h_change: number }>
        const tokenData = data[symbol.toLowerCase()]
        
        if (tokenData) {
          const change = tokenData.usd_24h_change?.toFixed(2)
          const changeStr = parseFloat(change || '0') >= 0 ? `+${change}%` : `${change}%`
          return { 
            success: true, 
            message: `${symbol} 当前价格: $${tokenData.usd.toLocaleString()} (24h: ${changeStr})` 
          }
        }
        return { success: false, message: `未找到 ${symbol} 的价格数据` }
      } catch {
        return { success: false, message: '获取价格失败，请稍后重试' }
      }
    }

    default:
      return { success: false, message: '抱歉，这个功能暂未支持。' }
  }
}

function generateTaskName(intent: ParsedIntent): string {
  switch (intent.type) {
    case 'create_price_alert': {
      const token = intent.entities.tokens?.[0]?.symbol || 'Token'
      const condition = intent.entities.priceCondition
      const conditionText = condition?.type === 'below' ? '跌破' : '涨到'
      return `${token} ${conditionText} $${condition?.value} 提醒`
    }
    case 'create_risk_monitor': {
      const tokens = intent.entities.tokens?.map(t => t.symbol).join('/') || 'Token'
      return `${tokens} 风险监控`
    }
    case 'create_news_brief':
      return '新闻速报订阅'
    case 'create_portfolio_diagnosis':
      return '持仓诊断'
    case 'create_opportunity_finder':
      return '机会发现'
    default:
      return '自定义任务'
  }
}

function generateSuccessMessage(intent: ParsedIntent, taskId: string): string {
  switch (intent.type) {
    case 'create_price_alert': {
      const token = intent.entities.tokens?.[0]?.symbol
      const condition = intent.entities.priceCondition
      const conditionText = condition?.type === 'below' ? '跌破' : '涨到'
      return `已创建提醒：当 ${token} ${conditionText} $${condition?.value} 时会通知您。`
    }
    case 'create_risk_monitor': {
      const tokens = intent.entities.tokens?.map(t => t.symbol).join('、')
      return `已开始监控 ${tokens} 的风险变化。如有异常会立即通知您。`
    }
    case 'create_news_brief':
      return '已订阅新闻速报。您将定期收到加密货币新闻摘要。'
    case 'create_portfolio_diagnosis':
      return '已设置持仓诊断。系统将每周一为您生成投资组合健康报告。'
    case 'create_opportunity_finder':
      return '已开启机会发现。系统将每周三为您发现潜在投资机会。'
    default:
      return `任务创建成功 (ID: ${taskId.slice(0, 8)})`
  }
}

export default app
