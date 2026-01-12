/**
 * Result Aggregator
 * Aggregates and normalizes results from multiple agents
 */

import type { AgentResult, AggregatedResult, ResultSection, SourceCitation } from '../types'

export interface AggregationOptions {
  includeAllSections?: boolean
  confidenceThreshold?: number
  maxRecommendations?: number
  maxKeyFindings?: number
}

export class ResultAggregator {
  /**
   * Aggregate all agent results into a final result
   */
  aggregate(results: AgentResult[], options: AggregationOptions = {}): AggregatedResult {
    const {
      includeAllSections = false,
      confidenceThreshold = 0,
      maxRecommendations = 5,
      maxKeyFindings = 5,
    } = options

    // Filter failed results
    const successfulResults = results.filter((r) => r.status === 'completed')
    const failedResults = results.filter((r) => r.status !== 'completed')

    // Generate summary
    const summary = this.generateSummary(successfulResults, failedResults)

    // Generate sections
    const sections = this.generateSections(results, includeAllSections)

    // Extract key findings
    const keyFindings = this.extractKeyFindings(successfulResults, maxKeyFindings)

    // Generate recommendations
    const recommendations = this.generateRecommendations(successfulResults, maxRecommendations)

    // Collect citations
    const citations = this.collectCitations(successfulResults)

    // Calculate confidence score
    const confidenceScore = this.calculateConfidenceScore(successfulResults, failedResults, confidenceThreshold)

    return {
      summary,
      sections,
      keyFindings,
      recommendations,
      citations,
      confidenceScore,
    }
  }

  /**
   * Generate executive summary
   */
  private generateSummary(successful: AgentResult[], failed: AgentResult[]): string {
    const parts: string[] = []

    parts.push(`Analysis completed using ${successful.length} of ${successful.length + failed.length} agents.`)

    // Summarize by agent type
    const agentSummary = successful.map((r) => {
      switch (r.agentId) {
        case 'researcher':
          const researchOutput = r.output as { searchResultsCount?: number }
          return `Research: ${researchOutput?.searchResultsCount || 0} sources analyzed`
        case 'analyzer':
          return 'Analysis: Market trends and insights identified'
        case 'risk':
          const riskOutput = r.output as { overallRiskLevel?: string }
          return `Risk: ${riskOutput?.overallRiskLevel || 'Unknown'} level`
        case 'news':
          const newsOutput = r.output as { articleCount?: number }
          return `News: ${newsOutput?.articleCount || 0} articles analyzed`
        case 'reporter':
          return 'Report: Comprehensive synthesis generated'
        default:
          return `${r.agentName}: Completed`
      }
    })

    parts.push(agentSummary.join('. ') + '.')

    if (failed.length > 0) {
      const failedNames = failed.map((r) => r.agentName).join(', ')
      parts.push(`Note: ${failedNames} could not complete their analysis.`)
    }

    return parts.join(' ')
  }

  /**
   * Generate result sections
   */
  private generateSections(results: AgentResult[], includeAll: boolean): ResultSection[] {
    const sections: ResultSection[] = []

    // Process each agent's output
    for (const result of results) {
      if (result.status !== 'completed') continue

      const output = result.output as Record<string, unknown>

      switch (result.agentId) {
        case 'researcher': {
          const searchResultsCount = (output.searchResultsCount as number) || 0
          sections.push({
            title: 'Research Findings',
            content: `Collected and analyzed ${searchResultsCount} sources from web search and price data.`,
            agentSource: 'researcher',
            importance: 'high',
          })
          break
        }

        case 'analyzer': {
          const overallMetrics = output.overallMetrics as { overallScore?: number; riskLevel?: string } | undefined
          sections.push({
            title: 'Market Analysis',
            content: overallMetrics
              ? `Overall score: ${overallMetrics.overallScore}/100. Risk level: ${overallMetrics.riskLevel}.`
              : 'Market analysis completed.',
            agentSource: 'analyzer',
            importance: 'high',
          })
          break
        }

        case 'risk': {
          const riskLevel = (output.overallRiskLevel as string) || 'unknown'
          const redFlags = (output.redFlags as string[]) || []
          sections.push({
            title: 'Risk Assessment',
            content: `Risk level: ${riskLevel.toUpperCase()}.${redFlags.length > 0 ? ` Red flags: ${redFlags.join(', ')}.` : ''}`,
            agentSource: 'risk',
            importance: 'high',
          })
          break
        }

        case 'news': {
          const sentiment = (output.sentimentAnalysis as { overallSentiment?: string })?.overallSentiment
          sections.push({
            title: 'News & Sentiment',
            content: sentiment
              ? `Overall market sentiment: ${sentiment}.`
              : 'News analysis completed.',
            agentSource: 'news',
            importance: 'medium',
          })
          break
        }

        case 'reporter': {
          // Reporter output is the aggregated result itself, skip
          break
        }
      }
    }

    return sections
  }

