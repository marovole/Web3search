/**
 * Search Providers Aggregation Module
 * Integrates multiple search APIs (Brave, Tavily, Serper) with unified interface,
 * failover orchestration, caching, and telemetry tracking.
 *
 * Provider Priority (failover order): Brave → Tavily → Serper
 * Each provider has independent caching with 5-minute TTL
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
    raw?: Record<string, unknown> // Raw response for debugging
  }
}

/** Supported search providers */
type SearchProvider = 'brave' | 'tavily' | 'serper'

/** Provider priority order for failover */
const PROVIDER_PRIORITY: SearchProvider[] = ['brave', 'tavily', 'serper']

/** Timeout for each provider attempt (milliseconds) */
const PROVIDER_TIMEOUT_MS = 5_000

/** Cache TTL for search results (seconds) */
const CACHE_TTL_SECONDS = 300 // 5 minutes

/** Max query length to log (for privacy) */
const QUERY_SNIPPET_LIMIT = 64

/**
 * Provider failure categories
 * Used for telemetry and failover decision making
 */
type ProviderFailureCode =
  | 'network'       // Network errors (ECONNRESET, ETIMEDOUT, etc.)
  | 'http'          // HTTP server errors (500, 502, 503, 504)
  | 'rate_limit'    // Rate limit error (429)
  | 'timeout'       // Request timeout (> PROVIDER_TIMEOUT_MS)
  | 'empty_results' // Provider returned zero results
  | 'unknown'       // Other errors

/** Detailed failure information */
interface ProviderFailureDetails {
  code: ProviderFailureCode
  statusCode?: number
  message: string
}

/**
 * Telemetry data for provider attempts
 * Logged for monitoring and debugging
 */
interface ProviderTelemetry {
  provider: SearchProvider
  query: string // Truncated query for privacy (max 64 chars)
  success: boolean // Whether results were obtained
  fromCache: boolean // Whether results came from cache
  ttfbMs: number // Time to first byte (0 if cached)
  totalMs: number // Total request time
  statusCode?: number // HTTP status code
  resultCount: number // Number of results returned
  errorType?: ProviderFailureCode // Failure type if unsuccessful
  errorMessage?: string // Error details if unsuccessful
}

/** Response from provider fetch functions */
interface ProviderFetchResponse {
  results: NormalizedSearchResult[]
  statusCode: number
}

/** Provider fetch function signature */
type ProviderFetcher = (
  query: string,
  env: Env,
  signal?: AbortSignal
) => Promise<ProviderFetchResponse>

/**
 * Custom error class for provider fetch failures
 * Includes categorization and HTTP status codes
 */
class ProviderFetchError extends Error {
  constructor(
    public provider: SearchProvider,
    public code: ProviderFailureCode,
    public statusCode?: number,
    message?: string
  ) {
    super(message ?? `${provider} fetch failed`)
    this.name = 'ProviderFetchError'
  }
}

/**
 * Truncate query string for logging (privacy)
 */
function buildQuerySnippet(query: string): string {
  if (query.length <= QUERY_SNIPPET_LIMIT) {
    return query
  }
  return `${query.slice(0, QUERY_SNIPPET_LIMIT - 3)}...`
}

/**
 * Calculate position-based relevance score
 * Used when provider doesn't provide explicit scores
 * Formula: max(0.5, 1 - index * 0.05)
 */
function normalizePositionScore(index: number): number {
  return Math.max(0.5, 1 - index * 0.05)
}

/**
 * Normalize Tavily's scoring system to 0-1 range
 * Tavily may provide scores in different ranges (0-1, 0-100, etc.)
 * Falls back to position-based scoring if unavailable
 */
function normalizeTavilyScore(rawScore: number | undefined, index: number): number {
  if (typeof rawScore === 'number' && !Number.isNaN(rawScore)) {
    // If already in 0-1 range, use as-is
    if (rawScore >= 0 && rawScore <= 1) {
      return rawScore
    }
    // If in 0-100 range, normalize
    return Math.min(1, Math.max(0, rawScore / 100))
  }
  // Fallback to position-based scoring
  return normalizePositionScore(index)
}

/**
 * Log provider telemetry for monitoring
 * Structured logging for easy querying and analysis
 */
function logProviderTelemetry(telemetry: ProviderTelemetry): void {
  console.info('[search-provider]', telemetry)
}

/**
 * Categorize provider errors for telemetry and failover logic
 */
