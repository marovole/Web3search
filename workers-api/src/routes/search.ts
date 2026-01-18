/**
 * Search Routes
 * Autocomplete and search functionality for cryptocurrency projects
 */

import { Hono } from 'hono'
import type { Env } from '../types/env'
import { searchProjects } from '../lib/convex-http'

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
    const { data, error } = await searchProjects(c.env, query, limit)

    if (error || !data) {
      console.error('Search query error:', error)
      return c.json(
        {
          error: {
            code: 'SEARCH_ERROR',
            message: error?.message || 'Failed to search projects',
            status: 500,
          },
        },
        500
      )
    }

    if (c.env.CACHE && data.results) {
      const cacheKey = `search:autocomplete:${query}:${limit}`
      await c.env.CACHE.put(cacheKey, JSON.stringify(data.results), {
        expirationTtl: 300,
      })
    }

    return c.json({
      query: data.query,
      count: data.count,
      results: data.results,
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
