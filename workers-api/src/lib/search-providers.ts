/**
 * Search Providers Aggregation Module
 * Integrates multiple search APIs (Brave, Tavily, Serper) with unified interface
 * Provides caching, deduplication, and relevance scoring
 */

import type { Env } from '../types/env'

/**
 * Normalized search result structure
 * All providers map to this common format
 */
export interface NormalizedSearchResult {
  id: string // Unique ID: `${provider}-${query}-${index}`
  query: string // Original search query
  provider: 'brave' | 'tavily' | 'serper'
  title: string
  snippet: string
  url: string
  relevance_score: number // 0-1, normalized across providers
  accessed_at: string // ISO 8601 timestamp
  metadata?: {
    // Raw response for debugging
    raw?: Record<string, unknown>
  }
}

/**
 * Brave Search API response structure
 */
interface BraveSearchResponse {
  web?: {
    results?: Array<{
      title: string
      description: string
      url: string
      age?: string
    }>
  }
}

/**
 * Fetch search results from Brave Search API
 * https://brave.com/search/api/
 */
async function fetchBraveSearch(
  query: string,
  env: Env
): Promise<NormalizedSearchResult[]> {
  if (!env.BRAVE_SEARCH_API_KEY) {
    console.warn('Brave Search API key not configured')
    return []
  }

  try {
    const url = new URL('https://api.search.brave.com/res/v1/web/search')
    url.searchParams.set('q', query)
    url.searchParams.set('count', '12') // Max results per query

    const response = await fetch(url.toString(), {
      headers: {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': env.BRAVE_SEARCH_API_KEY,
      },
    })

    if (!response.ok) {
      console.error(`Brave Search API error: ${response.status} ${response.statusText}`)
      return []
    }

    const data = (await response.json()) as BraveSearchResponse
    const results = data.web?.results || []

    return results.map((result, index) => ({
      id: `brave-${query}-${index}`,
      query,
      provider: 'brave' as const,
      title: result.title || '',
      snippet: result.description || '',
      url: result.url || '',
      // Brave doesn't provide scores, use position-based relevance
      relevance_score: Math.max(0.5, 1 - index * 0.05),
      accessed_at: new Date().toISOString(),
      metadata: {
        raw: result as Record<string, unknown>,
      },
    }))
  } catch (error) {
    console.error(`Brave Search API request failed for "${query}":`, error)
    return []
  }
}

/**
 * Cache key generator for search results
 */
function getCacheKey(provider: string, query: string): string {
  return `search:${provider}:${query.toLowerCase()}`
}

/**
 * Fetch and cache search results for a single query
 * Uses KV for 5-minute TTL cache
 */
async function fetchCachedSearchResults(
  query: string,
  env: Env,
  provider: 'brave' | 'tavily' | 'serper'
): Promise<NormalizedSearchResult[]> {
  // Try cache first
  if (env.CACHE) {
    const cacheKey = getCacheKey(provider, query)
    const cached = await env.CACHE.get(cacheKey)
    if (cached) {
      try {
        return JSON.parse(cached) as NormalizedSearchResult[]
      } catch {
        // Invalid cache, continue to fetch
      }
    }
  }

  // Fetch fresh results
  let results: NormalizedSearchResult[] = []
  switch (provider) {
    case 'brave':
      results = await fetchBraveSearch(query, env)
      break
    case 'tavily':
      // TODO: Implement Tavily API
      console.warn('Tavily Search not yet implemented')
      break
    case 'serper':
      // TODO: Implement Serper API
      console.warn('Serper Search not yet implemented')
      break
  }

  // Cache results (5 minute TTL)
  if (env.CACHE && results.length > 0) {
    const cacheKey = getCacheKey(provider, query)
    await env.CACHE.put(cacheKey, JSON.stringify(results), {
      expirationTtl: 300, // 5 minutes
    })
  }

  return results
}

/**
 * Deduplicate search results by URL
 * Keeps the result with highest relevance score for each URL
 */
function deduplicateResults(
  results: NormalizedSearchResult[]
): NormalizedSearchResult[] {
  const urlMap = new Map<string, NormalizedSearchResult>()

  for (const result of results) {
    const existing = urlMap.get(result.url)
    if (!existing || result.relevance_score > existing.relevance_score) {
      urlMap.set(result.url, result)
    }
  }

  return Array.from(urlMap.values())
}

/**
 * Main aggregation function
 * Fetches search results from all configured providers for multiple queries
 * Returns deduplicated and sorted results
 */
export async function fetchSearchResultsForQueries(
  queries: string[],
  env: Env
): Promise<NormalizedSearchResult[]> {
  // Limit total queries to prevent API quota abuse
  const limitedQueries = queries.slice(0, 10)

  // Determine available providers
  const providers: Array<'brave' | 'tavily' | 'serper'> = []
  if (env.BRAVE_SEARCH_API_KEY) providers.push('brave')
  if (env.TAVILY_API_KEY) providers.push('tavily')
  if (env.SERPER_API_KEY) providers.push('serper')

  if (providers.length === 0) {
    console.warn('No search API keys configured, using fallback')
    return []
  }

  // Fetch results from all providers for all queries (parallel)
  const allPromises = limitedQueries.flatMap((query) =>
    providers.map((provider) => fetchCachedSearchResults(query, env, provider))
  )

  const allResults = await Promise.all(allPromises)
  const flatResults = allResults.flat()

  // Deduplicate by URL
  const deduplicated = deduplicateResults(flatResults)

  // Sort by relevance score (descending)
  deduplicated.sort((a, b) => b.relevance_score - a.relevance_score)

  return deduplicated
}