  /**
   * Extract key findings from results
   */
  private extractKeyFindings(results: AgentResult[], max: number): string[] {
    const findings: string[] = []

    for (const result of results) {
      const output = result.output as { insights?: string[]; summary?: string; keyFindings?: string[] }

      if (output.insights && Array.isArray(output.insights)) {
        findings.push(...output.insights.slice(0, 3))
      }

      if (output.keyFindings && Array.isArray(output.keyFindings)) {
        findings.push(...output.keyFindings.slice(0, 2))
      }
    }

    // Deduplicate and limit
    return [...new Set(findings)].slice(0, max)
  }

  /**
   * Generate recommendations from results
   */
  private generateRecommendations(results: AgentResult[], max: number): string[] {
    const recommendations: string[] = []

    for (const result of results) {
      const output = result.output as { recommendations?: string[] }

      if (output.recommendations && Array.isArray(output.recommendations)) {
        recommendations.push(...output.recommendations)
      }
    }

    // Deduplicate and limit
    return [...new Set(recommendations)].slice(0, max)
  }

  /**
   * Collect citations from search results
   */
  private collectCitations(results: AgentResult[]): SourceCitation[] {
    const citations: SourceCitation[] = []

    for (const result of results) {
      if (result.agentId === 'researcher') {
        const output = result.output as { analyzedData?: { topResults?: Array<{ title: string; url: string; snippet: string }> } }

        if (output.analyzedData?.topResults) {
          output.analyzedData.topResults.forEach((item, index) => {
            citations.push({
              sourceId: `citation_${index}`,
              title: item.title,
              url: item.url,
              snippet: item.snippet,
              relevanceScore: 1 - index * 0.1, // Decreasing relevance
            })
          })
        }
      }
    }

    // Limit to top 10 citations
    return citations.slice(0, 10)
  }

  /**
   * Calculate confidence score
   */
  private calculateConfidenceScore(
    successful: AgentResult[],
    failed: AgentResult[],
    threshold: number
  ): number {
    const total = successful.length + failed.length
    if (total === 0) return 0

    // Base score from completion rate
    const completionRate = successful.length / total
    let score = completionRate * 100

    // Boost for having key agents
    const agentIds = new Set(successful.map((r) => r.agentId))
    if (agentIds.has('researcher')) score += 10
    if (agentIds.has('analyzer')) score += 5
    if (agentIds.has('reporter')) score += 5

    // Penalty for failed critical agents
    if (failed.some((r) => ['researcher', 'analyzer'].includes(r.agentId))) {
      score -= 15
    }

    // Apply threshold
    if (score < threshold) score = threshold

    return Math.max(0, Math.min(100, score))
  }

  /**
   * Validate aggregated result
   */
  validate(result: AggregatedResult): { valid: boolean; errors: string[] } {
    const errors: string[] = []

    if (!result.summary || result.summary.length < 10) {
      errors.push('Summary is missing or too short')
    }

    if (result.sections.length === 0) {
      errors.push('No sections generated')
    }

    if (result.citations.length === 0) {
      errors.push('No citations included')
    }

    return {
      valid: errors.length === 0,
      errors,
    }
  }

  /**
   * Format result for different outputs
   */
  formatForDisplay(result: AggregatedResult, format: 'summary' | 'detailed' | 'report'): string {
    switch (format) {
      case 'summary':
        return result.summary

      case 'detailed':
        return [
          result.summary,
          '',
          'Key Findings:',
          ...result.keyFindings.map((f, i) => `${i + 1}. ${f}`),
          '',
          'Recommendations:',
          ...result.recommendations.map((r, i) => `${i + 1}. ${r}`),
        ].join('\n')

      case 'report':
        return [
          '# Research Report',
          '',
          '## Summary',
          result.summary,
          '',
          ...result.sections.map((s) => `## ${s.title}\n${s.content}`),
          '',
          '## Key Findings',
          ...result.keyFindings.map((f, i) => `${i + 1}. ${f}`),
          '',
          '## Recommendations',
          ...result.recommendations.map((r, i) => `${i + 1}. ${r}`),
          '',
          '## Sources',
          ...result.citations.map((c, i) => `${i + 1}. [${c.title}](${c.url})`),
        ].join('\n')

      default:
        return result.summary
    }
  }
}

// Singleton instance
let aggregator: ResultAggregator | null = null

export function getResultAggregator(): ResultAggregator {
  if (!aggregator) {
    aggregator = new ResultAggregator()
  }
  return aggregator
}
