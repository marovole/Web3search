/**
 * Analyzer Agent
 * Responsible for analyzing collected data - trends, patterns, metrics
 */

import { BaseSubAgent } from './index'
import type { SharedContext, AgentInput, AgentResult, PriceDataMap, RiskAssessment } from '../types'
import type { ISSEEmitter } from '../../../services/deep-research/types'
import type { Env } from '../../../types/env'
import type { ModelConfig } from '../../model-routing'


export class AnalyzerAgent extends BaseSubAgent {
  readonly id = 'analyzer'
  readonly name = 'Analyzer'
  readonly description = 'Data analysis agent - identifies trends, patterns, and insights'
  readonly capabilities = [
    'trend_analysis',
    'pattern_recognition',
    'metric_calculation',
    'correlation_analysis',
  ]
  readonly inputRequirements: string[] = []

  async execute(
    context: SharedContext,
    input: AgentInput,
    emitter?: ISSEEmitter
  ): Promise<AgentResult> {
    const startTime = Date.now()
    this.emitProgress(emitter, 'analysis', 'Analyzer: Analyzing collected data...')

    try {
      // Step 1: Analyze price data
      const priceAnalysis = this.analyzePriceData(context.collectedData.priceData)

      // Step 2: Analyze search results for insights
      const insightAnalysis = this.analyzeInsights(context.collectedData.searchResults)

      // Step 3: Calculate overall metrics
      const overallMetrics = this.calculateOverallMetrics(priceAnalysis, insightAnalysis)

      // Step 4: Generate analysis report
      const analysisReport = this.generateAnalysisReport(
        priceAnalysis,
        insightAnalysis,
        overallMetrics
      )

      this.emitProgress(emitter, 'analysis', 'Analyzer: Analysis complete')

      return {
        agentId: this.id,
        agentName: this.name,
        status: 'completed',
        output: analysisReport,
        metrics: {
          tokensUsed: 0,
          duration: this.getDuration(startTime),
          sourcesProcessed: context.collectedData.searchResults.length,
        },
      }
    } catch (error) {
      return this.createErrorResult(error, startTime)
    }
  }

  private analyzePriceData(priceData: PriceDataMap): PriceAnalysis {
    const tokens = Object.values(priceData)
    const analysis: PriceAnalysis = {
      tokens: tokens,
      topGainers: [],
      topLosers: [],
      marketSentiment: 'neutral',
      overallTrend: 'sideways',
      averageChange24h: 0,
    }

    if (tokens.length === 0) return analysis

    // Calculate average change
    const changes = tokens.map((t) => t.priceChange24h)
    analysis.averageChange24h = changes.reduce((a, b) => a + b, 0) / changes.length

    // Identify top gainers and losers
    const sorted = [...tokens].sort((a, b) => b.priceChange24h - a.priceChange24h)
    analysis.topGainers = sorted.slice(0, 3)
    analysis.topLosers = sorted.slice(-3).reverse()

    // Determine market sentiment
    if (analysis.averageChange24h > 5) {
      analysis.marketSentiment = 'bullish'
    } else if (analysis.averageChange24h < -5) {
      analysis.marketSentiment = 'bearish'
    }

    // Determine overall trend
    if (analysis.averageChange24h > 3) {
      analysis.overallTrend = 'uptrend'
    } else if (analysis.averageChange24h < -3) {
      analysis.overallTrend = 'downtrend'
    }

    return analysis
  }

  private analyzeInsights(searchResults: Array<{ title: string; snippet: string; relevanceScore: number }>): InsightAnalysis {
    const insights: string[] = []
    const themes = new Map<string, number>()
    const sentimentKeywords = {
      positive: ['bullish', 'growth', 'surge', 'rally', 'breakthrough', 'adoption', 'partnership'],
      negative: ['scam', 'hack', 'exploit', 'crash', 'dump', 'rug', 'fraud', 'warning'],
    }

    let positiveCount = 0
    let negativeCount = 0

    searchResults.slice(0, 20).forEach((result) => {
      const text = `${result.title} ${result.snippet}`.toLowerCase()

      // Count sentiment
      sentimentKeywords.positive.forEach((word) => {
        if (text.includes(word)) positiveCount++
      })
      sentimentKeywords.negative.forEach((word) => {
        if (text.includes(word)) negativeCount++
      })

      // Extract themes
      const themeKeywords = ['defi', 'nft', 'gaming', 'metaverse', 'dao', 'staking', 'yield', 'layer2']
      themeKeywords.forEach((theme) => {
        if (text.includes(theme)) {
          themes.set(theme, (themes.get(theme) || 0) + 1)
        }
      })
    })

    // Generate insights
    if (positiveCount > negativeCount) {
      insights.push('Market sentiment appears positive based on recent coverage')
    } else if (negativeCount > positiveCount) {
      insights.push('Recent coverage shows caution or negative sentiment')
    }

    // Top themes
    const topThemes = [...themes.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3)
    if (topThemes.length > 0) {
      insights.push(`Dominant themes: ${topThemes.map(([t]) => t).join(', ')}`)
    }

    return {
      insights,
      themes: Object.fromEntries(topThemes),
      sentimentBreakdown: {
        positive: positiveCount,
        negative: negativeCount,
        neutral: searchResults.length - positiveCount - negativeCount,
      },
      confidenceScore: Math.min(searchResults.length / 20, 1) * 100,
    }
  }