function categorizeProviderError(error: unknown): ProviderFailureDetails {
  if (error instanceof ProviderFetchError) {
    return {
      code: error.code,
      statusCode: error.statusCode,
      message: error.message,
    }
  }

  if (error instanceof DOMException && error.name === 'AbortError') {
    return { code: 'timeout', message: 'Request aborted due to timeout' }
  }

  if (error instanceof Error) {
    return { code: 'network', message: error.message }
  }

  return { code: 'unknown', message: 'Unknown provider failure' }
}

/**
 * Get list of available providers based on configured API keys
 * Returns providers in priority order
 */
function getAvailableProviders(env: Env): SearchProvider[] {
  return PROVIDER_PRIORITY.filter((provider) => {
    switch (provider) {
      case 'brave':
        return Boolean(env.BRAVE_SEARCH_API_KEY)
      case 'tavily':
        return Boolean(env.TAVILY_API_KEY)
      case 'serper':
        return Boolean(env.SERPER_API_KEY)
    }
  })
}

// ============================================================================
// Brave Search API Integration
// ============================================================================

/** Brave Search API response structure */
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
  env: Env,
  signal?: AbortSignal
): Promise<ProviderFetchResponse> {
  if (!env.BRAVE_SEARCH_API_KEY) {
    console.warn('Brave Search API key not configured')
    return { results: [], statusCode: 0 }
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
      signal,
    })

    if (!response.ok) {
      const failureCode: ProviderFailureCode =
        response.status === 429 ? 'rate_limit' : 'http'
      throw new ProviderFetchError(
        'brave',
        failureCode,
        response.status,
        `Brave Search responded with ${response.status}`
      )
    }

    const data = (await response.json()) as BraveSearchResponse
    const rawResults = data.web?.results || []

    const normalized = rawResults.map((result, index) => ({
      id: `brave-${query}-${index}`,
      query,
      provider: 'brave' as const,
      title: result.title || '',
      snippet: result.description || '',
      url: result.url || '',
      relevance_score: normalizePositionScore(index),
      accessed_at: new Date().toISOString(),
      metadata: {
        raw: result as Record<string, unknown>,
      },
    }))

    return { results: normalized, statusCode: response.status }
  } catch (error) {
    // Re-throw ProviderFetchError as-is
    if (error instanceof ProviderFetchError) {
      throw error
    }

    // Handle timeout
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ProviderFetchError(
        'brave',
        'timeout',
        undefined,
        'Brave Search request aborted due to timeout'
      )
    }

    // Wrap other errors as network failures
    throw new ProviderFetchError(
      'brave',
      'network',
      undefined,
      `Brave Search API request failed: ${error instanceof Error ? error.message : 'unknown error'}`
    )
  }
}

// ============================================================================
// Tavily Search API Integration
// ============================================================================

/** Tavily Search API response structure (defensive parsing) */
interface TavilySearchEntry {
  title?: string
  snippet?: string
  description?: string
  url?: string
  score?: number
}

interface TavilySearchResponse {
  data?: {
    results?: TavilySearchEntry[]
    organic?: TavilySearchEntry[]
  }
  results?: TavilySearchEntry[]
}

/**
 * Fetch search results from Tavily Search API
 * https://docs.tavily.com
 */
async function fetchTavilySearch(
  query: string,
  env: Env,
  signal?: AbortSignal
): Promise<ProviderFetchResponse> {
  if (!env.TAVILY_API_KEY) {
    console.warn('Tavily Search API key not configured')
    return { results: [], statusCode: 0 }
  }

  try {
    const response = await fetch('https://api.tavily.com/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        api_key: env.TAVILY_API_KEY,
        query,
        search_depth: 'basic',
        max_results: 12,
      }),
      signal,
    })

    if (!response.ok) {
      const failureCode: ProviderFailureCode =
        response.status === 429 ? 'rate_limit' : 'http'
      throw new ProviderFetchError(
        'tavily',
        failureCode,
        response.status,
        `Tavily Search responded with ${response.status}`
      )
    }

    const data = (await response.json()) as TavilySearchResponse

    // Defensive parsing: try multiple possible response structures
    const rawResults =
      data.results ??
      data.data?.results ??
      data.data?.organic ??
      []

    const normalized = rawResults.map((result, index) => ({
      id: `tavily-${query}-${index}`,
      query,
      provider: 'tavily' as const,
      title: result.title ?? result.description ?? '',
      snippet: result.snippet ?? result.description ?? '',
      url: result.url ?? '',
      relevance_score: normalizeTavilyScore(result.score, index),
      accessed_at: new Date().toISOString(),
      metadata: {
        raw: result as Record<string, unknown>,
      },
    }))

    return { results: normalized, statusCode: response.status }
  } catch (error) {
    if (error instanceof ProviderFetchError) {
      throw error
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ProviderFetchError(
        'tavily',
        'timeout',
        undefined,
        'Tavily Search request aborted due to timeout'
      )
    }

    throw new ProviderFetchError(
      'tavily',
      'network',
      undefined,
      `Tavily Search API request failed: ${error instanceof Error ? error.message : 'unknown error'}`
    )
  }
}

