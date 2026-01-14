import type { Env } from '../types/env'
import { getSupabaseClient } from './supabase'
import { createOpenRouterClient } from './openrouter'
import { sendPushToUser, createNotificationPayload } from './push'

interface Holding {
  id: string
  symbol: string
  name: string
  quantity: number
  coingecko_id: string | null
  avg_buy_price: number | null
  total_cost_basis: number | null
  is_staked: boolean
  staking_apy: number | null
}

interface HoldingWithPrice extends Holding {
  current_price: number | null
  current_value: number | null
  pnl: number | null
  pnl_percent: number | null
  allocation_percent: number
}

interface DiagnosisConfig {
  enabled: boolean
  include_recommendations: boolean
  language: 'zh' | 'en'
}

export async function processPortfolioDiagnosis(env: Env): Promise<void> {
  console.log('[PortfolioDiagnosis] Starting portfolio diagnosis processing...')
  
  const supabase = getSupabaseClient(env, true)
  
  const { data: tasks, error } = await supabase
    .from('agent_tasks')
    .select('id, user_id, config')
    .eq('task_type', 'portfolio_health')
    .eq('status', 'active')
    .limit(50)

  if (error) {
    console.error('[PortfolioDiagnosis] Failed to fetch tasks:', error)
    return
  }

  if (!tasks || tasks.length === 0) {
    console.log('[PortfolioDiagnosis] No active portfolio_health tasks')
    return
  }

  console.log(`[PortfolioDiagnosis] Processing ${tasks.length} tasks`)

  for (const task of tasks) {
    const t = task as { id: string; user_id: string; config: unknown }
    try {
      await processUserPortfolio(env, t.id, t.user_id, t.config as DiagnosisConfig)
    } catch (taskError) {
      console.error(`[PortfolioDiagnosis] Task ${t.id} failed:`, taskError)
    }
  }

  console.log('[PortfolioDiagnosis] Completed portfolio diagnosis processing')
}

