import type { Env } from '../types/env'
import { getSupabaseClient } from './supabase'
import { createOpenRouterClient } from './openrouter'
import { sendPushToUser, createNotificationPayload } from './push'

interface UserPreferences {
  user_id: string
  risk_tolerance: 'conservative' | 'medium' | 'aggressive' | 'very_aggressive'
  investment_horizon: 'short' | 'medium' | 'long'
  preferred_sectors: string[]
  excluded_sectors: string[]
  preferred_chains: string[]
  min_market_cap: 'any' | 'micro' | 'small' | 'medium' | 'large'
  interest_tags: string[]
  max_recommendations_per_batch: number
}

interface OpportunityConfig {
  enabled: boolean
  frequency: 'daily' | 'weekly' | 'biweekly'
  max_recommendations: number
  include_trending: boolean
  include_sector_match: boolean
  include_similar: boolean
}

interface TrendingToken {
  id: string
  symbol: string
  name: string
  image?: string
  current_price: number
  market_cap: number
  market_cap_rank: number
  price_change_percentage_24h: number
  price_change_percentage_7d_in_currency?: number
  total_volume: number
}

interface Recommendation {
  token_id: string
  symbol: string
  name: string
  coingecko_id: string
  logo_url?: string
  recommendation_type: string
  confidence_score: number
  match_reasons: string[]
  market_data: Record<string, unknown>
  ai_analysis?: string
  risk_level: string
  potential_upside?: number
  time_horizon?: string
}

export async function processOpportunityDiscovery(env: Env): Promise<void> {
  console.log('[OpportunityDiscovery] Starting opportunity discovery processing...')
  
  const supabase = getSupabaseClient(env, true)
  
  const { data: tasks, error } = await supabase
    .from('agent_tasks')
    .select('id, user_id, config')
    .eq('task_type', 'opportunity_finder')
    .eq('status', 'active')
    .limit(50)

  if (error) {
    console.error('[OpportunityDiscovery] Failed to fetch tasks:', error)
    return
  }

  if (!tasks || tasks.length === 0) {
    console.log('[OpportunityDiscovery] No active opportunity_finder tasks')
    return
  }

  console.log(`[OpportunityDiscovery] Processing ${tasks.length} tasks`)

  for (const task of tasks) {
    const t = task as { id: string; user_id: string; config: unknown }
    try {
      await processUserOpportunities(env, t.id, t.user_id, t.config as OpportunityConfig)
    } catch (taskError) {
      console.error(`[OpportunityDiscovery] Task ${t.id} failed:`, taskError)
    }
  }

  console.log('[OpportunityDiscovery] Completed opportunity discovery processing')
}

