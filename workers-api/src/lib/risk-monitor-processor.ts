import type { Env } from '../types/env'
import { getSupabaseClient } from './supabase'
import { CoinGeckoClient, CoinGeckoPrice } from './coingecko'

export interface RiskMonitorConfig {
  token_id: string
  symbol: string
  sensitivity: 'low' | 'medium' | 'high'
  track_market_cap: boolean
  track_volatility: boolean
}

interface RiskAssessment {
  score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  red_flags: string[]
}

export interface RiskMonitorResult {
  task_id: string
  user_id: string
  changed: boolean
  previous_score: number
  current_score: number
  new_flags: string[]
  message: string
}

export async function processRiskMonitor(env: Env): Promise<RiskMonitorResult[]> {
  const supabase = getSupabaseClient(env, true)
  const results: RiskMonitorResult[] = []

  const { data: tasks, error } = await supabase
    .from('agent_tasks')
    .select('id, user_id, config, metadata')
    .eq('task_type', 'risk_monitor')
    .eq('status', 'active')
    .limit(50)

  if (error || !tasks || tasks.length === 0) {
    console.log('[RiskMonitor] No active risk monitor tasks')
    return results
  }

  const client = new CoinGeckoClient()

  for (const task of tasks) {
    const config = task.config as RiskMonitorConfig
    if (!config?.token_id) continue

    const priceResult = await client.getCoinPrice(config.token_id.toLowerCase())
    if ('error' in priceResult) continue

    const assessment = assessRisk(priceResult, config)
    const previousScore = (task.metadata as Record<string, number>)?.last_risk_score ?? 100
    const previousFlags = ((task.metadata as Record<string, string[]>)?.last_red_flags ?? []) as string[]

    const threshold = config.sensitivity === 'high' ? 5 : config.sensitivity === 'medium' ? 10 : 20
    const scoreDiff = Math.abs(assessment.score - previousScore)
    const newFlags = assessment.red_flags.filter((f) => !previousFlags.includes(f))

    const significantChange = scoreDiff >= threshold || newFlags.length > 0

    if (significantChange) {
      const message = buildRiskMessage(config.symbol, previousScore, assessment, newFlags)

      results.push({
        task_id: task.id,
        user_id: task.user_id,
        changed: true,
        previous_score: previousScore,
        current_score: assessment.score,
        new_flags: newFlags,
        message,
      })

      await supabase.from('notifications').insert({
        user_id: task.user_id,
        type: 'risk_alert',
        title: `风险提醒: ${config.symbol}`,
        message,
        data: {
          task_id: task.id,
          symbol: config.symbol,
          previous_score: previousScore,
          current_score: assessment.score,
          new_flags: newFlags,
          risk_level: assessment.risk_level,
        },
      })
    }

    await supabase
      .from('agent_tasks')
      .update({
        metadata: {
          last_risk_score: assessment.score,
          last_red_flags: assessment.red_flags,
          last_checked_at: new Date().toISOString(),
        },
      })
      .eq('id', task.id)
  }

  console.log(`[RiskMonitor] Processed ${tasks.length} tasks, ${results.length} changes detected`)
  return results
}

function assessRisk(priceData: CoinGeckoPrice, config: RiskMonitorConfig): RiskAssessment {
  const redFlags: string[] = []
  let score = 100

  if (priceData.market_cap_rank === null) {
    score -= 20
    redFlags.push('无市值排名')
  } else if (priceData.market_cap_rank > 500) {
    score -= 15
    redFlags.push(`市值排名较低 (#${priceData.market_cap_rank})`)
  } else if (priceData.market_cap_rank > 100) {
    score -= 5
  }

  if (config.track_market_cap) {
    if (priceData.market_cap < 1_000_000) {
      score -= 25
      redFlags.push('微型市值 (<$1M)')
    } else if (priceData.market_cap < 10_000_000) {
      score -= 15
      redFlags.push('超小市值 (<$10M)')
    } else if (priceData.market_cap < 100_000_000) {
      score -= 5
    }
  }

  if (config.track_volatility) {
    const priceChange = Math.abs(priceData.price_change_24h)
    if (priceChange > 50) {
      score -= 20
      redFlags.push(`极端波动 (${priceData.price_change_24h.toFixed(1)}%)`)
    } else if (priceChange > 20) {
      score -= 10
      redFlags.push(`高波动 (${priceData.price_change_24h.toFixed(1)}%)`)
    }
  }

  score = Math.max(0, Math.min(100, score))

  let riskLevel: 'low' | 'medium' | 'high' | 'critical'
  if (score >= 80) riskLevel = 'low'
  else if (score >= 60) riskLevel = 'medium'
  else if (score >= 40) riskLevel = 'high'
  else riskLevel = 'critical'

  return { score, risk_level: riskLevel, red_flags: redFlags }
}

function buildRiskMessage(
  symbol: string,
  previousScore: number,
  assessment: RiskAssessment,
  newFlags: string[]
): string {
  const parts: string[] = []

  if (assessment.score < previousScore) {
    parts.push(`${symbol} 风险评分下降: ${previousScore} → ${assessment.score}`)
  } else {
    parts.push(`${symbol} 风险评分变化: ${previousScore} → ${assessment.score}`)
  }

  if (newFlags.length > 0) {
    parts.push(`新增风险: ${newFlags.join(', ')}`)
  }

  parts.push(`当前风险等级: ${assessment.risk_level}`)

  return parts.join(' | ')
}