// ============================================================================
// Serper Search API Integration
// ============================================================================

/** Serper (Google) Search API response structure */
interface SerperOrganicResult {
  title?: string
  snippet?: string
  link?: string
  display_link?: string
}

interface SerperSearchResponse {
  organic?: SerperOrganicResult[]
}

/**
 * Fetch search results from Serper (Google) Search API
 * https://serper.dev/docs
 */
async function fetchSerperSearch(
  query: string,
  env: Env,
  signal?: AbortSignal
): Promise<ProviderFetchResponse> {
  if (!env.SERPER_API_KEY) {
    console.warn('Serper Search API key not configured')
    return { results: [], statusCode: 0 }
  }

  try {
    const response = await fetch('https://google.serper.dev/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': env.SERPER_API_KEY,
      },
      body: JSON.stringify({
        q: query,
        num: 12, // Max results
      }),
      signal,
    })

    if (!response.ok) {
      const failureCode: ProviderFailureCode =
        response.status === 429 ? 'rate_limit' : 'http'
      throw new ProviderFetchError(
        'serper',
        failureCode,
        response.status,
        `Serper Search responded with ${response.status}`
      )
    }

    const data = (await response.json()) as SerperSearchResponse
    const rawResults = data.organic || []

    const normalized = rawResults.map((result, index) => ({
      id: `serper-${query}-${index}`,
      query,
      provider: 'serper' as const,
      title: result.title ?? '',
      snippet: result.snippet ?? '',
      url: result.link ?? '',
      relevance_score: normalizePositionScore(index),
      accessed_at: new Date().toISOString(),
      metadata: {
        raw: result as Record<string, unknown>,
      },
    }))

    return { results: normalized, statusCode: response.status }
  } catch (error) {
    if (error instanceof ProviderFetchError) {
      throw error
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ProviderFetchError(
        'serper',
        'timeout',
        undefined,
        'Serper Search request aborted due to timeout'
      )
    }

    throw new ProviderFetchError(
      'serper',
      'network',
      undefined,
      `Serper Search API request failed: ${error instanceof Error ? error.message : 'unknown error'}`
    )
  }
}

// ============================================================================
// Caching and Provider Orchestration
// ============================================================================

/** Map of provider names to fetch functions */
const PROVIDER_FETCHERS: Record<SearchProvider, ProviderFetcher> = {
  brave: fetchBraveSearch,
  tavily: fetchTavilySearch,
  serper: fetchSerperSearch,
}

/**
 * Generate cache key for provider-specific results
 * Format: search:{provider}:{lowercase_query}
 */
function getCacheKey(provider: SearchProvider, query: string): string {
  return `search:${provider}:${query.toLowerCase()}`
}

/** Response from cached fetch including cache hit information */
interface CachedProviderResult {
  results: NormalizedSearchResult[]
  fromCache: boolean
  statusCode?: number
}

/**
 * Fetch provider results with caching
 * Checks cache first, falls back to API on miss
 */
async function fetchProviderResultsWithCache(
  query: string,
  env: Env,
  provider: SearchProvider,
  signal?: AbortSignal
): Promise<CachedProviderResult> {
  const cacheKey = getCacheKey(provider, query)

  // Try cache first
  if (env.CACHE) {
    const cached = await env.CACHE.get(cacheKey)
    if (cached) {
      try {
        const parsed = JSON.parse(cached) as NormalizedSearchResult[]
        return {
          results: parsed,
          fromCache: true,
          statusCode: 200, // Cached results are considered successful
        }
      } catch {
        // Corrupted cache entry, continue to fetch
      }
    }
  }

  // Fetch fresh results
  const fetcher = PROVIDER_FETCHERS[provider]
  const { results, statusCode } = await fetcher(query, env, signal)

  // Cache successful results
  if (env.CACHE && results.length > 0) {
    await env.CACHE.put(cacheKey, JSON.stringify(results), {
      expirationTtl: CACHE_TTL_SECONDS,
    })
  }

  return {
    results,
    fromCache: false,
    statusCode,
  }
}