async function processUserOpportunities(
  env: Env,
  taskId: string,
  userId: string,
  config: OpportunityConfig
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
    const { data: userPrefs } = await supabase
      .from('user_preferences')
      .select('*')
      .eq('user_id', userId)
      .single()

    const preferences: UserPreferences = (userPrefs as UserPreferences | null) || {
      user_id: userId,
      risk_tolerance: 'medium',
      investment_horizon: 'medium',
      preferred_sectors: [],
      excluded_sectors: [],
      preferred_chains: [],
      min_market_cap: 'any',
      interest_tags: [],
      max_recommendations_per_batch: config.max_recommendations || 5
    }

    const { data: holdings } = await supabase
      .from('holdings')
      .select('symbol, coingecko_id')
      .eq('user_id', userId)

    const { data: watchlist } = await supabase
      .from('watchlist')
      .select('symbol, coingecko_id')
      .eq('user_id', userId)

    const { data: recentRecs } = await supabase
      .from('recommendation_history')
      .select('token_id')
      .eq('user_id', userId)
      .gte('recommended_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString())

    const excludeTokens = new Set<string>([
      ...((holdings as unknown as Array<{coingecko_id?: string}>)?.map(h => h.coingecko_id).filter(Boolean) as string[] || []),
      ...((watchlist as unknown as Array<{coingecko_id?: string}>)?.map(w => w.coingecko_id).filter(Boolean) as string[] || []),
      ...((recentRecs as unknown as Array<{token_id: string}>)?.map(r => r.token_id) || [])
    ])

    const candidates = await fetchCandidateTokens(env, preferences, excludeTokens)

    if (candidates.length === 0) {
      console.log(`[OpportunityDiscovery] No candidates found for user ${userId}`)
      await completeRun(supabase, runId, startTime, { recommendations: [] })
      return
    }

    const recommendations = await analyzeAndRankCandidates(
      env,
      candidates,
      preferences,
      config.max_recommendations || 5
    )

    if (recommendations.length === 0) {
      console.log(`[OpportunityDiscovery] No recommendations generated for user ${userId}`)
      await completeRun(supabase, runId, startTime, { recommendations: [] })
      return
    }

    const batchId = crypto.randomUUID()
    const recInserts = recommendations.map((rec, index) => ({
      user_id: userId,
      task_id: taskId,
      run_id: runId,
      ...rec,
      batch_id: batchId,
      batch_position: index + 1,
      expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
    }))

    const { error: insertError } = await supabase
      .from('recommendations')
      .insert(recInserts)

    if (insertError) {
      throw new Error(`Failed to insert recommendations: ${insertError.message}`)
    }

    const historyInserts = recommendations.map(rec => ({
      user_id: userId,
      token_id: rec.coingecko_id,
      recommendation_id: null,
      price_at_recommendation: rec.market_data.current_price
    }))

    await supabase.from('recommendation_history').insert(historyInserts)

    await supabase.from('notifications').insert({
      user_id: userId,
      type: 'recommendation',
      title: '发现新投资机会',
      body: `为您找到 ${recommendations.length} 个潜在投资机会，包括 ${recommendations.slice(0, 2).map(r => r.symbol).join('、')} 等`,
      data: {
        batch_id: batchId,
        count: recommendations.length,
        top_picks: recommendations.slice(0, 3).map(r => ({
          symbol: r.symbol,
          type: r.recommendation_type,
          confidence: r.confidence_score
        }))
      },
      source_type: 'agent_run',
      source_id: runId
    })

    try {
      const payload = createNotificationPayload(
        'recommendation',
        '发现新投资机会',
        `为您找到 ${recommendations.length} 个潜在投资机会`,
        { batch_id: batchId }
      )
      await sendPushToUser(env, userId, payload)
    } catch (pushError) {
      console.error('[OpportunityDiscovery] Push failed:', pushError)
    }

    await completeRun(supabase, runId, startTime, {
      recommendations: recommendations.map(r => ({
        symbol: r.symbol,
        type: r.recommendation_type,
        confidence: r.confidence_score
      })),
      batch_id: batchId
    })

    console.log(`[OpportunityDiscovery] Generated ${recommendations.length} recommendations for user ${userId}`)

  } catch (error) {
    console.error(`[OpportunityDiscovery] Error processing user ${userId}:`, error)
    
    await supabase.from('agent_runs').update({
      status: 'failed',
      completed_at: new Date().toISOString(),
      duration_ms: Date.now() - startTime,
      error_message: error instanceof Error ? error.message : 'Unknown error'
    }).eq('id', runId)
  }
}

