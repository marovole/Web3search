/**
 * Risk Agent
 * Responsible for assessing risk factors - security, scam probability, liquidity
 */

import { BaseSubAgent } from './index'
import type { SharedContext, AgentInput, AgentResult, RiskAssessment, RiskMetricMap } from '../types'
import type { ISSEEmitter } from '../../../services/deep-research/types'
import type { Env } from '../../../types/env'
import type { ModelConfig } from '../../model-routing'


export class RiskAgent extends BaseSubAgent {
  readonly id = 'risk'
  readonly name = 'RiskAgent'
  readonly description = 'Risk assessment agent - evaluates security, scam probability, and liquidity risks'
  readonly capabilities = [
    'scam_detection',
    'liquidity_analysis',
    'holder_distribution_analysis',
    'audit_status_check',
    'contract_risk_evaluation',
  ]
  readonly inputRequirements: string[] = []

  async execute(
    context: SharedContext,
    input: AgentInput,
    emitter?: ISSEEmitter
  ): Promise<AgentResult> {
    const startTime = Date.now()
    this.emitProgress(emitter, 'risk', 'RiskAgent: Assessing risk factors...')

    try {
      const riskMetrics: RiskMetricMap = {}

      // Analyze each token's risk profile
      const tokens = Object.keys(context.collectedData.priceData)

      for (const tokenAddress of tokens) {
        const assessment = await this.assessTokenRisk(tokenAddress, context, emitter)
        riskMetrics[tokenAddress] = assessment
      }

      // If no price data, try to extract token from query
      if (tokens.length === 0) {
        const extractedToken = this.extractTokenFromQuery(input.query)
        if (extractedToken) {
          const assessment = await this.assessTokenRisk(extractedToken, context, emitter)
          riskMetrics[extractedToken] = assessment
        }
      }

      // Generate overall risk report
      const riskReport = this.generateRiskReport(riskMetrics)

      // Update context
      context.collectedData.riskMetrics = riskMetrics

      this.emitProgress(emitter, 'risk', `RiskAgent: Complete - analyzed ${Object.keys(riskMetrics).length} tokens`)

      return {
        agentId: this.id,
        agentName: this.name,
        status: 'completed',
        output: riskReport,
        metrics: {
          tokensUsed: 0,
          duration: this.getDuration(startTime),
          sourcesProcessed: Object.keys(riskMetrics).length,
        },
      }
    } catch (error) {
      return this.createErrorResult(error, startTime)
    }
  }

  private async assessTokenRisk(
    tokenAddress: string,
    context: SharedContext,
    emitter?: ISSEEmitter
  ): Promise<RiskAssessment> {
    const assessment: RiskAssessment = {
      overallScore: 50, // Start neutral
      scamProbability: 0,
      liquidityRisk: 50,
      concentrationRisk: 50,
      contractRisk: 50,
      redFlags: [],
      auditStatus: 'unknown',
    }

    // Check GoPlus security API
    try {
      const goplusResponse = await fetch(
        `https://api.gopluslabs.io/api/v2/security_audit/${tokenAddress}?chain_id=1`,
        {
          headers: { Accept: 'application/json' },
        }
      )

      if (goplusResponse.ok) {
        const data = await goplusResponse.json() as { result?: { security?: Record<string, string> } }
        const security = data.result?.security || {}

        if (security.is_honeypot === 'yes') {
          assessment.redFlags.push('Honeypot detected')
          assessment.scamProbability += 40
        }
        if (security.is_open_source === 'no') {
          assessment.redFlags.push('Contract not verified')
          assessment.contractRisk += 30
        }
        if (security.owner_change_balance === 'yes') {
          assessment.redFlags.push('Owner can modify balance')
          assessment.scamProbability += 20
        }
        if (security.trading_cooldown === 'yes') {
          assessment.redFlags.push('Trading cooldown detected')
          assessment.scamProbability += 15
        }
        if (security.slippage_modifiable === 'yes') {
          assessment.redFlags.push('Slippage can be modified')
          assessment.scamProbability += 15
        }
      }
    } catch (error) {
      console.warn(`GoPlus API call failed for ${tokenAddress}:`, error)
    }

    // Check DexScreener for liquidity
    try {
      const dexResponse = await fetch(
        `https://api.dexscreener.com/latest/dex/tokens/${tokenAddress}`
      )

      if (dexResponse.ok) {
        const data = await dexResponse.json() as { pairs?: Array<{ liquidity?: { usd?: number }; fdv?: number }> }
        const pairs = data.pairs?.[0]

        if (pairs) {
          const liquidityUsd = pairs.liquidity?.usd || 0

          if (liquidityUsd < 10000) {
            assessment.liquidityRisk = 90
            assessment.redFlags.push('Very low liquidity (<$10K)')
          } else if (liquidityUsd < 50000) {
            assessment.liquidityRisk = 70
          } else if (liquidityUsd < 100000) {
            assessment.liquidityRisk = 50
          } else {
            assessment.liquidityRisk = 30
          }

          // Check FDV vs liquidity ratio
          const fdv = pairs.fdv || 0
          if (fdv > 0 && liquidityUsd > 0) {
            const ratio = fdv / liquidityUsd
            if (ratio > 100) {
              assessment.redFlags.push('High FDV to liquidity ratio')
              assessment.liquidityRisk += 20
            }
          }
        }
      }
    } catch (error) {
      console.warn(`DexScreener API call failed for ${tokenAddress}:`, error)
    }

    // Check for holder concentration (simulated)
    const priceData = context.collectedData.priceData[tokenAddress]
    if (priceData && priceData.marketCap > 0) {
      // In a real implementation, this would call an API for holder data
      assessment.holderDistribution = {
        top10HolderPercent: 30, // Placeholder
        totalHolders: 1000, // Placeholder
        deployerBalancePercent: 5, // Placeholder
      }
    }

    // Calculate overall score
    assessment.overallScore = Math.min(
      Math.max(
        (assessment.scamProbability * 0.4) +
        (assessment.liquidityRisk * 0.25) +
        (assessment.concentrationRisk * 0.2) +
        (assessment.contractRisk * 0.15),
        0
      ),
      100
    )

    // Determine audit status
    if (assessment.redFlags.length === 0) {
      assessment.auditStatus = 'verified'
    } else if (assessment.redFlags.some((f) => f.includes('honeypot') || f.includes('scam'))) {
      assessment.auditStatus = 'failed'
    } else {
      assessment.auditStatus = 'pending'
    }

    return assessment
  }