/**
 * Deduplicate search results by URL
 * Keeps the result with highest relevance score for each URL
 * (Single-provider deduplication as per spec)
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

/** Result of a single provider attempt */
interface ProviderAttemptResult {
  results: NormalizedSearchResult[]
  telemetry: ProviderTelemetry
  failure?: ProviderFailureDetails
}

/**
 * Attempt to fetch results from a single provider
 * Includes timeout, telemetry, and error handling
 */
async function attemptProvider(
  query: string,
  env: Env,
  provider: SearchProvider
): Promise<ProviderAttemptResult> {
  const querySnippet = buildQuerySnippet(query)
  const attemptStart = Date.now()

  // Setup timeout
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), PROVIDER_TIMEOUT_MS)

  try {
    const { results, fromCache, statusCode } = await fetchProviderResultsWithCache(
      query,
      env,
      provider,
      controller.signal
    )

    const responseTime = Date.now()
    const ttfbMs = fromCache ? 0 : Math.max(0, responseTime - attemptStart)
    const totalMs = Math.max(0, Date.now() - attemptStart)
    const success = results.length > 0

    const telemetry: ProviderTelemetry = {
      provider,
      query: querySnippet, // Only log truncated query for privacy
      success,
      fromCache,
      ttfbMs,
      totalMs,
      statusCode,
      resultCount: results.length,
      errorType: success ? undefined : 'empty_results',
      errorMessage: success ? undefined : 'Provider returned zero results',
    }

    logProviderTelemetry(telemetry)

    const failure = success
      ? undefined
      : {
          code: 'empty_results' as ProviderFailureCode,
          statusCode,
          message: 'Provider returned zero results',
        }

    return { results, telemetry, failure }
  } catch (error) {
    const failure = categorizeProviderError(error)
    const failedAt = Date.now()
    const ttfbMs = Math.max(0, failedAt - attemptStart)

    const telemetry: ProviderTelemetry = {
      provider,
      query: querySnippet, // Only log truncated query for privacy
      success: false,
      fromCache: false,
      ttfbMs,
      totalMs: ttfbMs,
      statusCode: failure.statusCode,
      resultCount: 0,
      errorType: failure.code,
      errorMessage: failure.message,
    }

    logProviderTelemetry(telemetry)

    return { results: [], telemetry, failure }
  } finally {
    clearTimeout(timeoutId)
  }
}

/**
 * Fetch search results with provider failover
 * Tries providers in priority order, returns first successful result
 * Returns empty array if all providers fail
 */
async function fetchWithFailover(
  query: string,
  env: Env,
  providers: SearchProvider[]
): Promise<NormalizedSearchResult[]> {
  const querySnippet = buildQuerySnippet(query)
  const attemptTelemetries: ProviderTelemetry[] = []

  // Try each provider in order
  for (const provider of providers) {
    const attempt = await attemptProvider(query, env, provider)
    attemptTelemetries.push(attempt.telemetry)

    // Return on first success
    if (!attempt.failure && attempt.results.length > 0) {
      return attempt.results
    }
  }

  // All providers failed
  console.warn('[search-provider] All providers failed for query', {
    query: querySnippet,
    attempts: attemptTelemetries.map((telemetry) => ({
      provider: telemetry.provider,
      success: telemetry.success,
      statusCode: telemetry.statusCode,
      errorType: telemetry.errorType,
      totalMs: telemetry.totalMs,
    })),
  })

  return []
}

// ============================================================================
// Main Public API
// ============================================================================

/**
 * Main aggregation function
 * Fetches search results for multiple queries with provider failover
 * Returns deduplicated and sorted results
 *
 * @param queries - Array of search queries (max 10)
 * @param env - Environment with API keys and cache
 * @returns Deduplicated search results sorted by relevance
 */
export async function fetchSearchResultsForQueries(
  queries: string[],
  env: Env
): Promise<NormalizedSearchResult[]> {
  // Limit total queries to prevent API quota abuse
  const limitedQueries = queries.slice(0, 10)

  // Get available providers based on configured API keys
  const providers = getAvailableProviders(env)

  if (providers.length === 0) {
    console.warn('No search API keys configured, cannot fetch results')
    return []
  }

  // Fetch results for each query with failover
  const resultsPerQuery = await Promise.all(
    limitedQueries.map((query) => fetchWithFailover(query, env, providers))
  )

  // Flatten all results
  const flatResults = resultsPerQuery.flat()

  // Deduplicate by URL (keeps highest relevance score)
  const deduplicated = deduplicateResults(flatResults)

  // Sort by relevance score (descending)
  deduplicated.sort((a, b) => b.relevance_score - a.relevance_score)

  return deduplicated
}
