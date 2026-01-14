/**
 * Agent Tools Registry
 * Tools available for the Agent Engine to use during task execution
 */

import type { AgentTool, AgentContext, ToolResult } from './agent-engine'
import { CoinGeckoClient } from './coingecko'
import { fetchSearchResultsForQueries } from './search-providers'

/**
 * Tool: get_token_price
 * Fetches real-time price data for a cryptocurrency token
 */
export const getTokenPriceTool: AgentTool = {
  name: 'get_token_price',
  description: 'Get current price, 24h change, and market cap for a cryptocurrency token',
  parameters: {
    symbol: {
      type: 'string',
      description: 'Token symbol (e.g., BTC, ETH, SOL) or CoinGecko ID',
      required: true,
    },
  },
  async execute(params: Record<string, unknown>, _context: AgentContext): Promise<ToolResult> {
    const symbol = params.symbol as string
    if (!symbol) {
      return { success: false, error: 'Missing required parameter: symbol' }
    }

    try {
      const client = new CoinGeckoClient()
      const result = await client.getCoinPrice(symbol.toLowerCase())

      if ('error' in result) {
        return { success: false, error: result.message }
      }

      return {
        success: true,
        data: {
          symbol: result.symbol,
          name: result.name,
          price_usd: result.price_usd,
          price_change_24h: result.price_change_24h,
          market_cap: result.market_cap,
          market_cap_rank: result.market_cap_rank,
          fetched_at: new Date().toISOString(),
        },
      }
    } catch (error) {
      return {
        success: false,
        error: `Failed to fetch price: ${error instanceof Error ? error.message : 'Unknown error'}`,
      }
    }
  },
}

/**
 * Tool: get_risk_score
 * Calculates a basic risk score (ScamMeter) for a token
 * This is a simplified version - full implementation would include:
 * - Contract analysis
 * - Social media sentiment
 * - Holder distribution
 * - Team verification
 */
export const getRiskScoreTool: AgentTool = {
  name: 'get_risk_score',
  description: 'Calculate a risk score (0-100) for a cryptocurrency token based on available metrics',
  parameters: {
    symbol: {
      type: 'string',
      description: 'Token symbol (e.g., BTC, ETH, SOL)',
      required: true,
    },
  },
  async execute(params: Record<string, unknown>, _context: AgentContext): Promise<ToolResult> {
    const symbol = params.symbol as string
    if (!symbol) {
      return { success: false, error: 'Missing required parameter: symbol' }
    }

    try {
      const client = new CoinGeckoClient()
      const priceData = await client.getCoinPrice(symbol.toLowerCase())

      if ('error' in priceData) {
        return { success: false, error: priceData.message }
      }

      // Simplified risk score calculation based on available metrics
      // Lower score = higher risk
      const redFlags: string[] = []
      let score = 100

      // Factor 1: Market cap rank (higher rank = more established)
      if (priceData.market_cap_rank === null) {
        score -= 20
        redFlags.push('Unranked by market cap - low visibility')
      } else if (priceData.market_cap_rank > 500) {
        score -= 15
        redFlags.push(`Low market cap rank (#${priceData.market_cap_rank})`)
      } else if (priceData.market_cap_rank > 100) {
        score -= 5
      }

      // Factor 2: Market cap size
      if (priceData.market_cap < 1_000_000) {
        score -= 25
        redFlags.push('Micro cap (<$1M) - high manipulation risk')
      } else if (priceData.market_cap < 10_000_000) {
        score -= 15
        redFlags.push('Very small market cap (<$10M)')
      } else if (priceData.market_cap < 100_000_000) {
        score -= 5
      }

      // Factor 3: Extreme price volatility
      const priceChange = Math.abs(priceData.price_change_24h)
      if (priceChange > 50) {
        score -= 20
        redFlags.push(`Extreme volatility (${priceData.price_change_24h.toFixed(1)}% in 24h)`)
      } else if (priceChange > 20) {
        score -= 10
        redFlags.push(`High volatility (${priceData.price_change_24h.toFixed(1)}% in 24h)`)
      }

      // Ensure score is within bounds
      score = Math.max(0, Math.min(100, score))

      // Determine risk level
      let riskLevel: string
      if (score >= 80) riskLevel = 'low'
      else if (score >= 60) riskLevel = 'medium'
      else if (score >= 40) riskLevel = 'high'
      else riskLevel = 'critical'

      return {
        success: true,
        data: {
          symbol: priceData.symbol,
          name: priceData.name,
          risk_score: score,
          risk_level: riskLevel,
          red_flags: redFlags,
          metrics_used: {
            market_cap_rank: priceData.market_cap_rank,
            market_cap: priceData.market_cap,
            price_change_24h: priceData.price_change_24h,
          },
          note: 'This is a simplified risk assessment. Full ScamMeter includes contract analysis, social metrics, and holder distribution.',
          assessed_at: new Date().toISOString(),
        },
      }
    } catch (error) {
      return {
        success: false,
        error: `Failed to calculate risk score: ${error instanceof Error ? error.message : 'Unknown error'}`,
      }
    }
  },
}

/**
 * Tool: search_news
 * Searches for recent news about a cryptocurrency topic
 */
