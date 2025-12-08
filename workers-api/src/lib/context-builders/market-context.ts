/**
 * Market Context Builder
 *
 * Aggregates real-time market data from DexScreener and GoPlus APIs
 * to provide dynamic context injection for deep research prompts.
 *
 * @module context-builders/market-context
 */

import type { Env } from '../../types/env'

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Aggregated market context for a token/contract
 */
export interface MarketContext {
  /** Contract address (checksummed or lowercase) */
  contract_address: string
  /** Blockchain identifier (e.g., 'ethereum', 'bsc', 'polygon') */
  chain: string
  /** ISO8601 timestamp when data was fetched */
  fetched_at: string
  /** Whether this data was served from cache */
  from_cache: boolean
  /** Price information */
  price: {
    usd: number
    change_24h: number
  } | null
  /** Liquidity pool information */
  liquidity: {
    usd: number
    locked_percent?: number
  } | null
  /** 24-hour trading volume in USD */
  volume_24h: number | null
  /** Holder distribution information */
  holders: {
    total?: number
    top10_percent?: number
  } | null
  /** Security analysis results */
  security: {
    is_honeypot: boolean
    is_open_source: boolean
    has_proxy: boolean
    risk_level: 'low' | 'medium' | 'high' | 'unknown'
  } | null
  /** Data source availability flags */
  data_sources: {
    dexscreener: boolean
    goplus: boolean
  }
}

// ============================================================================
// Configuration
// ============================================================================

/** Cache TTL in seconds (1 hour) */
const CACHE_TTL_SECONDS = 3600

/** Request timeout in milliseconds (5 seconds) */
const REQUEST_TIMEOUT_MS = 5000

/** DexScreener API base URL */
const DEXSCREENER_API_URL = 'https://api.dexscreener.com/latest/dex/tokens'

/** GoPlus API base URL */
const GOPLUS_API_URL = 'https://api.gopluslabs.io/api/v1/token_security'

// ============================================================================
// External API Response Types
// ============================================================================

interface DexScreenerPair {
  priceUsd?: string
  priceChange?: { h24?: number | string }
  liquidity?: { usd?: number }
  volume?: { h24?: number }
  fdv?: number
  marketCap?: number
}

interface DexScreenerResponse {
  pairs?: DexScreenerPair[]
}

interface GoPlusSecurityRecord {
  is_honeypot?: string
  is_open_source?: string
  is_proxy?: string
  proxy?: string
  holder_count?: string
  top10_holder_rate?: string
  lp_holder_count?: string
  lp_total_supply?: string
}

interface GoPlusResponse {
  code?: number
  message?: string
  result?: Record<string, GoPlusSecurityRecord>
}

// ============================================================================
// Main Export
// ============================================================================

/**
 * Fetch aggregated market context for a token contract
 *
 * @param address - Contract address
 * @param chain - Blockchain identifier (default: '1' for Ethereum mainnet)
 * @param env - Cloudflare Workers environment bindings
 * @returns Aggregated market context with graceful degradation
 *
 * @example
 * ```typescript
 * const context = await fetchMarketContext(
 *   '0x1234...abcd',
 *   '1', // Ethereum
 *   env
 * )
 * ```
 */
export async function fetchMarketContext(
  address: string,
  chain: string = '1',
  env: Env
): Promise<MarketContext> {
  const normalizedAddress = address.toLowerCase()
  const cacheKey = `research:context:${chain}:${normalizedAddress}`

  // Attempt to serve from KV cache
  if (env.CACHE) {
    try {
      const cached = await env.CACHE.get(cacheKey)
      if (cached) {
        const parsed = JSON.parse(cached) as MarketContext
        return { ...parsed, from_cache: true }
      }
    } catch (error) {
      console.warn('[MarketContext] Cache read failed:', error)
    }
  }

  // Fetch from external APIs in parallel
  const startTime = Date.now()
  const [dexData, securityData] = await Promise.all([
    fetchDexScreenerData(normalizedAddress),
    fetchGoPlusData(normalizedAddress, chain),
  ])
  const fetchDuration = Date.now() - startTime

  console.log(`[MarketContext] Fetched data for ${address} in ${fetchDuration}ms`)

  // Build context object
  const context: MarketContext = {
    contract_address: address,
    chain,
    fetched_at: new Date().toISOString(),
    from_cache: false,
    price: dexData.price,
    liquidity: dexData.liquidity,
    volume_24h: dexData.volume24h,
    holders: securityData.holders,
    security: securityData.security,
    data_sources: {
      dexscreener: dexData.success,
      goplus: securityData.success,
    },
  }

  // Cache the result (best-effort, even if partial data)
  if (env.CACHE) {
    try {
      await env.CACHE.put(cacheKey, JSON.stringify(context), {
        expirationTtl: CACHE_TTL_SECONDS,
      })
    } catch (error) {
      console.warn('[MarketContext] Cache write failed:', error)
    }
  }

  return context
}

/**
 * Format market context as a prompt-friendly string
 *
 * @param context - Market context object
 * @returns Formatted string for prompt injection
 */
