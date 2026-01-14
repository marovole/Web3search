/**
 * Researcher Agent
 * Responsible for gathering information from multiple sources
 */

import { BaseSubAgent } from './index'
import type { SharedContext, AgentInput, AgentResult, NormalizedSearchResult, PriceDataMap } from '../types'
import type { ISSEEmitter } from '../../../services/deep-research/types'
import type { Env as _Env } from '../../../types/env'
import type { ModelConfig as _ModelConfig } from '../../model-routing'


export class ResearcherAgent extends BaseSubAgent {
  readonly id = 'researcher'
  readonly name = 'Researcher'
  readonly description = 'Information gathering agent - collects data from search, price, and news sources'
  readonly capabilities = [
    'web_search',
    'price_data_collection',
    'news_gathering',
    'social_sentiment_analysis',
  ]
  readonly inputRequirements = ['query']

  async execute(
    context: SharedContext,
    input: AgentInput,
    emitter?: ISSEEmitter
  ): Promise<AgentResult> {
    const startTime = Date.now()
    this.emitProgress(emitter, 'research', `Researcher: Gathering information for "${input.query}"...`)

    try {
      // Step 1: Generate optimized search queries
      const searchQueries = await this.generateSearchQueries(input.query)

      // Step 2: Perform parallel searches
      const searchResults = await this.performParallelSearch(searchQueries, emitter)

      // Step 3: Collect price data if token-related
      const priceData = await this.collectPriceData(input.query, emitter)

      // Step 4: Analyze and structure results
      const analyzedData = await this.analyzeResults(searchResults, input.query)

      // Update shared context
      context.collectedData.searchResults = searchResults
      context.collectedData.priceData = priceData

      this.emitProgress(
        emitter,
        'research',
        `Researcher: Complete - collected ${searchResults.length} sources and ${Object.keys(priceData).length} price feeds`
      )

      return {
        agentId: this.id,
        agentName: this.name,
        status: 'completed',
        output: {
          searchQueries,
          searchResultsCount: searchResults.length,
          priceDataCount: Object.keys(priceData).length,
          analyzedData,
        },
        metrics: {
          tokensUsed: 0, // To be extracted from model response
          duration: this.getDuration(startTime),
          sourcesProcessed: searchResults.length,
        },
      }
    } catch (error) {
      return this.createErrorResult(error, startTime)
    }
  }

  private async generateSearchQueries(query: string): Promise<string[]> {
    // Extract token symbols from query
    const tokenPattern = /\b[A-Z]{2,8}\b/g
    const tokens = query.match(tokenPattern) || []

    const baseQueries = [
      query,
      `${query} latest news`,
      `${query} price analysis`,
      `${query} market sentiment`,
    ]

    // Add token-specific queries
    if (tokens.length > 0) {
      tokens.forEach((token) => {
        baseQueries.push(`${token} token analysis`)
        baseQueries.push(`${token} cryptocurrency news`)
      })
    }

    return [...new Set(baseQueries)]
  }

  private async performParallelSearch(
    queries: string[],
    _emitter?: ISSEEmitter
  ): Promise<NormalizedSearchResult[]> {
    const results: NormalizedSearchResult[] = []
    const searchPromises = queries.map(async (query) => {
      try {
        const response = await fetch(
          `https://api.search.brave.com/v1/search?q=${encodeURIComponent(query)}`,
          {
            headers: {
              Accept: 'application/json',
              'X-Subscription-Token': this.env.BRAVE_SEARCH_API_KEY || '',
            },
          }
        )

        if (!response.ok) {
          console.warn(`Search failed for query: ${query}`)
          return []
        }

        const data = await response.json() as Record<string, unknown>
        return this.normalizeSearchResults(data, query)
      } catch (error) {
        console.warn(`Search error for query "${query}":`, error)
        return []
      }
    })

    const allResults = await Promise.all(searchPromises)
    allResults.forEach((r) => results.push(...r))

    // Sort by relevance and deduplicate
    return this.deduplicateAndSort(results)
  }