async function processUserPortfolio(
  env: Env,
  taskId: string,
  userId: string,
  config: DiagnosisConfig
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
    const { data: holdings } = await supabase
      .from('holdings')
      .select('id, symbol, name, quantity, coingecko_id, avg_buy_price, total_cost_basis, is_staked, staking_apy')
      .eq('user_id', userId)

    if (!holdings || holdings.length === 0) {
      await supabase.from('agent_runs').update({
        status: 'completed',
        completed_at: new Date().toISOString(),
        duration_ms: Date.now() - startTime,
        output: { message: 'No holdings to analyze', holdings_count: 0 }
      }).eq('id', runId)
      return
    }

    const holdingsWithPrices = await fetchPricesForHoldings(holdings as unknown as Holding[])
    
    const totalValue = holdingsWithPrices.reduce((sum, h) => sum + (h.current_value || 0), 0)
    
    const holdingsWithAllocation = holdingsWithPrices.map(h => ({
      ...h,
      allocation_percent: totalValue > 0 ? ((h.current_value || 0) / totalValue) * 100 : 0
    }))

    const metrics = calculatePortfolioMetrics(holdingsWithAllocation)
    
    const diagnosis = await generateDiagnosis(env, holdingsWithAllocation, metrics, config.language || 'zh')

    const today = new Date().toISOString().split('T')[0]
    
    await supabase.from('portfolio_diagnoses').upsert({
      user_id: userId,
      task_id: taskId,
      run_id: runId,
      diagnosis_date: today,
      overall_health_score: diagnosis.overall_score,
      diversification_score: metrics.diversification_score,
      risk_score: metrics.risk_score,
      performance_score: metrics.performance_score,
      summary: diagnosis.summary,
      strengths: diagnosis.strengths,
      weaknesses: diagnosis.weaknesses,
      recommendations: diagnosis.recommendations,
      sector_allocation: metrics.sector_allocation,
      correlation_analysis: metrics.correlation_analysis,
      risk_factors: metrics.risk_factors,
      performance_vs_benchmarks: metrics.performance_vs_benchmarks,
      full_report: diagnosis.full_report
    }, { onConflict: 'user_id,diagnosis_date' })

    await supabase.from('portfolio_snapshots').upsert({
      user_id: userId,
      snapshot_date: today,
      total_value_usd: totalValue,
      total_cost_basis_usd: holdingsWithAllocation.reduce((sum, h) => sum + (h.total_cost_basis || 0), 0),
      total_pnl_usd: holdingsWithAllocation.reduce((sum, h) => sum + (h.pnl || 0), 0),
      total_pnl_percent: metrics.total_pnl_percent,
      holdings_count: holdings.length,
      holdings_breakdown: holdingsWithAllocation.map(h => ({
        symbol: h.symbol,
        value: h.current_value,
        allocation: h.allocation_percent
      })),
      top_gainers: holdingsWithAllocation
        .filter(h => (h.pnl_percent || 0) > 0)
        .sort((a, b) => (b.pnl_percent || 0) - (a.pnl_percent || 0))
        .slice(0, 3)
        .map(h => ({ symbol: h.symbol, pnl_percent: h.pnl_percent })),
      top_losers: holdingsWithAllocation
        .filter(h => (h.pnl_percent || 0) < 0)
        .sort((a, b) => (a.pnl_percent || 0) - (b.pnl_percent || 0))
        .slice(0, 3)
        .map(h => ({ symbol: h.symbol, pnl_percent: h.pnl_percent })),
      concentration_metrics: {
        hhi: metrics.hhi,
        top3_concentration: metrics.top3_concentration
      }
    }, { onConflict: 'user_id,snapshot_date' })

    const notificationTitle = config.language === 'en' 
      ? '📊 Weekly Portfolio Diagnosis' 
      : '📊 每周持仓诊断报告'
    
    await supabase.from('notifications').insert({
      user_id: userId,
      type: 'portfolio_update',
      title: notificationTitle,
      body: diagnosis.summary,
      data: {
        overall_score: diagnosis.overall_score,
        total_value: totalValue,
        holdings_count: holdings.length,
        diagnosis_date: today
      },
      source_type: 'agent_task',
      source_id: taskId,
      priority: 'normal'
    })

    await sendPushToUser(env, userId, createNotificationPayload(
      'portfolio_update',
      notificationTitle,
      diagnosis.summary.slice(0, 100),
      { link: '/portfolio?tab=diagnosis' }
    ))

    await supabase.from('agent_runs').update({
      status: 'completed',
      completed_at: new Date().toISOString(),
      duration_ms: Date.now() - startTime,
      output: {
        holdings_count: holdings.length,
        total_value: totalValue,
        overall_score: diagnosis.overall_score
      },
      notification_sent: true
    }).eq('id', runId)

    await supabase.from('agent_tasks').update({
      last_run_at: new Date().toISOString()
    }).eq('id', taskId)

  } catch (error) {
    console.error(`[PortfolioDiagnosis] Error processing task ${taskId}:`, error)
    
    await supabase.from('agent_runs').update({
      status: 'failed',
      completed_at: new Date().toISOString(),
      duration_ms: Date.now() - startTime,
      error_message: error instanceof Error ? error.message : 'Unknown error',
      error_code: 'PROCESSING_ERROR'
    }).eq('id', runId)
  }
}

async function fetchPricesForHoldings(holdings: Holding[]): Promise<HoldingWithPrice[]> {
  const coingeckoIds = holdings
    .filter(h => h.coingecko_id)
    .map(h => h.coingecko_id)
    .join(',')

  let prices: Record<string, { usd: number }> = {}
  
  if (coingeckoIds) {
    try {
      const res = await fetch(
        `https://api.coingecko.com/api/v3/simple/price?ids=${coingeckoIds}&vs_currencies=usd`
      )
      if (res.ok) {
        prices = await res.json()
      }
    } catch (err) {
      console.error('[PortfolioDiagnosis] Failed to fetch prices:', err)
    }
  }

  return holdings.map(h => {
    const price = h.coingecko_id ? prices[h.coingecko_id]?.usd : null
    const currentValue = price ? Number(h.quantity) * price : null
    const costBasis = h.total_cost_basis ? Number(h.total_cost_basis) : null
    const pnl = currentValue && costBasis ? currentValue - costBasis : null
    const pnlPercent = pnl && costBasis && costBasis > 0 ? (pnl / costBasis) * 100 : null

    return {
      ...h,
      current_price: price,
      current_value: currentValue,
      pnl,
      pnl_percent: pnlPercent,
      allocation_percent: 0
    }
  })
}