export function formatMarketContextForPrompt(context: MarketContext): string {
  const lines: string[] = [
    '=== REAL-TIME MARKET DATA SNAPSHOT ===',
    `Contract: ${context.contract_address}`,
    `Chain: ${chainIdToName(context.chain)}`,
    `Data Timestamp: ${context.fetched_at}`,
    `Cache Status: ${context.from_cache ? 'CACHED' : 'FRESH'}`,
    '',
  ]

  // Price section
  if (context.price) {
    lines.push('## Price')
    lines.push(`- Current Price: $${formatNumber(context.price.usd)}`)
    lines.push(`- 24h Change: ${formatPercent(context.price.change_24h)}`)
    lines.push('')
  } else {
    lines.push('## Price: Data unavailable')
    lines.push('')
  }

  // Liquidity section
  if (context.liquidity) {
    lines.push('## Liquidity')
    lines.push(`- Pool Liquidity: $${formatNumber(context.liquidity.usd)}`)
    if (context.liquidity.locked_percent !== undefined) {
      lines.push(`- Locked: ${formatPercent(context.liquidity.locked_percent)}`)
    }
    lines.push('')
  } else {
    lines.push('## Liquidity: Data unavailable')
    lines.push('')
  }

  // Volume
  if (context.volume_24h !== null) {
    lines.push(`## 24h Volume: $${formatNumber(context.volume_24h)}`)
    lines.push('')
  }

  // Holders section
  if (context.holders) {
    lines.push('## Holder Distribution')
    if (context.holders.total !== undefined) {
      lines.push(`- Total Holders: ${context.holders.total.toLocaleString()}`)
    }
    if (context.holders.top10_percent !== undefined) {
      const riskFlag = context.holders.top10_percent > 50 ? ' [HIGH CONCENTRATION RISK]' : ''
      lines.push(`- Top 10 Holders Control: ${formatPercent(context.holders.top10_percent)}${riskFlag}`)
    }
    lines.push('')
  }

  // Security section
  if (context.security) {
    lines.push('## Security Analysis (GoPlus)')
    lines.push(`- Honeypot Detection: ${context.security.is_honeypot ? 'YES [DANGER]' : 'No'}`)
    lines.push(`- Open Source: ${context.security.is_open_source ? 'Yes' : 'No [CAUTION]'}`)
    lines.push(`- Proxy Contract: ${context.security.has_proxy ? 'Yes [UPGRADEABLE]' : 'No'}`)
    lines.push(`- Overall Risk Level: ${context.security.risk_level.toUpperCase()}`)
    lines.push('')
  } else {
    lines.push('## Security Analysis: Data unavailable')
    lines.push('')
  }

  // Data quality notice
  lines.push('=== END MARKET DATA ===')
  lines.push('')
  lines.push('IMPORTANT: Use the above data as ground truth. Do NOT hallucinate or guess values not provided.')

  return lines.join('\n')
}

/**
 * Extract contract address from a query string
 *
 * @param query - User query that may contain a contract address
 * @returns Extracted address or null
 */
export function extractContractAddress(query: string): string | null {
  // Match Ethereum-style addresses (0x followed by 40 hex characters)
  const ethMatch = query.match(/0x[a-fA-F0-9]{40}/i)
  if (ethMatch) {
    return ethMatch[0]
  }

  // Match Solana addresses (base58, typically 32-44 characters)
  const solMatch = query.match(/[1-9A-HJ-NP-Za-km-z]{32,44}/)
  if (solMatch && !solMatch[0].includes('http')) {
    return solMatch[0]
  }

  return null
}

/**
 * Detect blockchain from query context
 *
 * @param query - User query
 * @returns Chain identifier
 */
export function detectChainFromQuery(query: string): string {
  const lowerQuery = query.toLowerCase()

  const chainMappings: Record<string, string> = {
    'ethereum': '1',
    'eth': '1',
    'bsc': '56',
    'binance': '56',
    'bnb': '56',
    'polygon': '137',
    'matic': '137',
    'arbitrum': '42161',
    'arb': '42161',
    'optimism': '10',
    'op': '10',
    'avalanche': '43114',
    'avax': '43114',
    'base': '8453',
    'solana': 'solana',
    'sol': 'solana',
  }

  for (const [keyword, chainId] of Object.entries(chainMappings)) {
    if (lowerQuery.includes(keyword)) {
      return chainId
    }
  }

  // Default to Ethereum
  return '1'
}

// ============================================================================
// Internal Helper Functions
// ============================================================================

interface DexScreenerResult {
  success: boolean
  price: MarketContext['price']
  liquidity: MarketContext['liquidity']
  volume24h: number | null
}