  private normalizeSearchResults(
    data: Record<string, unknown>,
    query: string
  ): NormalizedSearchResult[] {
    const webResults = (data as { web?: Array<{
      title?: string
      url?: string
      description?: string
      published_on?: number
    }> }).web || []

    return webResults.map((result, index) => ({
      id: `search_${query.slice(0, 10)}_${index}`,
      title: result.title || 'No title',
      url: result.url || '',
      snippet: result.description || '',
      relevanceScore: this.calculateRelevanceScore(result, query),
      provider: 'brave',
      publishedAt: result.published_on
        ? new Date(result.published_on * 1000).toISOString()
        : undefined,
    }))
  }

  private calculateRelevanceScore(
    result: { title?: string; description?: string },
    query: string
  ): number {
    const queryLower = query.toLowerCase()
    const titleLower = (result.title || '').toLowerCase()
    const descLower = (result.description || '').toLowerCase()

    let score = 0.5 // Base score

    // Title matches
    if (titleLower.includes(queryLower)) score += 0.3
    if (titleLower.startsWith(queryLower)) score += 0.1

    // Description matches
    const queryWords = queryLower.split(' ')
    queryWords.forEach((word) => {
      if (descLower.includes(word)) score += 0.05
    })

    return Math.min(score, 1)
  }

  private deduplicateAndSort(results: NormalizedSearchResult[]): NormalizedSearchResult[] {
    const seen = new Set<string>()
    return results
      .filter((r) => {
        if (seen.has(r.url)) return false
        seen.add(r.url)
        return true
      })
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, 50) // Limit to top 50 results
  }

  private async collectPriceData(
    query: string,
    _emitter?: ISSEEmitter
  ): Promise<PriceDataMap> {
    const tokenPattern = /\b0x[a-fA-F0-9]{40}\b|\b[A-Z]{2,8}\b/g
    const matches = query.match(tokenPattern) || []

    if (matches.length === 0) return {}

    const priceData: PriceDataMap = {}

    for (const token of matches.slice(0, 5)) {
      try {
        // Try CoinGecko API
        const response = await fetch(
          `https://api.coingecko.com/api/v3/simple/price?ids=${token.toLowerCase()}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true`
        )

        if (!response.ok) continue

        const data = await response.json() as Record<string, Record<string, number>>
        const tokenData = data[token.toLowerCase()]

        if (tokenData) {
          priceData[token] = {
            symbol: token.toUpperCase(),
            name: token,
            currentPrice: tokenData.usd || 0,
            priceChange24h: tokenData.usd_24h_change || 0,
            marketCap: tokenData.usd_market_cap || 0,
            volume24h: tokenData.usd_24h_vol || 0,
            liquidity: 0, // Would need additional API call
          }
        }
      } catch (error) {
        console.warn(`Price fetch failed for ${token}:`, error)
      }
    }

    return priceData
  }

  private async analyzeResults(
    results: NormalizedSearchResult[],
    query: string
  ): Promise<Record<string, unknown>> {
    // Group results by topic
    const topics = new Map<string, NormalizedSearchResult[]>()

    results.forEach((result) => {
      const topic = this.categorizeResult(result, query)
      if (!topics.has(topic)) {
        topics.set(topic, [])
      }
      topics.get(topic)!.push(result)
    })

    return {
      topics: Object.fromEntries(topics),
      topResults: results.slice(0, 10).map((r) => ({
        title: r.title,
        url: r.url,
        snippet: r.snippet,
      })),
      totalResults: results.length,
    }
  }

  private categorizeResult(
    result: NormalizedSearchResult,
    _query: string
  ): string {
    const titleLower = result.title.toLowerCase()
    const snippetLower = result.snippet.toLowerCase()
    const combined = `${titleLower} ${snippetLower}`

    if (combined.includes('price') || combined.includes('trading') || combined.includes('market')) {
      return 'price_market'
    }
    if (combined.includes('news') || combined.includes('announcement') || combined.includes('update')) {
      return 'news'
    }
    if (combined.includes('audit') || combined.includes('security') || combined.includes('risk')) {
      return 'security'
    }
    if (combined.includes('team') || combined.includes('roadmap') || combined.includes('whitepaper')) {
      return 'fundamentals'
    }
    return 'general'
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
