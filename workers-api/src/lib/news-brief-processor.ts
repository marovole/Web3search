import type { Env } from '../types/env'
import { getSupabaseClient } from './supabase'
import { fetchNewsForTokens, getTopNews, formatNewsForSummary, CryptoPanicNews } from './cryptopanic'
import { createOpenRouterClient } from './openrouter'
import { sendPushToUser, createNotificationPayload } from './push'

interface NewsBriefConfig {
  enabled: boolean
  frequency: 'hourly' | 'daily'
  include_watchlist: boolean
  max_articles: number
  language: 'zh' | 'en'
}

interface WatchlistItem {
  symbol: string
  name: string
}

export async function processNewsBrief(env: Env): Promise<void> {
  console.log('[NewsBrief] Starting news brief processing...')
  
  const supabase = getSupabaseClient(env, true)
  
  const { data: tasks, error } = await supabase
    .from('agent_tasks')
    .select('id, user_id, config')
    .eq('task_type', 'news_brief')
    .eq('status', 'active')
    .limit(100)

  if (error) {
    console.error('[NewsBrief] Failed to fetch tasks:', error)
    return
  }

  if (!tasks || tasks.length === 0) {
    console.log('[NewsBrief] No active news_brief tasks')
    return
  }

  console.log(`[NewsBrief] Processing ${tasks.length} tasks`)

  for (const task of tasks) {
    const t = task as { id: string; user_id: string; config: unknown }
    try {
      await processUserNewsBrief(env, t.id, t.user_id, t.config as NewsBriefConfig)
    } catch (taskError) {
      console.error(`[NewsBrief] Task ${t.id} failed:`, taskError)
    }
  }

  console.log('[NewsBrief] Completed news brief processing')
}

async function processUserNewsBrief(
  env: Env,
  taskId: string,
  userId: string,
  config: NewsBriefConfig
): Promise<void> {
  const supabase = getSupabaseClient(env, true)
  const startTime = Date.now()

  const runId = crypto.randomUUID()
  await supabase.from('agent_runs').insert({
    id: runId,
    task_id: taskId,
    user_id: userId,
    status: 'running',
    triggered_by: 'schedule',
    input: { config }
  })

  try {
    let tokenSymbols: string[] = []

    if (config.include_watchlist) {
      const { data: watchlist } = await supabase
        .from('watchlist')
        .select('symbol, name')
        .eq('user_id', userId)
        .limit(20)

      if (watchlist && watchlist.length > 0) {
        tokenSymbols = (watchlist as unknown as WatchlistItem[]).map(w => w.symbol)
      }
    }

    const news = await fetchNewsForTokens(env, tokenSymbols)
    const topNews = getTopNews(news, config.max_articles || 5)

    if (topNews.length === 0) {
      await supabase.from('agent_runs').update({
        status: 'completed',
        completed_at: new Date().toISOString(),
        duration_ms: Date.now() - startTime,
        output: { message: 'No relevant news found', news_count: 0 }
      }).eq('id', runId)
      return
    }

    const summary = await generateNewsSummary(env, topNews, config.language || 'zh')

    await supabase.from('notifications').insert({
      user_id: userId,
      type: 'news_brief',
      title: config.language === 'en' ? 'Crypto News Brief' : '加密货币新闻速报',
      body: summary.brief,
      data: {
        full_summary: summary.full,
        articles: topNews.map(n => ({
          title: n.title,
          url: n.url,
          source: n.source.title,
          currencies: n.currencies?.map(c => c.code)
        })),
        generated_at: new Date().toISOString()
      },
      source_type: 'agent_task',
      source_id: taskId,
      priority: 'normal'
    })

    await sendPushToUser(env, userId, createNotificationPayload(
      'news_brief',
      config.language === 'en' ? '📰 Crypto News Brief' : '📰 加密货币新闻速报',
      summary.brief,
      { link: '/notifications?type=news_brief' }
    ))

    await supabase.from('agent_runs').update({
      status: 'completed',
      completed_at: new Date().toISOString(),
      duration_ms: Date.now() - startTime,
      output: {
        news_count: topNews.length,
        summary_length: summary.full.length,
        tokens_mentioned: topNews.flatMap(n => n.currencies?.map(c => c.code) || [])
      },
      notification_sent: true
    }).eq('id', runId)

    await supabase.from('agent_tasks').update({
      last_run_at: new Date().toISOString()
    }).eq('id', taskId)

  } catch (error) {
    console.error(`[NewsBrief] Error processing task ${taskId}:`, error)
    
    await supabase.from('agent_runs').update({
      status: 'failed',
      completed_at: new Date().toISOString(),
      duration_ms: Date.now() - startTime,
      error_message: error instanceof Error ? error.message : 'Unknown error',
      error_code: 'PROCESSING_ERROR'
    }).eq('id', runId)

    await supabase.from('agent_tasks').update({
      last_run_at: new Date().toISOString()
    }).eq('id', taskId)
  }
}

async function generateNewsSummary(
  env: Env,
  news: CryptoPanicNews[],
  language: 'zh' | 'en'
): Promise<{ brief: string; full: string }> {
  const newsText = formatNewsForSummary(news)
  
  const systemPrompt = language === 'zh'
    ? `你是一位专业的加密货币分析师，负责为投资者提供每日新闻速报。
请根据提供的新闻列表，生成简洁的摘要。

输出格式：
1. 一句话概述（不超过50字，用于推送通知）
2. 详细摘要（3-5个要点，每个要点1-2句话）

要求：
- 突出重要的市场动态和价格相关信息
- 标注利好/利空情绪
- 使用中文回复`
    : `You are a professional cryptocurrency analyst providing daily news briefs for investors.
Based on the news list provided, generate a concise summary.

Output format:
1. One-line overview (max 100 chars, for push notification)
2. Detailed summary (3-5 bullet points, 1-2 sentences each)

Requirements:
- Highlight important market movements and price-related info
- Mark bullish/bearish sentiment
- Reply in English`

  const userPrompt = language === 'zh'
    ? `以下是最近的加密货币新闻：\n\n${newsText}\n\n请生成新闻速报摘要。`
    : `Here are the recent crypto news:\n\n${newsText}\n\nPlease generate a news brief summary.`

  try {
    const openrouter = createOpenRouterClient(env)
    const response = await openrouter.request({
      model: 'deepseek/deepseek-chat',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0.3,
      max_tokens: 500
    })

    const data = await response.json() as { choices: Array<{ message: { content: string } }> }
    const content = data.choices[0]?.message?.content || ''
    
    const lines = content.split('\n').filter((line: string) => line.trim())
    const brief = lines[0]?.replace(/^[1\.\-\*\s]+/, '').trim() || 
                  (language === 'zh' ? '查看今日加密货币市场要闻' : 'Check today\'s crypto market news')
    
    return {
      brief: brief.slice(0, 100),
      full: content
    }
  } catch (error) {
    console.error('[NewsBrief] LLM summary generation failed:', error)
    
    const fallbackBrief = language === 'zh'
      ? `发现 ${news.length} 条相关新闻`
      : `Found ${news.length} relevant news articles`
    
    return {
      brief: fallbackBrief,
      full: newsText
    }
  }
}