async function fetchDexScreenerData(address: string): Promise<DexScreenerResult> {
  const url = `${DEXSCREENER_API_URL}/${encodeURIComponent(address)}`

  try {
    const response = await fetchWithTimeout(url, REQUEST_TIMEOUT_MS)

    if (!response.ok) {
      console.warn(`[DexScreener] HTTP ${response.status} for ${address}`)
      return { success: false, price: null, liquidity: null, volume24h: null }
    }

    const data = (await response.json()) as DexScreenerResponse
    const pairs = Array.isArray(data.pairs) ? data.pairs : []

    if (pairs.length === 0) {
      console.log(`[DexScreener] No pairs found for ${address}`)
      return { success: true, price: null, liquidity: null, volume24h: null }
    }

    // Select the pair with highest volume
    const sortedPairs = [...pairs].sort(
      (a, b) => (toNumber(b.volume?.h24) ?? 0) - (toNumber(a.volume?.h24) ?? 0)
    )
    const bestPair = sortedPairs[0]

    const priceUsd = toNumber(bestPair.priceUsd)
    const change24h = toNumber(bestPair.priceChange?.h24)
    const liquidityUsd = toNumber(bestPair.liquidity?.usd)
    const volume24h = toNumber(bestPair.volume?.h24)

    return {
      success: true,
      price: priceUsd !== null
        ? { usd: priceUsd, change_24h: change24h ?? 0 }
        : null,
      liquidity: liquidityUsd !== null
        ? { usd: liquidityUsd }
        : null,
      volume24h,
    }
  } catch (error) {
    console.error('[DexScreener] Fetch failed:', error)
    return { success: false, price: null, liquidity: null, volume24h: null }
  }
}

interface GoPlusResult {
  success: boolean
  holders: MarketContext['holders']
  security: MarketContext['security']
}

async function fetchGoPlusData(address: string, chain: string): Promise<GoPlusResult> {
  const url = `${GOPLUS_API_URL}/${encodeURIComponent(chain)}?contract_addresses=${encodeURIComponent(address)}`

  try {
    const response = await fetchWithTimeout(url, REQUEST_TIMEOUT_MS)

    if (!response.ok) {
      console.warn(`[GoPlus] HTTP ${response.status} for ${address}`)
      return { success: false, holders: null, security: null }
    }

    const data = (await response.json()) as GoPlusResponse

    if (data.code !== undefined && data.code !== 1) {
      console.warn(`[GoPlus] API error: ${data.message}`)
      return { success: false, holders: null, security: null }
    }

    // GoPlus returns address keys in lowercase
    const record = data.result?.[address.toLowerCase()] ?? null

    if (!record) {
      console.log(`[GoPlus] No security data for ${address}`)
      return { success: true, holders: null, security: null }
    }

    return {
      success: true,
      holders: buildHolderData(record),
      security: buildSecurityData(record),
    }
  } catch (error) {
    console.error('[GoPlus] Fetch failed:', error)
    return { success: false, holders: null, security: null }
  }
}

function buildHolderData(record: GoPlusSecurityRecord): MarketContext['holders'] {
  const total = toNumber(record.holder_count)
  const top10Rate = toNumber(record.top10_holder_rate)

  if (total === null && top10Rate === null) {
    return null
  }

  return {
    total: total ?? undefined,
    // GoPlus returns rate as decimal (0-1), convert to percentage
    top10_percent: top10Rate !== null ? top10Rate * 100 : undefined,
  }
}

function buildSecurityData(record: GoPlusSecurityRecord): MarketContext['security'] {
  return {
    is_honeypot: record.is_honeypot === '1',
    is_open_source: record.is_open_source === '1',
    has_proxy: record.is_proxy === '1' || record.proxy === '1',
    risk_level: calculateRiskLevel(record),
  }
}

function calculateRiskLevel(record: GoPlusSecurityRecord): 'low' | 'medium' | 'high' | 'unknown' {
  // Calculate risk based on multiple factors
  let riskScore = 0

  if (record.is_honeypot === '1') riskScore += 100 // Instant high risk
  if (record.is_open_source !== '1') riskScore += 30
  if (record.is_proxy === '1' || record.proxy === '1') riskScore += 20

  const top10Rate = toNumber(record.top10_holder_rate)
  if (top10Rate !== null && top10Rate > 0.5) riskScore += 25

  if (riskScore >= 50) return 'high'
  if (riskScore >= 20) return 'medium'
  if (riskScore > 0) return 'low'
  return 'unknown'
}

/**
 * Fetch with timeout using AbortController
 */
async function fetchWithTimeout(url: string, timeoutMs: number): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'Web3search/1.0',
      },
    })
    return response
  } finally {
    clearTimeout(timeoutId)
  }
}

/**
 * Safely convert a value to a number
 */
function toNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null

  const num = typeof value === 'string' ? Number(value) :
              typeof value === 'number' ? value : null

  if (num === null || !Number.isFinite(num)) return null
  return num
}

/**
 * Format a number with appropriate precision
 */
function formatNumber(value: number): string {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(2)}B`
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M`
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(2)}K`
  }
  if (value < 0.01) {
    return value.toExponential(4)
  }
  return value.toFixed(4)
}

/**
 * Format a percentage value
 */
function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

/**
 * Convert chain ID to human-readable name
 */
function chainIdToName(chainId: string): string {
  const names: Record<string, string> = {
    '1': 'Ethereum',
    '56': 'BNB Chain',
    '137': 'Polygon',
    '42161': 'Arbitrum',
    '10': 'Optimism',
    '43114': 'Avalanche',
    '8453': 'Base',
    'solana': 'Solana',
  }
  return names[chainId] ?? `Chain ${chainId}`
}
