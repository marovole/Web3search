/**
 * News Agent
 * Responsible for aggregating news and social media sentiment
 */

import { BaseSubAgent } from './index'
import type { SharedContext, AgentInput, AgentResult, NewsArticle, SocialMetricMap } from '../types'
import type { ISSEEmitter } from '../../../services/deep-research/types'
import type { Env } from '../../../types/env'
import type { ModelConfig } from '../../model-routing'


export class NewsAgent extends BaseSubAgent {
  readonly id = 'news'
  readonly name = 'NewsAgent'
  readonly description = 'News aggregation agent - collects and analyzes news and social media'
  readonly capabilities = [
    'news_collection',
    'social_sentiment_analysis',
    'trend_detection',
    'influencer_tracking',
  ]
  readonly inputRequirements: string[] = []

  async execute(
    context: SharedContext,
    input: AgentInput,
    emitter?: ISSEEmitter
  ): Promise<AgentResult> {
    const startTime = Date.now()
    this.emitProgress(emitter, 'news', 'NewsAgent: Gathering news and social media sentiment...')

    try {
      // Step 1: Collect news articles
      const newsArticles = await this.collectNews(input.query, emitter)

      // Step 2: Collect social metrics
      const socialMetrics = await this.collectSocialMetrics(input.query, context, emitter)

      // Step 3: Analyze sentiment
      const sentimentAnalysis = this.analyzeSentiment(newsArticles)

      // Step 4: Generate news report
      const newsReport = this.generateNewsReport(newsArticles, socialMetrics, sentimentAnalysis)

      // Update context
      context.collectedData.newsArticles = newsArticles
      context.collectedData.socialMetrics = socialMetrics

      this.emitProgress(emitter, 'news', `NewsAgent: Complete - collected ${newsArticles.length} articles`)

      return {
        agentId: this.id,
        agentName: this.name,
        status: 'completed',
        output: newsReport,
        metrics: {
          tokensUsed: 0,
          duration: this.getDuration(startTime),
          sourcesProcessed: newsArticles.length,
        },
      }
    } catch (error) {
      return this.createErrorResult(error, startTime)
    }
  }

  private async collectNews(query: string, emitter?: ISSEEmitter): Promise<NewsArticle[]> {
    // Extract potential token symbol
    const tokenPattern = /\b[A-Z]{2,8}\b/g
    const tokens = query.match(tokenPattern) || []
    const primaryToken = tokens[0] || 'crypto'

    const articles: NewsArticle[] = []

    try {
      // Search for news using Brave News API or similar
      const newsQueries = [
        `${primaryToken} cryptocurrency news`,
        `${primaryToken} crypto latest`,
        'crypto market news today',
      ]

      const fetchPromises = newsQueries.map(async (q) => {
        try {
          const response = await fetch(
            `https://api.search.brave.com/v1/news?q=${encodeURIComponent(q)}`,
            {
              headers: {
                Accept: 'application/json',
                'X-Subscription-Token': this.env.BRAVE_SEARCH_API_KEY || '',
              },
            }
          )

          if (!response.ok) return []

          const data = await response.json() as Record<string, unknown>
          return this.normalizeNewsResults(data, q)
        } catch (error) {
          console.warn(`News fetch failed for query "${q}":`, error)
          return []
        }
      })

      const results = await Promise.all(fetchPromises)
      results.forEach((r) => articles.push(...r))
    } catch (error) {
      console.warn('News collection error:', error)
    }

    // Sort by date and deduplicate
    return this.deduplicateAndSortNews(articles).slice(0, 30)
  }

  private normalizeNewsResults(
    data: Record<string, unknown>,
    query: string
  ): NewsArticle[] {
    const results = (data as { results?: Array<{
      title?: string
      url?: string
      description?: string
      source?: { name?: string }
      published_at?: string
    }> }).results || []

    return results.map((article, index) => ({
      id: `news_${query.slice(0, 8)}_${index}`,
      title: article.title || 'No title',
      url: article.url || '',
      source: article.source?.name || 'Unknown',
      publishedAt: article.published_at || new Date().toISOString(),
      sentiment: 'neutral' as const,
      engagement: Math.floor(Math.random() * 1000), // Placeholder
      snippet: article.description || '',
    }))
  }

