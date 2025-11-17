/**
 * Search Routes
 * Autocomplete and search functionality for cryptocurrency projects
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import { getSupabaseClient } from '../lib/supabase'

const search = new Hono<{ Bindings: Env }>()

/**
 * GET /autocomplete
 * Search autocomplete for cryptocurrency projects
 * Query Parameters:
 * - q: search query (required)
 * - limit: max results to return (optional, default: 10, max: 50)
 */
search.get('/autocomplete', async (c) => {
  const query = c.req.query('q')?.trim()
  const limitParam = c.req.query('limit')
  const limit = limitParam ? Math.min(parseInt(limitParam, 10), 50) : 10

  // Validate query parameter
  if (!query) {
    return c.json(
      {
        error: {
          code: 'MISSING_QUERY',
          message: 'Query parameter "q" is required',
          status: 400,
        },
      },
      400
    )
  }

  if (query.length < 1) {
    return c.json(
      {
        error: {
          code: 'INVALID_QUERY',
          message: 'Query must be at least 1 character',
          status: 400,
        },
      },
      400
    )
  }

  try {
    const supabase = getSupabaseClient(c.env)
    // 转义 PostgreSQL ILIKE 特殊字符以防止 SQL 注入
    const searchTerm = query.replace(/[%_]/g, '\\$&')

    // Search in both symbol and name fields
    // Use ilike for case-insensitive search
    const { data, error } = await supabase
      .from('projects')
      .select('id, symbol, name, coingecko_id, description, blockchain, categories, tags')
      .or(`symbol.ilike.%${searchTerm}%,name.ilike.%${searchTerm}%`)
      .order('symbol', { ascending: true })
      .limit(limit)

    if (error) {
      console.error('Search query error:', error)
      return c.json(
        {
          error: {
            code: 'SEARCH_ERROR',
            message: 'Failed to search projects',
            status: 500,
          },
        },
        500
      )
    }

    // Cache the result if KV is available
    if (c.env.CACHE && data) {
      const cacheKey = `search:autocomplete:${query}:${limit}`
      // Cache for 5 minutes (300 seconds)
      await c.env.CACHE.put(cacheKey, JSON.stringify(data), {
        expirationTtl: 300,
      })
    }

    return c.json({
      query,
      count: data?.length || 0,
      results: data || [],
    })
  } catch (error) {
    console.error('Autocomplete error:', error)
    return c.json(
      {
        error: {
          code: 'INTERNAL_ERROR',
          message: 'An internal error occurred',
          status: 500,
        },
      },
      500
    )
  }
})

export default search
