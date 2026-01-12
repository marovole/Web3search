/**
 * Reporter Agent
 * Responsible for synthesizing all agent results into a comprehensive report
 */

import { BaseSubAgent } from './index'
import type { SharedContext, AgentInput, AgentResult, AggregatedResult, SourceCitation } from '../types'
import type { ISSEEmitter } from '../../../services/deep-research/types'
import type { Env } from '../../../types/env'
import type { ModelConfig } from '../../model-routing'


export class ReporterAgent extends BaseSubAgent {
  readonly id = 'reporter'
  readonly name = 'Reporter'
  readonly description = 'Report generation agent - synthesizes all agent results into a comprehensive report'
  readonly capabilities = [
    'result_synthesis',
    'summary_generation',
    'recommendation_creation',
    'citation_management',
    'report_formatting',
  ]
  readonly inputRequirements: string[] = []

  async execute(
    context: SharedContext,
    input: AgentInput,
    emitter?: ISSEEmitter
  ): Promise<AgentResult> {
    const startTime = Date.now()
    this.emitProgress(emitter, 'report', 'Reporter: Synthesizing all results into final report...')

    try {
      // Step 1: Collect all agent results
      const allResults = Array.from(context.agentResults.values())

      if (allResults.length === 0) {
        throw new Error('No agent results available to synthesize')
      }

      // Step 2: Extract citations from search results
      const citations = this.extractCitations(context.collectedData.searchResults)

      // Step 3: Synthesize key findings
      const keyFindings = this.synthesizeKeyFindings(allResults)

      // Step 4: Generate recommendations
      const recommendations = this.generateRecommendations(allResults)

      // Step 5: Generate summary
      const summary = this.generateSummary(context, allResults)

      // Step 6: Create structured sections
      const sections = this.createSections(context, allResults)

      // Step 7: Calculate confidence score
      const confidenceScore = this.calculateConfidenceScore(allResults)

      // Step 8: Format final output
      const aggregatedResult: AggregatedResult = {
        summary,
        sections,
        keyFindings,
        recommendations,
        citations,
        confidenceScore,
      }

      this.emitProgress(emitter, 'report', 'Reporter: Report generation complete')

      return {
        agentId: this.id,
        agentName: this.name,
        status: 'completed',
        output: aggregatedResult,
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

  private extractCitations(searchResults: Array<{
    id: string
    title: string
    url: string
    snippet: string
    relevanceScore: number
  }>): SourceCitation[] {
    // Select top sources by relevance
    const topResults = searchResults
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, 20)

    return topResults.map((result, index) => ({
      sourceId: result.id,
      title: result.title,
      url: result.url,
      snippet: result.snippet,
      relevanceScore: result.relevanceScore,
    }))
  }

  private synthesizeKeyFindings(allResults: Array<{ agentId: string; output: unknown }>): string[] {
    const findings: string[] = []

    // Extract findings from each agent
    allResults.forEach((result) => {
      switch (result.agentId) {
        case 'analyzer': {
          const report = result.output as { summary?: string; recommendations?: string[] }
          if (report.summary) {
            findings.push(`Analysis: ${report.summary}`)
          }
          break
        }
        case 'risk': {
          const report = result.output as { summary?: string; recommendations?: string[] }
          if (report.summary) {
            findings.push(`Risk Assessment: ${report.summary}`)
          }
          break
        }
        case 'news': {
          const report = result.output as { summary?: string; sentimentAnalysis?: { overallSentiment?: string } }
          if (report.sentimentAnalysis?.overallSentiment) {
            findings.push(`News Sentiment: ${report.sentimentAnalysis.overallSentiment}`)
          }
          break
        }
      }
    })

    // Deduplicate and limit
    return [...new Set(findings)].slice(0, 10)
  }

  private generateRecommendations(allResults: Array<{ agentId: string; output: unknown }>): string[] {
    const recommendations: string[] = []

    // Collect recommendations from each agent
    allResults.forEach((result) => {
      const output = result.output as { recommendations?: string[] }
      if (output.recommendations && Array.isArray(output.recommendations)) {
        recommendations.push(...output.recommendations)
      }
    })

    // Deduplicate and limit
    return [...new Set(recommendations)].slice(0, 8)
  }

  private generateSummary(context: SharedContext, allResults: Array<{ agentId: string; output: unknown }>): string {
    const parts: string[] = []

    parts.push(`Research completed for: "${context.originalQuery}"`)

    // Count sources
    const sourceCount = context.collectedData.searchResults.length
    const tokenCount = Object.keys(context.collectedData.priceData).length
    parts.push(`Analyzed ${sourceCount} sources${tokenCount > 0 ? ` across ${tokenCount} token(s)` : ''}.`)

    // Overall sentiment from news
    const newsResult = allResults.find((r) => r.agentId === 'news')
    if (newsResult) {
      const newsOutput = newsResult.output as { sentimentAnalysis?: { overallSentiment?: string } }
      if (newsOutput.sentimentAnalysis?.overallSentiment) {
        parts.push(`News sentiment: ${newsOutput.sentimentAnalysis.overallSentiment}.`)
      }
    }

    // Overall risk from risk agent
    const riskResult = allResults.find((r) => r.agentId === 'risk')
    if (riskResult) {
      const riskOutput = riskResult.output as { overallRiskLevel?: string }
      if (riskOutput.overallRiskLevel) {
        parts.push(`Risk level: ${riskOutput.overallRiskLevel}.`)
      }
    }

    return parts.join(' ')
  }

  private createSections(
    context: SharedContext,
    allResults: Array<{ agentId: string; output: unknown }>
  ): AggregatedResult['sections'] {
    const sections: AggregatedResult['sections'] = []

    // Executive Summary
    sections.push({
      title: 'Executive Summary',
      content: this.generateSummary(context, allResults),
      importance: 'high',
    })

    // Market Analysis Section
    const analyzerResult = allResults.find((r) => r.agentId === 'analyzer')
    if (analyzerResult) {
      const output = analyzerResult.output as {
        priceAnalysis?: Record<string, unknown>
        insightAnalysis?: Record<string, unknown>
        overallMetrics?: Record<string, unknown>
      }
      sections.push({
        title: 'Market Analysis',
        content: this.formatMarketAnalysis(output),
        agentSource: 'analyzer',
        importance: 'high',
      })
    }

    // Risk Assessment Section
    const riskResult = allResults.find((r) => r.agentId === 'risk')
    if (riskResult) {
      const output = riskResult.output as {
        overallRiskLevel?: string
        redFlags?: string[]
        tokenDetails?: Array<{ address: string; score: number; riskLevel: string; redFlags: string[] }>
        recommendations?: string[]
      }
      sections.push({
        title: 'Risk Assessment',
        content: this.formatRiskAssessment(output),
        agentSource: 'risk',
        importance: 'high',
      })
    }

    // News & Sentiment Section
    const newsResult = allResults.find((r) => r.agentId === 'news')
    if (newsResult) {
      const output = newsResult.output as {
        articleCount?: number
        sentimentAnalysis?: {
          overallSentiment?: string
          positiveCount?: number
          negativeCount?: number
          trendingTopics?: string[]
        }
        topHeadlines?: Array<{ title: string; source: string }>
      }
      sections.push({
        title: 'News & Sentiment',
        content: this.formatNewsAnalysis(output),
        agentSource: 'news',
        importance: 'medium',
      })
    }

    // Key Findings
    sections.push({
      title: 'Key Findings',
      content: this.formatKeyFindings(allResults),
      importance: 'high',
    })

    // Recommendations
    sections.push({
      title: 'Recommendations',
      content: this.formatRecommendations(allResults),
      importance: 'high',
    })

    return sections
  }

  private formatMarketAnalysis(output: Record<string, unknown> | undefined): string {
    if (!output) return 'No market analysis data available.'

    const parts: string[] = []

    const priceAnalysis = output.priceAnalysis as { averageChange24h?: number; overallTrend?: string } | undefined
    if (priceAnalysis) {
      parts.push(`**Price Overview**:`)
      parts.push(`- 24h Average Change: ${priceAnalysis.averageChange24h?.toFixed(2) || 'N/A'}%`)
      parts.push(`- Overall Trend: ${priceAnalysis.overallTrend || 'N/A'}`)
    }

    const overallMetrics = output.overallMetrics as { riskLevel?: string; confidenceScore?: number } | undefined
    if (overallMetrics) {
      parts.push(`**Metrics**:`)
      parts.push(`- Risk Level: ${overallMetrics.riskLevel || 'N/A'}`)
      parts.push(`- Confidence: ${overallMetrics.confidenceScore?.toFixed(0) || 'N/A'}%`)
    }

    return parts.join('\n')
  }

  private formatRiskAssessment(output: Record<string, unknown> | undefined): string {
    if (!output) return 'No risk assessment data available.'

    const parts: string[] = []

    const riskLevel = (output.overallRiskLevel as string) || 'unknown'
    parts.push(`**Overall Risk Level**: ${riskLevel.toUpperCase()}`)

    const redFlags = output.redFlags as string[] | undefined
    if (redFlags && redFlags.length > 0) {
      parts.push(`\n**Red Flags Detected**:`)
      redFlags.forEach((flag) => {
        parts.push(`- ${flag}`)
      })
    }

    const tokenDetails = output.tokenDetails as Array<{ address: string; score: number; riskLevel: string }> | undefined
    if (tokenDetails && tokenDetails.length > 0) {
      parts.push(`\n**Token Risk Breakdown**:`)
      tokenDetails.forEach((token) => {
        parts.push(`- ${token.address.slice(0, 6)}...${token.address.slice(-4)}: ${token.riskLevel.toUpperCase()} (Score: ${token.score})`)
      })
    }

    return parts.join('\n')
  }

  private formatNewsAnalysis(output: Record<string, unknown> | undefined): string {
    if (!output) return 'No news data available.'

    const parts: string[] = []

    const sentiment = output.sentimentAnalysis as { overallSentiment?: string; positiveCount?: number; negativeCount?: number; trendingTopics?: string[] } | undefined
    if (sentiment) {
      parts.push(`**Sentiment**: ${sentiment.overallSentiment || 'Unknown'}`)
      parts.push(`- Positive articles: ${sentiment.positiveCount || 0}`)
      parts.push(`- Negative articles: ${sentiment.negativeCount || 0}`)
      if (sentiment.trendingTopics && sentiment.trendingTopics.length > 0) {
        parts.push(`- Trending: ${sentiment.trendingTopics.join(', ')}`)
      }
    }

    const topHeadlines = output.topHeadlines as Array<{ title: string; source: string }> | undefined
    if (topHeadlines && topHeadlines.length > 0) {
      parts.push(`\n**Top Headlines**:`)
      topHeadlines.slice(0, 5).forEach((h, i) => {
        parts.push(`${i + 1}. ${h.title} (${h.source})`)
      })
    }

    return parts.join('\n')
  }

  private formatKeyFindings(allResults: Array<{ agentId: string; output: unknown }>): string {
    const findings: string[] = []

    allResults.forEach((result) => {
      const output = result.output as { insights?: string[] }
      if (output.insights && Array.isArray(output.insights)) {
        findings.push(...output.insights)
      }
    })

    if (findings.length === 0) {
      return 'No specific findings identified.'
    }

    return findings.map((f, i) => `${i + 1}. ${f}`).join('\n')
  }

  private formatRecommendations(allResults: Array<{ agentId: string; output: unknown }>): string {
    const recommendations: string[] = []

    allResults.forEach((result) => {
      const output = result.output as { recommendations?: string[] }
      if (output.recommendations && Array.isArray(output.recommendations)) {
        recommendations.push(...output.recommendations)
      }
    })

    if (recommendations.length === 0) {
      return 'No specific recommendations available.'
    }

    return recommendations.map((r, i) => `${i + 1}. ${r}`).join('\n')
  }

  private calculateConfidenceScore(allResults: Array<{ agentId: string; output: unknown }>): number {
    let score = 50 // Base score
    let factors = 0

    allResults.forEach((result) => {
      switch (result.agentId) {
        case 'researcher': {
          const output = result.output as { searchResultsCount?: number }
          if (output.searchResultsCount && output.searchResultsCount > 10) {
            score += 20
            factors++
          } else if (output.searchResultsCount && output.searchResultsCount > 0) {
            score += 10
            factors++
          }
          break
        }
        case 'analyzer': {
          factors++
          break
        }
        case 'risk': {
          const output = result.output as { totalTokensAnalyzed?: number }
          if (output.totalTokensAnalyzed && output.totalTokensAnalyzed > 0) {
            score += 15
            factors++
          }
          break
        }
        case 'news': {
          const output = result.output as { articleCount?: number }
          if (output.articleCount && output.articleCount > 10) {
            score += 15
            factors++
          } else if (output.articleCount && output.articleCount > 0) {
            score += 10
            factors++
          }
          break
        }
      }
    })

    // Normalize based on number of active agents
    const normalizedScore = factors > 0 ? Math.min(score, 95) : 30

    return normalizedScore
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