interface PortfolioMetrics {
  diversification_score: number
  risk_score: number
  performance_score: number
  total_pnl_percent: number | null
  hhi: number
  top3_concentration: number
  sector_allocation: Record<string, number>
  correlation_analysis: Record<string, unknown>
  risk_factors: Array<{ factor: string; severity: string; description: string }>
  performance_vs_benchmarks: Record<string, unknown>
}

function calculatePortfolioMetrics(holdings: HoldingWithPrice[]): PortfolioMetrics {
  const allocations = holdings.map(h => h.allocation_percent / 100)
  const hhi = allocations.reduce((sum, a) => sum + a * a, 0) * 10000
  
  const sortedByAllocation = [...holdings].sort((a, b) => b.allocation_percent - a.allocation_percent)
  const top3Concentration = sortedByAllocation.slice(0, 3).reduce((sum, h) => sum + h.allocation_percent, 0)
  
  let diversificationScore = 100
  if (hhi > 5000) diversificationScore -= 40
  else if (hhi > 2500) diversificationScore -= 20
  else if (hhi > 1500) diversificationScore -= 10
  
  if (top3Concentration > 80) diversificationScore -= 30
  else if (top3Concentration > 60) diversificationScore -= 15
  
  if (holdings.length < 3) diversificationScore -= 20
  else if (holdings.length < 5) diversificationScore -= 10
  
  diversificationScore = Math.max(0, Math.min(100, diversificationScore))
  
  const riskFactors: Array<{ factor: string; severity: string; description: string }> = []
  
  if (top3Concentration > 70) {
    riskFactors.push({
      factor: 'concentration_risk',
      severity: 'high',
      description: 'Portfolio heavily concentrated in top 3 holdings'
    })
  }
  
  if (holdings.length < 5) {
    riskFactors.push({
      factor: 'low_diversification',
      severity: 'medium',
      description: 'Less than 5 holdings in portfolio'
    })
  }
  
  const stakedHoldings = holdings.filter(h => h.is_staked)
  if (stakedHoldings.length > 0) {
    const stakedValue = stakedHoldings.reduce((sum, h) => sum + (h.current_value || 0), 0)
    const totalValue = holdings.reduce((sum, h) => sum + (h.current_value || 0), 0)
    if (totalValue > 0 && (stakedValue / totalValue) > 0.5) {
      riskFactors.push({
        factor: 'liquidity_risk',
        severity: 'medium',
        description: 'More than 50% of portfolio is staked and may be illiquid'
      })
    }
  }
  
  const riskScore = Math.max(0, 100 - riskFactors.length * 20)
  
  const totalCostBasis = holdings.reduce((sum, h) => sum + (h.total_cost_basis || 0), 0)
  const totalPnl = holdings.reduce((sum, h) => sum + (h.pnl || 0), 0)
  const totalPnlPercent = totalCostBasis > 0 ? (totalPnl / totalCostBasis) * 100 : null
  
  let performanceScore = 50
  if (totalPnlPercent !== null) {
    if (totalPnlPercent > 100) performanceScore = 95
    else if (totalPnlPercent > 50) performanceScore = 85
    else if (totalPnlPercent > 20) performanceScore = 75
    else if (totalPnlPercent > 0) performanceScore = 60
    else if (totalPnlPercent > -20) performanceScore = 40
    else performanceScore = 25
  }
  
  return {
    diversification_score: diversificationScore,
    risk_score: riskScore,
    performance_score: performanceScore,
    total_pnl_percent: totalPnlPercent,
    hhi: Math.round(hhi),
    top3_concentration: Math.round(top3Concentration * 100) / 100,
    sector_allocation: {},
    correlation_analysis: {},
    risk_factors: riskFactors,
    performance_vs_benchmarks: {}
  }
}

interface DiagnosisResult {
  overall_score: number
  summary: string
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  full_report: string
}

