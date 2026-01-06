/**
 * Deep Research Formatter Service
 * Handles query validation and result formatting
 */

import type { QueryValidationResult } from './types'

const MAX_RESEARCH_QUERY_LENGTH = 5000

/**
 * Prompt injection patterns to block
 */
const INJECTION_PATTERNS = [
  /ignore\s+previous\s+instructions/i,
  /system\s*:/i,
  /assistant\s*:/i,
  /\b(jailbreak|jail\s*break)\b/i,
  /\b(dan|do\s*anything\s*now)\b/i,
  /<script\b/i,
  /javascript:/i,
  /on\w+\s*=/i,
]

/**
 * Validate and sanitize research query input
 * Prevents injection attacks and ensures safe processing
 */
export function validateResearchQuery(input: string): QueryValidationResult {
  // Check for empty or invalid input
  if (!input || typeof input !== 'string') {
    return { valid: false, sanitized: '', error: 'Query is required' }
  }

  const trimmed = input.trim()

  // Check minimum length
  if (trimmed.length < 2) {
    return { valid: false, sanitized: '', error: 'Query must be at least 2 characters' }
  }

  // Check maximum length
  if (trimmed.length > MAX_RESEARCH_QUERY_LENGTH) {
    return {
      valid: false,
      sanitized: '',
      error: `Query exceeds maximum length of ${MAX_RESEARCH_QUERY_LENGTH} characters`,
    }
  }

  // Check for potential prompt injection patterns
  for (const pattern of INJECTION_PATTERNS) {
    if (pattern.test(trimmed)) {
      return { valid: false, sanitized: '', error: 'Query contains prohibited content' }
    }
  }

  // Sanitize the input (remove potential XSS vectors)
  const sanitized = trimmed
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+\s*=/gi, '')
    .replace(/data:/g, '')

  return { valid: true, sanitized }
}

/**
 * Format structured analysis result into readable markdown answer
 */
export function formatStructuredAnswer(parsed: {
  executive_summary?: string
  detailed_analysis?: {
    sections?: Array<{ title: string; content: string }>
  }
  key_findings?: Array<string | { finding: string; confidence?: number }>
  risks_and_uncertainties?: {
    limitations?: string[]
    uncertainties?: string[]
  }
  conclusion?: {
    summary?: string
    recommendations?: string[]
  }
}): string {
  const parts: string[] = []

  // Executive Summary
  if (parsed.executive_summary) {
    parts.push(`## 执行摘要\n${parsed.executive_summary}`)
  }

  // Detailed Analysis
  if (parsed.detailed_analysis?.sections) {
    parts.push('\n## 详细分析')
    for (const section of parsed.detailed_analysis.sections) {
      parts.push(`\n### ${section.title}\n${section.content}`)
    }
  }

  // Key Findings
  if (parsed.key_findings?.length) {
    parts.push('\n## 关键发现')
    for (const finding of parsed.key_findings) {
      const text = typeof finding === 'string' ? finding : finding.finding
      const confidence =
        typeof finding === 'object' && finding.confidence
          ? ` (置信度: ${(finding.confidence * 100).toFixed(0)}%)`
          : ''
      parts.push(`- ${text}${confidence}`)
    }
  }

  // Risks and Uncertainties
  if (parsed.risks_and_uncertainties) {
    const risks = parsed.risks_and_uncertainties
    if (risks.limitations?.length || risks.uncertainties?.length) {
      parts.push('\n## 风险与不确定性')
      if (risks.limitations?.length) {
        parts.push('**局限性:**')
        risks.limitations.forEach((l: string) => parts.push(`- ${l}`))
      }
      if (risks.uncertainties?.length) {
        parts.push('**不确定因素:**')
        risks.uncertainties.forEach((u: string) => parts.push(`- ${u}`))
      }
    }
  }

  // Conclusion
  if (parsed.conclusion) {
    parts.push('\n## 结论')
    if (parsed.conclusion.summary) {
      parts.push(parsed.conclusion.summary)
    }
    if (parsed.conclusion.recommendations?.length) {
      parts.push('\n**建议:**')
      parsed.conclusion.recommendations.forEach((r: string) => parts.push(`- ${r}`))
    }
  }

  return parts.join('\n')
}

/**
 * Format tokenomics audit result into readable markdown answer
 */