  private deduplicateAndSortNews(articles: NewsArticle[]): NewsArticle[] {
    const seen = new Set<string>()

    return articles
      .filter((a) => {
        if (seen.has(a.url)) return false
        seen.add(a.url)
        return true
      })
      .sort((a, b) => {
        const dateA = new Date(a.publishedAt).getTime()
        const dateB = new Date(b.publishedAt).getTime()
        return dateB - dateA
      })
  }

  private async collectSocialMetrics(
    query: string,
    context: SharedContext,
    emitter?: ISSEEmitter
  ): Promise<SocialMetricMap> {
    const metrics: SocialMetricMap = {}

    // Extract token addresses from price data
    const tokenAddresses = Object.keys(context.collectedData.priceData)

    for (const address of tokenAddresses) {
      const priceData = context.collectedData.priceData[address]
      const symbol = priceData.symbol

      try {
        // Fetch Twitter/X mentions (using a mock/placeholder API)
        const socialData = await this.fetchSocialMetrics(symbol, address)

        metrics[address] = {
          twitterFollowers: socialData.twitterFollowers,
          discordMembers: socialData.discordMembers,
          telegramMembers: socialData.telegramMembers,
          holderCount: socialData.holderCount || 0,
          sentimentScore: socialData.sentimentScore || 0,
          recentMentions: socialData.recentMentions || 0,
        }
      } catch (error) {
        console.warn(`Social metrics fetch failed for ${symbol}:`, error)

        metrics[address] = {
          holderCount: 0,
          sentimentScore: 0,
          recentMentions: 0,
        }
      }
    }

    return metrics
  }

  private async fetchSocialMetrics(
    symbol: string,
    address: string
  ): Promise<{
    twitterFollowers?: number
    discordMembers?: number
    telegramMembers?: number
    holderCount?: number
    sentimentScore: number
    recentMentions: number
  }> {
    // Placeholder - in production, this would call APIs like:
    // - Twitter/X API for follower counts
    // - Discord API for server members
    // - Telegram API for group members
    // - DexScreener or similar for holder counts

    // Simulate some social metrics based on token
    return {
      twitterFollowers: Math.floor(Math.random() * 50000),
      discordMembers: Math.floor(Math.random() * 10000),
      telegramMembers: Math.floor(Math.random() * 20000),
      holderCount: Math.floor(Math.random() * 5000),
      sentimentScore: (Math.random() * 2 - 1), // -1 to 1
      recentMentions: Math.floor(Math.random() * 500),
    }
  }