  private extractTokenFromQuery(query: string): string | null {
    // Try to extract token address or symbol
    const addressPattern = /\b0x[a-fA-F0-9]{40}\b/
    const match = query.match(addressPattern)
    return match ? match[0] : null
  }

  private generateRiskReport(riskMetrics: RiskMetricMap): RiskReport {
    const tokens = Object.entries(riskMetrics)

    if (tokens.length === 0) {
      return {
        overallRiskLevel: 'unknown',
        totalTokensAnalyzed: 0,
        redFlags: [],
        summary: 'No tokens could be identified for risk analysis',
        recommendations: ['Unable to assess risk - please provide a token contract address'],
      }
    }

    const allRedFlags = tokens.flatMap(([, assessment]) => assessment.redFlags)
    const avgScore = tokens.reduce((sum, [, a]) => sum + a.overallScore, 0) / tokens.length

    let overallRiskLevel: 'low' | 'medium' | 'high' | 'critical'
    if (avgScore < 30) overallRiskLevel = 'low'
    else if (avgScore < 50) overallRiskLevel = 'medium'
    else if (avgScore < 70) overallRiskLevel = 'high'
    else overallRiskLevel = 'critical'

    return {
      overallRiskLevel,
      totalTokensAnalyzed: tokens.length,
      redFlags: [...new Set(allRedFlags)], // Deduplicate
      tokenDetails: tokens.map(([address, a]) => ({
        address,
        score: a.overallScore,
        riskLevel: a.overallScore < 30 ? 'low' : a.overallScore < 50 ? 'medium' : a.overallScore < 70 ? 'high' : 'critical',
        redFlags: a.redFlags,
      })),
      summary: this.generateRiskSummary(riskMetrics, overallRiskLevel),
      recommendations: this.generateRiskRecommendations(riskMetrics, overallRiskLevel),
    }
  }

  private generateRiskSummary(riskMetrics: RiskMetricMap, level: string): string {
    const tokenCount = Object.keys(riskMetrics).length
    const highRiskCount = Object.values(riskMetrics).filter((a) => a.overallScore >= 50).length

    if (level === 'low') {
      return `Low risk profile detected across ${tokenCount} token(s). No major red flags identified.`
    }
    if (level === 'medium') {
      return `Medium risk detected in ${highRiskCount} of ${tokenCount} token(s). Some caution advised.`
    }
    return `Elevated risk detected - ${highRiskCount} of ${tokenCount} token(s) show concerning indicators.`
  }

  private generateRiskRecommendations(riskMetrics: RiskMetricMap, level: string): string[] {
    const recommendations: string[] = []

    if (level === 'critical') {
      recommendations.push('Avoid investment until thorough due diligence is completed')
      recommendations.push('Consider consulting with a security expert')
    }
    if (level === 'high') {
      recommendations.push('Start with a small position if proceeding')
      recommendations.push('Set strict stop-loss levels')
    }

    Object.entries(riskMetrics).forEach(([address, assessment]) => {
      if (assessment.redFlags.includes('Very low liquidity')) {
        recommendations.push(`Token ${address.slice(0, 6)}...${address.slice(-4)}: Beware of slippage and difficulty exiting positions`)
      }
      if (assessment.redFlags.includes('Contract not verified')) {
        recommendations.push(`Token ${address.slice(0, 6)}...${address.slice(-4)}: Cannot verify contract safety`)
      }
      if (assessment.redFlags.includes('Honeypot detected')) {
        recommendations.push(`Token ${address.slice(0, 6)}...${address.slice(-4)}: HIGH RISK - Honeypot detected`)
      }
    })

    return recommendations
  }

  private createErrorResult(error: unknown, startTime: number): AgentResult {
    return {
      agentId: this.id,
      agentName: this.name,
      status: 'failed',
      output: null,
      metrics: {
        tokensUsed: 0,
        duration: this.getDuration(startTime),
        sourcesProcessed: 0,
      },
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// ============================================================================
// Risk Report Types
// ============================================================================

interface RiskReport {
  overallRiskLevel: 'low' | 'medium' | 'high' | 'critical' | 'unknown'
  totalTokensAnalyzed: number
  redFlags: string[]
  tokenDetails?: Array<{
    address: string
    score: number
    riskLevel: 'low' | 'medium' | 'high' | 'critical'
    redFlags: string[]
  }>
  summary: string
  recommendations: string[]
}