export function formatTokenomicsAnswer(parsed: {
  scorecard?: { score: number; rating: string; color: string }
  red_flags?: string[]
  analysis?: {
    supply_dynamics?: {
      circulating_supply?: string
      max_supply?: string
      fdv?: string
      inflation_rate?: string
      findings?: string
    }
    allocation?: {
      insider_percentage?: number
      centralization_risk?: string
      breakdown?: Record<string, number>
      findings?: string
    }
    vesting?: {
      tge_date?: string
      next_major_unlock?: string
      monthly_sell_pressure_usd?: string
      findings?: string
    }
    value_accrual?: {
      mechanism?: string
      yield_type?: string
      protocol_revenue?: string
      findings?: string
    }
    sustainability?: {
      death_spiral_risk?: string
      ponzi_score?: number
      findings?: string
    }
  }
  stress_test?: {
    treasury_runway?: string
    staking_impact?: string
    protocol_survival?: string
    findings?: string
  }
  verdict?: {
    recommendation?: string
    investment_horizon?: string
    key_catalysts?: string[]
    key_risks?: string[]
    summary?: string
  }
  data_quality?: {
    transparency_score?: number
    missing_data?: string[]
    conflicting_sources?: string[]
  }
}): string {
  const parts: string[] = []

  // Scorecard Header
  if (parsed.scorecard) {
    const { score, rating, color } = parsed.scorecard
    const emoji = color === 'green' ? '🟢' : color === 'yellow' ? '🟡' : '🔴'
    parts.push(`## ${emoji} Tokenomics Scorecard: ${score}/100 (${rating})`)
  }

  // Red Flags
  if (parsed.red_flags?.length) {
    parts.push('\n## 🚨 Red Flags')
    for (const flag of parsed.red_flags) {
      parts.push(`- ${flag}`)
    }
  }

  // 5-Dimension Analysis
  if (parsed.analysis) {
    const { supply_dynamics, allocation, vesting, value_accrual, sustainability } = parsed.analysis

    parts.push('\n## 📊 5-Dimension Audit')

    if (supply_dynamics) {
      parts.push('\n### 1. Supply Dynamics & FDV')
      if (supply_dynamics.circulating_supply)
        parts.push(`- 流通供应量: ${supply_dynamics.circulating_supply}`)
      if (supply_dynamics.max_supply) parts.push(`- 最大供应量: ${supply_dynamics.max_supply}`)
      if (supply_dynamics.fdv) parts.push(`- FDV: ${supply_dynamics.fdv}`)
      if (supply_dynamics.inflation_rate) parts.push(`- 通胀率: ${supply_dynamics.inflation_rate}`)
      if (supply_dynamics.findings) parts.push(`\n${supply_dynamics.findings}`)
    }

    if (allocation) {
      parts.push('\n### 2. Token Allocation & Centralization')
      if (allocation.insider_percentage !== undefined)
        parts.push(`- 内部人持仓: ${allocation.insider_percentage}%`)
      if (allocation.centralization_risk)
        parts.push(`- 中心化风险: ${allocation.centralization_risk}`)
      if (allocation.breakdown) {
        parts.push('- 分配明细:')
        for (const [key, value] of Object.entries(allocation.breakdown)) {
          parts.push(`  - ${key}: ${value}%`)
        }
      }
      if (allocation.findings) parts.push(`\n${allocation.findings}`)
    }

    if (vesting) {
      parts.push('\n### 3. Vesting & Unlock Schedule')
      if (vesting.tge_date) parts.push(`- TGE日期: ${vesting.tge_date}`)
      if (vesting.next_major_unlock) parts.push(`- 下次重大解锁: ${vesting.next_major_unlock}`)
      if (vesting.monthly_sell_pressure_usd)
        parts.push(`- 月度抛压: ${vesting.monthly_sell_pressure_usd}`)
      if (vesting.findings) parts.push(`\n${vesting.findings}`)
    }

    if (value_accrual) {
      parts.push('\n### 4. Value Accrual')
      if (value_accrual.mechanism) parts.push(`- 价值捕获机制: ${value_accrual.mechanism}`)
      if (value_accrual.yield_type) parts.push(`- 收益类型: ${value_accrual.yield_type}`)
      if (value_accrual.protocol_revenue)
        parts.push(`- 协议收入: ${value_accrual.protocol_revenue}`)
      if (value_accrual.findings) parts.push(`\n${value_accrual.findings}`)
    }

    if (sustainability) {
      parts.push('\n### 5. Sustainability & Ponzi Check')
      if (sustainability.death_spiral_risk)
        parts.push(`- 死亡螺旋风险: ${sustainability.death_spiral_risk}`)
      if (sustainability.ponzi_score !== undefined)
        parts.push(`- Ponzi评分: ${sustainability.ponzi_score}/10`)
      if (sustainability.findings) parts.push(`\n${sustainability.findings}`)
    }
  }

  // Stress Test
  if (parsed.stress_test) {
    parts.push('\n## 🔥 Stress Test: 50% Market Crash')
    if (parsed.stress_test.treasury_runway)
      parts.push(`- Treasury Runway: ${parsed.stress_test.treasury_runway}`)
    if (parsed.stress_test.staking_impact)
      parts.push(`- Staking Impact: ${parsed.stress_test.staking_impact}`)
    if (parsed.stress_test.protocol_survival)
      parts.push(`- Protocol Survival: ${parsed.stress_test.protocol_survival}`)
    if (parsed.stress_test.findings) parts.push(`\n${parsed.stress_test.findings}`)
  }

  // Verdict
  if (parsed.verdict) {
    parts.push('\n## 📋 Investment Verdict')
    if (parsed.verdict.recommendation)
      parts.push(`**Recommendation:** ${parsed.verdict.recommendation}`)
    if (parsed.verdict.investment_horizon)
      parts.push(`**Horizon:** ${parsed.verdict.investment_horizon}`)
    if (parsed.verdict.key_catalysts?.length) {
      parts.push('\n**Positive Catalysts:**')
      parsed.verdict.key_catalysts.forEach((c: string) => parts.push(`- ${c}`))
    }
    if (parsed.verdict.key_risks?.length) {
      parts.push('\n**Key Risks:**')
      parsed.verdict.key_risks.forEach((r: string) => parts.push(`- ${r}`))
    }
    if (parsed.verdict.summary) parts.push(`\n${parsed.verdict.summary}`)
  }

  // Data Quality
  if (parsed.data_quality) {
    parts.push('\n## 📝 Data Quality Assessment')
    if (parsed.data_quality.transparency_score !== undefined) {
      parts.push(`- Transparency Score: ${parsed.data_quality.transparency_score}/10`)
    }
    if (parsed.data_quality.missing_data?.length) {
      parts.push('- Missing Data:')
      parsed.data_quality.missing_data.forEach((d: string) => parts.push(`  - ${d}`))
    }
    if (parsed.data_quality.conflicting_sources?.length) {
      parts.push('- Conflicting Sources:')
      parsed.data_quality.conflicting_sources.forEach((c: string) => parts.push(`  - ${c}`))
    }
  }

  return parts.join('\n')
}