export const searchNewsTool: AgentTool = {
  name: 'search_news',
  description: 'Search for recent cryptocurrency news and articles about a topic or token',
  parameters: {
    query: {
      type: 'string',
      description: 'Search query (e.g., "Bitcoin ETF", "Ethereum upgrade", "Solana news")',
      required: true,
    },
    limit: {
      type: 'number',
      description: 'Maximum number of results to return (default: 5, max: 10)',
      required: false,
    },
  },
  async execute(params: Record<string, unknown>, context: AgentContext): Promise<ToolResult> {
    const query = params.query as string
    const limit = Math.min((params.limit as number) || 5, 10)

    if (!query) {
      return { success: false, error: 'Missing required parameter: query' }
    }

    try {
      // Add "crypto news" context to ensure relevant results
      const searchQuery = `${query} cryptocurrency news latest`
      const results = await fetchSearchResultsForQueries([searchQuery], context.env)

      if (results.length === 0) {
        return {
          success: true,
          data: {
            query,
            articles: [],
            message: 'No news articles found for this query',
            searched_at: new Date().toISOString(),
          },
        }
      }

      const articles = results.slice(0, limit).map((result, index) => ({
        rank: index + 1,
        title: result.title,
        snippet: result.snippet,
        url: result.url,
        source: new URL(result.url).hostname,
        relevance_score: result.relevance_score,
      }))

      return {
        success: true,
        data: {
          query,
          articles,
          total_found: results.length,
          returned: articles.length,
          searched_at: new Date().toISOString(),
        },
      }
    } catch (error) {
      return {
        success: false,
        error: `Failed to search news: ${error instanceof Error ? error.message : 'Unknown error'}`,
      }
    }
  },
}

/**
 * Tool: check_price_condition
 * Evaluates if a price condition is met (for price alert tasks)
 */
export const checkPriceConditionTool: AgentTool = {
  name: 'check_price_condition',
  description: 'Check if a price condition is met (e.g., price above/below a target)',
  parameters: {
    symbol: {
      type: 'string',
      description: 'Token symbol (e.g., BTC, ETH)',
      required: true,
    },
    condition: {
      type: 'string',
      description: 'Condition type: "above", "below", "change_up", "change_down"',
      required: true,
    },
    target_value: {
      type: 'number',
      description: 'Target price or percentage value',
      required: true,
    },
  },
  async execute(params: Record<string, unknown>, _context: AgentContext): Promise<ToolResult> {
    const symbol = params.symbol as string
    const condition = params.condition as string
    const targetValue = params.target_value as number

    if (!symbol || !condition || targetValue === undefined) {
      return { success: false, error: 'Missing required parameters' }
    }

    try {
      const client = new CoinGeckoClient()
      const priceData = await client.getCoinPrice(symbol.toLowerCase())

      if ('error' in priceData) {
        return { success: false, error: priceData.message }
      }

      let conditionMet = false
      let message = ''

      switch (condition) {
        case 'above':
          conditionMet = priceData.price_usd >= targetValue
          message = conditionMet
            ? `${priceData.symbol} price ($${priceData.price_usd.toFixed(2)}) is above target ($${targetValue})`
            : `${priceData.symbol} price ($${priceData.price_usd.toFixed(2)}) is still below target ($${targetValue})`
          break
        case 'below':
          conditionMet = priceData.price_usd <= targetValue
          message = conditionMet
            ? `${priceData.symbol} price ($${priceData.price_usd.toFixed(2)}) is below target ($${targetValue})`
            : `${priceData.symbol} price ($${priceData.price_usd.toFixed(2)}) is still above target ($${targetValue})`
          break
        case 'change_up':
          conditionMet = priceData.price_change_24h >= targetValue
          message = conditionMet
            ? `${priceData.symbol} 24h change (${priceData.price_change_24h.toFixed(2)}%) is above threshold (${targetValue}%)`
            : `${priceData.symbol} 24h change (${priceData.price_change_24h.toFixed(2)}%) is below threshold (${targetValue}%)`
          break
        case 'change_down':
          conditionMet = priceData.price_change_24h <= -targetValue
          message = conditionMet
            ? `${priceData.symbol} dropped ${Math.abs(priceData.price_change_24h).toFixed(2)}% (threshold: ${targetValue}%)`
            : `${priceData.symbol} has not dropped enough (${priceData.price_change_24h.toFixed(2)}% vs -${targetValue}%)`
          break
        default:
          return { success: false, error: `Unknown condition type: ${condition}` }
      }

      return {
        success: true,
        data: {
          symbol: priceData.symbol,
          name: priceData.name,
          current_price: priceData.price_usd,
          price_change_24h: priceData.price_change_24h,
          condition,
          target_value: targetValue,
          condition_met: conditionMet,
          message,
          checked_at: new Date().toISOString(),
        },
      }
    } catch (error) {
      return {
        success: false,
        error: `Failed to check price condition: ${error instanceof Error ? error.message : 'Unknown error'}`,
      }
    }
  },
}

/**
 * Register all agent tools
 * Call this function during module initialization
 */
export function registerAllAgentTools(registerTool: (tool: AgentTool) => void): void {
  registerTool(getTokenPriceTool)
  registerTool(getRiskScoreTool)
  registerTool(searchNewsTool)
  registerTool(checkPriceConditionTool)
}