async function fetchCandidateTokens(
  env: Env,
  preferences: UserPreferences,
  excludeTokens: Set<string>
): Promise<TrendingToken[]> {
  const candidates: TrendingToken[] = []

  try {
    const trendingUrl = 'https://api.coingecko.com/api/v3/coins/markets?' + new URLSearchParams({
      vs_currency: 'usd',
      order: 'volume_desc',
      per_page: '100',
      page: '1',
      sparkline: 'false',
      price_change_percentage: '24h,7d'
    })

    const response = await fetch(trendingUrl, {
      headers: { 'Accept': 'application/json' }
    })

    if (response.ok) {
      const data = await response.json() as TrendingToken[]
      
      for (const token of data) {
        if (excludeTokens.has(token.id)) continue
        
        if (!passesMarketCapFilter(token.market_cap, preferences.min_market_cap)) continue
        
        candidates.push(token)
      }
    }
  } catch (fetchError) {
    console.error('[OpportunityDiscovery] Failed to fetch trending tokens:', fetchError)
  }

  try {
    const gainersUrl = 'https://api.coingecko.com/api/v3/coins/markets?' + new URLSearchParams({
      vs_currency: 'usd',
      order: 'price_change_percentage_24h_desc',
      per_page: '50',
      page: '1',
      sparkline: 'false',
      price_change_percentage: '24h,7d'
    })

    const response = await fetch(gainersUrl, {
      headers: { 'Accept': 'application/json' }
    })

    if (response.ok) {
      const data = await response.json() as TrendingToken[]
      
      for (const token of data) {
        if (excludeTokens.has(token.id)) continue
        if (candidates.some(c => c.id === token.id)) continue
        if (!passesMarketCapFilter(token.market_cap, preferences.min_market_cap)) continue
        
        candidates.push(token)
      }
    }
  } catch (fetchError) {
    console.error('[OpportunityDiscovery] Failed to fetch gainers:', fetchError)
  }

  return candidates.slice(0, 50)
}

function passesMarketCapFilter(marketCap: number, filter: string): boolean {
  if (filter === 'any') return true
  
  const thresholds: Record<string, number> = {
    micro: 10_000_000,
    small: 100_000_000,
    medium: 1_000_000_000,
    large: 10_000_000_000
  }

  return marketCap >= (thresholds[filter] || 0)
}

async function analyzeAndRankCandidates(
  env: Env,
  candidates: TrendingToken[],
  preferences: UserPreferences,
  maxRecommendations: number
): Promise<Recommendation[]> {
  const scored = candidates.map(token => ({
    token,
    score: calculateOpportunityScore(token, preferences)
  }))

  scored.sort((a, b) => b.score - a.score)

  const topCandidates = scored.slice(0, Math.min(10, maxRecommendations * 2))

  const recommendations: Recommendation[] = []

  for (const { token, score } of topCandidates) {
    if (recommendations.length >= maxRecommendations) break

    const recType = determineRecommendationType(token)
    const riskLevel = determineRiskLevel(token, preferences.risk_tolerance)

    let aiAnalysis: string | undefined

    if (recommendations.length < 3 && env.OPENROUTER_API_KEY) {
      try {
        aiAnalysis = await generateAIAnalysis(env, token)
      } catch {
        console.log('[OpportunityDiscovery] AI analysis skipped')
      }
    }

    recommendations.push({
      token_id: token.id,
      symbol: token.symbol.toUpperCase(),
      name: token.name,
      coingecko_id: token.id,
      logo_url: token.image,
      recommendation_type: recType,
      confidence_score: Math.min(95, Math.round(score)),
      match_reasons: generateMatchReasons(token, recType),
      market_data: {
        current_price: token.current_price,
        market_cap: token.market_cap,
        market_cap_rank: token.market_cap_rank,
        price_change_24h: token.price_change_percentage_24h,
        price_change_7d: token.price_change_percentage_7d_in_currency,
        volume_24h: token.total_volume
      },
      ai_analysis: aiAnalysis,
      risk_level: riskLevel,
      potential_upside: estimatePotentialUpside(token, riskLevel),
      time_horizon: preferences.investment_horizon === 'short' ? '1-4 weeks' : 
                    preferences.investment_horizon === 'medium' ? '1-3 months' : '3-12 months'
    })
  }

  return recommendations
}

