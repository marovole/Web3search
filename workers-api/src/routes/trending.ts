/**
 * Trending API Routes
 * Provides trending crypto topics and hotspots
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import { createSupabaseClient } from '../lib/supabase'

const trending = new Hono<{ Bindings: Env }>()

/**
 * GET /hotspots
 * Get trending crypto topics/hotspots
 */
trending.get('/hotspots', async (c) => {
  const limit = parseInt(c.req.query('limit') || '10', 10)
  const forceRefresh = c.req.query('force_refresh') === 'true'

  try {
    const supabase = createSupabaseClient(c.env)

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

    // Extract keywords and count frequency
    const keywordCounts = new Map<string, number>()
    const cryptoKeywords = [
      'bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol',
      'cardano', 'ada', 'polygon', 'matic', 'avalanche', 'avax',
      'polkadot', 'dot', 'chainlink', 'link', 'uniswap', 'uni',
      'defi', 'nft', 'dao', 'web3', 'metaverse', 'staking',
      'yield', 'liquidity', 'smart contract', 'dex', 'cefi'
    ]

    hotTopics?.forEach((msg) => {
      const content = msg.content.toLowerCase()
      cryptoKeywords.forEach((keyword) => {
        if (content.includes(keyword)) {
          keywordCounts.set(keyword, (keywordCounts.get(keyword) || 0) + 1)
        }
      })
    })

    // Sort by frequency and get top N
    const sortedHotspots = Array.from(keywordCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map(([keyword, count], index) => ({
        id: index + 1,
        keyword,
        count,
        trend: 'up' as const, // Simplified, could calculate based on historical data
        category: getCategoryForKeyword(keyword),
      }))

    const response = {
      hotspots: sortedHotspots,
      count: sortedHotspots.length,
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

/**
 * Helper function to categorize keywords
 */
function getCategoryForKeyword(keyword: string): string {
  const categories: Record<string, string[]> = {
    'Layer 1': ['bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol', 'cardano', 'ada', 'avalanche', 'avax', 'polkadot', 'dot'],
    'DeFi': ['defi', 'uniswap', 'uni', 'yield', 'liquidity', 'staking', 'dex'],
    'Infrastructure': ['chainlink', 'link', 'polygon', 'matic', 'smart contract'],
    'Trends': ['nft', 'dao', 'web3', 'metaverse', 'cefi'],
  }

  for (const [category, keywords] of Object.entries(categories)) {
    if (keywords.includes(keyword)) {
      return category
    }
  }

  return 'Other'
}

export default trending