  private analyzeSentiment(articles: NewsArticle[]): SentimentAnalysis {
    if (articles.length === 0) {
      return {
        overallSentiment: 'neutral',
        positiveCount: 0,
        negativeCount: 0,
        neutralCount: 0,
        trendingTopics: [],
        keyHeadlines: [],
      }
    }

    // Simple keyword-based sentiment analysis
    const positiveKeywords = ['surge', 'rally', 'breakthrough', 'adoption', 'partnership', 'bullish', 'growth', 'success']
    const negativeKeywords = ['crash', 'dump', 'hack', 'exploit', 'scam', 'warning', 'ban', 'crackdown']

    let positiveCount = 0
    let negativeCount = 0

    articles.forEach((article) => {
      const text = `${article.title} ${article.snippet}`.toLowerCase()

      if (positiveKeywords.some((k) => text.includes(k))) {
        positiveCount++
        article.sentiment = 'positive'
      } else if (negativeKeywords.some((k) => text.includes(k))) {
        negativeCount++
        article.sentiment = 'negative'
      } else {
        article.sentiment = 'neutral'
      }
    })

    let overallSentiment: 'positive' | 'negative' | 'neutral'
    if (positiveCount > negativeCount * 2) {
      overallSentiment = 'positive'
    } else if (negativeCount > positiveCount * 2) {
      overallSentiment = 'negative'
    } else {
      overallSentiment = 'neutral'
    }

    // Extract trending topics
    const topicCounts = new Map<string, number>()
    articles.forEach((article) => {
      const text = article.title.toLowerCase()
      const topics = ['defi', 'nft', 'gaming', 'metaverse', 'dao', 'staking', 'layer2', 'bitcoin', 'ethereum']
      topics.forEach((topic) => {
        if (text.includes(topic)) {
          topicCounts.set(topic, (topicCounts.get(topic) || 0) + 1)
        }
      })
    })

    const trendingTopics = [...topicCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([topic]) => topic)

    return {
      overallSentiment,
      positiveCount,
      negativeCount,
      neutralCount: articles.length - positiveCount - negativeCount,
      trendingTopics,
      keyHeadlines: articles.slice(0, 5).map((a) => ({
        title: a.title,
        source: a.source,
        sentiment: a.sentiment,
      })),
    }
  }

  private generateNewsReport(
    articles: NewsArticle[],
    socialMetrics: SocialMetricMap,
    sentimentAnalysis: SentimentAnalysis
  ): NewsReport {
    return {
      articleCount: articles.length,
      socialMetrics: Object.entries(socialMetrics).map(([address, m]) => ({
        token: address,
        ...m,
      })),
      sentimentAnalysis,
      topHeadlines: sentimentAnalysis.keyHeadlines,
      summary: this.generateNewsSummary(articles, sentimentAnalysis),
      recommendations: this.generateNewsRecommendations(sentimentAnalysis),
    }
  }

  private generateNewsSummary(articles: NewsArticle[], sentiment: SentimentAnalysis): string {
    const parts: string[] = []

    parts.push(`Collected ${articles.length} articles from various sources.`)

    if (sentiment.positiveCount > sentiment.negativeCount) {
      parts.push(`Overall sentiment is positive with ${sentiment.positiveCount} positive vs ${sentiment.negativeCount} negative articles.`)
    } else if (sentiment.negativeCount > sentiment.positiveCount) {
      parts.push(`Market sentiment shows caution with ${sentiment.negativeCount} concerning articles.`)
    }

    if (sentiment.trendingTopics.length > 0) {
      parts.push(`Trending topics: ${sentiment.trendingTopics.join(', ')}`)
    }

    return parts.join(' ')
  }

  private generateNewsRecommendations(sentiment: SentimentAnalysis): string[] {
    const recommendations: string[] = []

    if (sentiment.overallSentiment === 'positive' && sentiment.positiveCount > 10) {
      recommendations.push('Strong positive news flow - market attention may be increasing')
    }
    if (sentiment.overallSentiment === 'negative' && sentiment.negativeCount > 5) {
      recommendations.push('Negative news dominance - consider risk management')
    }
    if (sentiment.trendingTopics.includes('hack') || sentiment.trendingTopics.includes('exploit')) {
      recommendations.push('Security concerns trending - verify protocol security before investing')
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
// News Report Types
// ============================================================================

interface SentimentAnalysis {
  overallSentiment: 'positive' | 'negative' | 'neutral'
  positiveCount: number
  negativeCount: number
  neutralCount: number
  trendingTopics: string[]
  keyHeadlines: Array<{
    title: string
    source: string
    sentiment: 'positive' | 'negative' | 'neutral'
  }>
}

interface NewsReport {
  articleCount: number
  socialMetrics: Array<{
    token: string
    twitterFollowers?: number
    discordMembers?: number
    telegramMembers?: number
    holderCount: number
    sentimentScore: number
    recentMentions: number
  }>
  sentimentAnalysis: SentimentAnalysis
  topHeadlines: SentimentAnalysis['keyHeadlines']
  summary: string
  recommendations: string[]
}