function calculateOpportunityScore(token: TrendingToken, preferences: UserPreferences): number {
  let score = 50

  const change24h = token.price_change_percentage_24h || 0
  if (change24h > 0 && change24h < 20) {
    score += Math.min(20, change24h)
  } else if (change24h >= 20) {
    score += 15
  }

  const volumeToMcap = token.total_volume / token.market_cap
  if (volumeToMcap > 0.1) score += 10
  if (volumeToMcap > 0.2) score += 5

  if (token.market_cap_rank && token.market_cap_rank <= 100) {
    score += 10
  } else if (token.market_cap_rank && token.market_cap_rank <= 300) {
    score += 5
  }

  if (preferences.risk_tolerance === 'aggressive' || preferences.risk_tolerance === 'very_aggressive') {
    if (token.market_cap < 1_000_000_000) score += 10
  } else if (preferences.risk_tolerance === 'conservative') {
    if (token.market_cap > 10_000_000_000) score += 10
  }

  return Math.min(100, score)
}

function determineRecommendationType(token: TrendingToken): string {
  const change24h = token.price_change_percentage_24h || 0
  const change7d = token.price_change_percentage_7d_in_currency || 0

  if (change24h > 10 && change7d > 20) return 'trending'
  if (change24h < -10 && token.market_cap > 1_000_000_000) return 'recovery_play'
  if (token.market_cap_rank && token.market_cap_rank <= 50) return 'high_potential'
  
  return 'ai_picked'
}

function determineRiskLevel(token: TrendingToken, _userRisk: string): string {
  if (token.market_cap > 10_000_000_000) return 'low'
  if (token.market_cap > 1_000_000_000) return 'medium'
  if (token.market_cap > 100_000_000) return 'high'
  return 'very_high'
}

function generateMatchReasons(token: TrendingToken, recType: string): string[] {
  const reasons: string[] = []

  if (recType === 'trending') {
    reasons.push('近期价格和交易量显著上涨')
  }
  if (recType === 'recovery_play') {
    reasons.push('大市值代币出现回调，可能存在抄底机会')
  }
  if (recType === 'high_potential') {
    reasons.push('市值排名靠前，流动性充足')
  }

  if (token.market_cap_rank && token.market_cap_rank <= 100) {
    reasons.push(`市值排名 #${token.market_cap_rank}`)
  }

  const volumeToMcap = token.total_volume / token.market_cap
  if (volumeToMcap > 0.15) {
    reasons.push('交易活跃度较高')
  }

  if (reasons.length === 0) {
    reasons.push('符合您的投资偏好')
  }

  return reasons
}

function estimatePotentialUpside(token: TrendingToken, riskLevel: string): number {
  const baseUpside: Record<string, number> = {
    low: 20,
    medium: 50,
    high: 100,
    very_high: 200
  }

  return baseUpside[riskLevel] || 50
}

async function generateAIAnalysis(env: Env, token: TrendingToken): Promise<string> {
  const openrouter = createOpenRouterClient(env)

  const prompt = `简要分析 ${token.name} (${token.symbol.toUpperCase()}) 的投资潜力。

当前数据:
- 价格: $${token.current_price}
- 市值: $${(token.market_cap / 1_000_000_000).toFixed(2)}B
- 24h涨跌: ${token.price_change_percentage_24h?.toFixed(2)}%
- 市值排名: #${token.market_cap_rank}

请用2-3句话给出简洁的投资观点，包括主要机会和风险。用中文回复。`

  const response = await openrouter.request({
    model: 'deepseek/deepseek-chat',
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 200,
    temperature: 0.7
  })

  const data = await response.json() as { choices: Array<{ message: { content: string } }> }
  return data.choices[0]?.message?.content || ''
}

async function completeRun(
  supabase: ReturnType<typeof getSupabaseClient>,
  runId: string,
  startTime: number,
  output: Record<string, unknown>
): Promise<void> {
  await supabase.from('agent_runs').update({
    status: 'completed',
    completed_at: new Date().toISOString(),
    duration_ms: Date.now() - startTime,
    output
  }).eq('id', runId)
}
