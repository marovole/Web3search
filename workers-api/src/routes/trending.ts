/**
 * Trending API Routes
 * Provides trending crypto topics and hotspots
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import { getSupabaseClient } from '../lib/supabase'
import { createCoinGeckoClient } from '../lib/coingecko'

const trending = new Hono<{ Bindings: Env }>()

/**
 * GET /hotspots
 * Get trending crypto topics/hotspots
 */
trending.get('/hotspots', async (c) => {
  const limit = parseInt(c.req.query('limit') || '10', 10)
  const forceRefresh = c.req.query('force_refresh') === 'true'

  try {
    // Use service role to bypass RLS for backend queries
    const supabase = getSupabaseClient(c.env, true)

    // Check cache first (if not force refresh)
    if (!forceRefresh && c.env.CACHE) {
      const cacheKey = `trending:hotspots:${limit}`
      const cached = await c.env.CACHE.get(cacheKey)
      if (cached) {
        try {
          return c.json(JSON.parse(cached))
        } catch (parseError) {
          // Cache data is malformed, continue to database query
          console.warn('[Trending] Malformed cache data, falling back to database')
        }
      }
    }

    // Query recent popular topics from messages
    const { data: hotTopics, error } = await supabase
      .from('messages')
      .select('content')
      .eq('role', 'user')
      .order('created_at', { ascending: false })
      .limit(100)

    if (error) {
      console.error('[Trending] Database error:', error)
      return c.json(
        {
          error: {
            code: 'DATABASE_ERROR',
            message: 'Failed to fetch trending data',
            status: 500,
          },
        },
        500
      )
    }

    // Extract crypto keywords and count frequency
    const keywordCounts = new Map<string, number>()
    const cryptoKeywords = [
      'bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol',
      'cardano', 'ada', 'polygon', 'matic', 'avalanche', 'avax',
      'polkadot', 'dot', 'chainlink', 'link', 'uniswap', 'uni',
      'bnb', 'ripple', 'xrp', 'dogecoin', 'doge', 'tron', 'trx',
      'near', 'algorand', 'algo', 'cosmos', 'atom'
    ]

    hotTopics?.forEach((msg) => {
      const content = msg.content.toLowerCase()
      cryptoKeywords.forEach((keyword) => {
        if (content.includes(keyword)) {
          keywordCounts.set(keyword, (keywordCounts.get(keyword) || 0) + 1)
        }
      })
    })

    // Sort by frequency and get top keywords
    const topKeywords = Array.from(keywordCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, Math.min(limit * 3, 30)) // Fetch more than needed to account for API failures and deduplication

    // Fetch real crypto data from CoinGecko
    const coinGecko = createCoinGeckoClient()
    
    // Track seen coin IDs to avoid duplicates (e.g., 'btc' and 'bitcoin' resolve to same coin)
    const seenCoinIds = new Set<string>()
    
    const hotspotPromises = topKeywords.map(async ([keyword, searchCount]) => {
      try {
        // Resolve keyword to coin ID and fetch market data
        const coinId = (coinGecko as any).resolveCoinId(keyword)
        
        // Skip if we've already seen this coin (handles aliases like 'btc'/'bitcoin')
        if (seenCoinIds.has(coinId)) {
          return null
        }
        seenCoinIds.add(coinId)
        
        const coinData = await coinGecko.getCoinPrice(coinId)

        if ('error' in coinData) {
          console.warn(`[Trending] Failed to fetch data for ${keyword}:`, coinData.message)
          return null
        }

        // Calculate total score based on search count and market rank
        // Higher search count = higher score, lower market cap rank = higher score
        const searchScore = searchCount * 10 // Weight for search frequency
        const rankScore = coinData.market_cap_rank
          ? Math.max(0, 100 - coinData.market_cap_rank) // Top 100 coins get bonus
          : 0
        const totalScore = searchScore + rankScore

        return {
          coin_id: coinId,
          symbol: coinData.symbol,
          name: coinData.name,
          market_cap_rank: coinData.market_cap_rank || 9999,
          price_usd: coinData.price_usd,
          price_change_24h: coinData.price_change_24h,
          volume_24h: 0, // CoinGecko free API doesn't provide volume in this endpoint
          total_score: totalScore,
          scores_breakdown: {
            twitter: 0,
            reddit: 0,
            price: Math.abs(coinData.price_change_24h) * 5, // Price volatility as score
            volume: 0,
            news: searchScore / 2, // Search count as proxy for news activity
          },
          timestamp: new Date().toISOString(),
        }
      } catch (err) {
        console.error(`[Trending] Error processing ${keyword}:`, err)
        return null
      }
    })

    // Wait for all API calls and filter out failures
    const hotspotResults = await Promise.all(hotspotPromises)
    const validHotspots = hotspotResults
      .filter((h): h is NonNullable<typeof h> => h !== null)
      .sort((a, b) => b.total_score - a.total_score) // Sort by total score
      .slice(0, limit) // Get top N

    // If we don't have enough results, fetch default popular coins
    if (validHotspots.length < limit) {
      const defaultCoins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polygon', 'avalanche-2', 'polkadot', 'chainlink']
      const existingCoinIds = new Set(validHotspots.map(h => h.coin_id))
      
      for (const coinId of defaultCoins) {
        if (validHotspots.length >= limit) break
        if (existingCoinIds.has(coinId)) continue
        
        try {
          const coinData = await coinGecko.getCoinPrice(coinId)
          if ('error' in coinData) continue
          
          validHotspots.push({
            coin_id: coinId,
            symbol: coinData.symbol,
            name: coinData.name,
            market_cap_rank: coinData.market_cap_rank || 9999,
            price_usd: coinData.price_usd,
            price_change_24h: coinData.price_change_24h,
            volume_24h: 0,
            total_score: coinData.market_cap_rank ? Math.max(0, 100 - coinData.market_cap_rank) : 0,
            scores_breakdown: {
              twitter: 0,
              reddit: 0,
              price: Math.abs(coinData.price_change_24h) * 5,
              volume: 0,
              news: 0,
            },
            timestamp: new Date().toISOString(),
          })
          existingCoinIds.add(coinId)
        } catch (err) {
          console.warn(`[Trending] Failed to fetch default coin ${coinId}:`, err)
        }
      }
    }

    const response = {
      hotspots: validHotspots,
      count: validHotspots.length,
      updated_at: new Date().toISOString(),
    }

    // Cache the result for 15 minutes
    if (c.env.CACHE) {
      const cacheKey = `trending:hotspots:${limit}`
      await c.env.CACHE.put(cacheKey, JSON.stringify(response), {
        expirationTtl: 60 * 15, // 15 minutes
      })
    }

    return c.json(response)
  } catch (error) {
    console.error('[Trending] Unexpected error:', error)
    return c.json(
      {
        error: {
          code: 'INTERNAL_ERROR',
          message: 'An unexpected error occurred',
          status: 500,
        },
      },
      500
    )
  }
})

export default trending