  private calculateOverallMetrics(
    priceAnalysis: PriceAnalysis,
    insightAnalysis: InsightAnalysis
  ): OverallMetrics {
    let score = 50 // Base score

    // Adjust based on price action
    score += Math.min(priceAnalysis.averageChange24h, 20)
    score += Math.min(insightAnalysis.sentimentBreakdown.positive * 2, 20)
    score -= Math.min(insightAnalysis.sentimentBreakdown.negative * 3, 30)

    return {
      overallScore: Math.max(0, Math.min(100, score)),
      momentumScore: priceAnalysis.averageChange24h > 0 ? 60 + priceAnalysis.averageChange24h : 40 + priceAnalysis.averageChange24h,
      sentimentScore: insightAnalysis.sentimentBreakdown,
      confidenceScore: insightAnalysis.confidenceScore,
      riskLevel: score < 30 ? 'high' : score < 60 ? 'medium' : 'low',
    }
  }

  private generateAnalysisReport(
    priceAnalysis: PriceAnalysis,
    insightAnalysis: InsightAnalysis,
    overallMetrics: OverallMetrics
  ): AnalysisReport {
    return {
      priceAnalysis,
      insightAnalysis,
      overallMetrics,
      summary: this.generateSummary(priceAnalysis, insightAnalysis),
      recommendations: this.generateRecommendations(overallMetrics),
    }
  }

  private generateSummary(priceAnalysis: PriceAnalysis, insightAnalysis: InsightAnalysis): string {
    const parts: string[] = []

    parts.push(`Analyzed ${insightAnalysis.sentimentBreakdown.positive + insightAnalysis.sentimentBreakdown.negative + insightAnalysis.sentimentBreakdown.neutral} sources.`)

    if (priceAnalysis.tokens.length > 0) {
      parts.push(`Price analysis shows ${priceAnalysis.overallTrend} with average 24h change of ${priceAnalysis.averageChange24h.toFixed(2)}%.`)
    }

    parts.push(`Sentiment: ${insightAnalysis.sentimentBreakdown.positive > insightAnalysis.sentimentBreakdown.negative ? 'Positive' : 'Cautious'} (${insightAnalysis.sentimentBreakdown.positive} positive, ${insightAnalysis.sentimentBreakdown.negative} negative mentions).`)

    return parts.join(' ')
  }

  private generateRecommendations(metrics: OverallMetrics): string[] {
    const recommendations: string[] = []

    if (metrics.riskLevel === 'high') {
      recommendations.push('Consider reducing exposure given elevated risk indicators')
    }
    if (metrics.momentumScore > 70) {
      recommendations.push('Strong momentum observed - may indicate continued trend')
    }
    if (metrics.momentumScore < 30) {
      recommendations.push('Weak momentum - consider waiting for clearer signals')
    }
    if (metrics.confidenceScore < 50) {
      recommendations.push('Limited data available - seek additional sources before making decisions')
    }

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
// Analysis Types (internal)
// ============================================================================

interface PriceAnalysis {
  tokens: PriceDataMap[string][]
  topGainers: PriceDataMap[string][]
  topLosers: PriceDataMap[string][]
  marketSentiment: 'bullish' | 'bearish' | 'neutral'
  overallTrend: 'uptrend' | 'downtrend' | 'sideways'
  averageChange24h: number
}

interface InsightAnalysis {
  insights: string[]
  themes: Record<string, number>
  sentimentBreakdown: {
    positive: number
    negative: number
    neutral: number
  }
  confidenceScore: number
}

interface OverallMetrics {
  overallScore: number
  momentumScore: number
  sentimentScore: InsightAnalysis['sentimentBreakdown']
  confidenceScore: number
  riskLevel: 'high' | 'medium' | 'low'
}

interface AnalysisReport {
  priceAnalysis: PriceAnalysis
  insightAnalysis: InsightAnalysis
  overallMetrics: OverallMetrics
  summary: string
  recommendations: string[]
}