async function generateDiagnosis(
  env: Env,
  holdings: HoldingWithPrice[],
  metrics: PortfolioMetrics,
  language: 'zh' | 'en'
): Promise<DiagnosisResult> {
  const overallScore = Math.round(
    (metrics.diversification_score * 0.3 + 
     metrics.risk_score * 0.3 + 
     metrics.performance_score * 0.4)
  )
  
  const holdingsSummary = holdings
    .sort((a, b) => (b.current_value || 0) - (a.current_value || 0))
    .slice(0, 10)
    .map(h => `${h.symbol}: ${h.allocation_percent.toFixed(1)}% (${h.pnl_percent ? (h.pnl_percent > 0 ? '+' : '') + h.pnl_percent.toFixed(1) + '%' : 'N/A'})`)
    .join('\n')
  
  const systemPrompt = language === 'zh'
    ? `你是一位专业的加密货币投资组合分析师。请根据用户的持仓数据生成诊断报告。

输出格式（JSON）：
{
  "summary": "一段话总结（50-100字）",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "recommendations": ["建议1", "建议2", "建议3"],
  "full_report": "详细分析报告（300-500字）"
}

要求：
- 分析多样化程度、风险水平、表现
- 给出具体可操作的建议
- 使用中文回复`
    : `You are a professional cryptocurrency portfolio analyst. Generate a diagnosis report based on the user's holdings.

Output format (JSON):
{
  "summary": "One paragraph summary (50-100 words)",
  "strengths": ["Strength 1", "Strength 2"],
  "weaknesses": ["Weakness 1", "Weakness 2"],
  "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
  "full_report": "Detailed analysis report (300-500 words)"
}

Requirements:
- Analyze diversification, risk level, performance
- Provide specific actionable recommendations
- Reply in English`

  const userPrompt = language === 'zh'
    ? `持仓概览：
${holdingsSummary}

指标：
- 多样化评分：${metrics.diversification_score}/100
- 风险评分：${metrics.risk_score}/100
- 表现评分：${metrics.performance_score}/100
- HHI指数：${metrics.hhi}
- 前3持仓占比：${metrics.top3_concentration}%
- 总收益率：${metrics.total_pnl_percent ? metrics.total_pnl_percent.toFixed(2) + '%' : '未知'}
- 风险因素：${metrics.risk_factors.map(r => r.factor).join(', ') || '无'}

请生成诊断报告。`
    : `Holdings Overview:
${holdingsSummary}

Metrics:
- Diversification Score: ${metrics.diversification_score}/100
- Risk Score: ${metrics.risk_score}/100
- Performance Score: ${metrics.performance_score}/100
- HHI Index: ${metrics.hhi}
- Top 3 Concentration: ${metrics.top3_concentration}%
- Total P&L: ${metrics.total_pnl_percent ? metrics.total_pnl_percent.toFixed(2) + '%' : 'Unknown'}
- Risk Factors: ${metrics.risk_factors.map(r => r.factor).join(', ') || 'None'}

Please generate the diagnosis report.`

  try {
    const openrouter = createOpenRouterClient(env)
    const response = await openrouter.request({
      model: 'deepseek/deepseek-chat',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0.3,
      max_tokens: 1000
    })

    const data = await response.json() as { choices: Array<{ message: { content: string } }> }
    const content = data.choices[0]?.message?.content || ''
    
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0])
      return {
        overall_score: overallScore,
        summary: parsed.summary || '',
        strengths: parsed.strengths || [],
        weaknesses: parsed.weaknesses || [],
        recommendations: parsed.recommendations || [],
        full_report: parsed.full_report || ''
      }
    }
    
    throw new Error('Failed to parse LLM response')
  } catch (error) {
    console.error('[PortfolioDiagnosis] LLM diagnosis failed:', error)
    
    const fallbackSummary = language === 'zh'
      ? `您的投资组合包含 ${holdings.length} 个持仓，整体健康评分为 ${overallScore}/100。`
      : `Your portfolio contains ${holdings.length} holdings with an overall health score of ${overallScore}/100.`
    
    return {
      overall_score: overallScore,
      summary: fallbackSummary,
      strengths: [],
      weaknesses: metrics.risk_factors.map(r => r.description),
      recommendations: [],
      full_report: ''
    }
  }
}
