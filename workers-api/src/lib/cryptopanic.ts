import type { Env } from '../types/env'

export interface CryptoPanicNews {
  id: number
  kind: 'news' | 'media'
  domain: string
  source: {
    title: string
    region: string
    domain: string
    path: string | null
  }
  title: string
  published_at: string
  slug: string
  currencies: Array<{
    code: string
    title: string
    slug: string
    url: string
  }> | null
  url: string
  created_at: string
  votes: {
    negative: number
    positive: number
    important: number
    liked: number
    disliked: number
    lol: number
    toxic: number
    saved: number
    comments: number
  }
}

export interface CryptoPanicResponse {
  count: number
  next: string | null
  previous: string | null
  results: CryptoPanicNews[]
}

export interface NewsFilter {
  currencies?: string[]
  regions?: string[]
  kind?: 'news' | 'media' | 'all'
  filter?: 'rising' | 'hot' | 'bullish' | 'bearish' | 'important' | 'saved' | 'lol'
  public?: boolean
}

const CRYPTOPANIC_API_BASE = 'https://cryptopanic.com/api/v1'

export async function fetchCryptoNews(
  env: Env,
  options: NewsFilter = {}
): Promise<CryptoPanicNews[]> {
  const apiKey = env.CRYPTOPANIC_API_KEY
  
  if (!apiKey) {
    console.warn('[CryptoPanic] API key not configured, using public feed')
    return fetchPublicFeed()
  }

  const params = new URLSearchParams({
    auth_token: apiKey,
    public: 'true'
  })

  if (options.currencies && options.currencies.length > 0) {
    params.set('currencies', options.currencies.join(','))
  }

  if (options.regions && options.regions.length > 0) {
    params.set('regions', options.regions.join(','))
  }

  if (options.kind && options.kind !== 'all') {
    params.set('kind', options.kind)
  }

  if (options.filter) {
    params.set('filter', options.filter)
  }

  try {
    const response = await fetch(`${CRYPTOPANIC_API_BASE}/posts/?${params}`, {
      headers: {
        'Accept': 'application/json'
      }
    })

    if (!response.ok) {
      console.error('[CryptoPanic] API error:', response.status)
      return []
    }

    const data: CryptoPanicResponse = await response.json()
    return data.results || []
  } catch (error) {
    console.error('[CryptoPanic] Fetch error:', error)
    return []
  }
}

async function fetchPublicFeed(): Promise<CryptoPanicNews[]> {
  try {
    const response = await fetch(`${CRYPTOPANIC_API_BASE}/posts/?public=true`, {
      headers: { 'Accept': 'application/json' }
    })

    if (!response.ok) {
      return []
    }

    const data: CryptoPanicResponse = await response.json()
    return data.results || []
  } catch {
    return []
  }
}

export async function fetchNewsForTokens(
  env: Env,
  tokenSymbols: string[]
): Promise<CryptoPanicNews[]> {
  if (tokenSymbols.length === 0) {
    return fetchCryptoNews(env, { filter: 'hot' })
  }

  const upperSymbols = tokenSymbols.map(s => s.toUpperCase())
  const news = await fetchCryptoNews(env, { currencies: upperSymbols })

  if (news.length === 0) {
    return fetchCryptoNews(env, { filter: 'hot' })
  }

  return news
}

export function filterRecentNews(
  news: CryptoPanicNews[],
  hoursAgo: number = 24
): CryptoPanicNews[] {
  const cutoff = Date.now() - hoursAgo * 60 * 60 * 1000
  
  return news.filter(item => {
    const publishedAt = new Date(item.published_at).getTime()
    return publishedAt >= cutoff
  })
}

export function sortNewsByImportance(news: CryptoPanicNews[]): CryptoPanicNews[] {
  return [...news].sort((a, b) => {
    const scoreA = a.votes.important * 3 + a.votes.positive * 2 + a.votes.liked - a.votes.negative - a.votes.toxic
    const scoreB = b.votes.important * 3 + b.votes.positive * 2 + b.votes.liked - b.votes.negative - b.votes.toxic
    return scoreB - scoreA
  })
}

export function getTopNews(
  news: CryptoPanicNews[],
  limit: number = 5
): CryptoPanicNews[] {
  const recent = filterRecentNews(news, 24)
  const sorted = sortNewsByImportance(recent)
  return sorted.slice(0, limit)
}

export function formatNewsForSummary(news: CryptoPanicNews[]): string {
  if (news.length === 0) {
    return '暂无相关新闻'
  }

  return news.map((item, index) => {
    const currencies = item.currencies?.map(c => c.code).join(', ') || '综合'
    const sentiment = getSentiment(item.votes)
    return `${index + 1}. [${currencies}] ${item.title} (${sentiment}) - ${item.source.title}`
  }).join('\n')
}

function getSentiment(votes: CryptoPanicNews['votes']): string {
  const positive = votes.positive + votes.liked + votes.important
  const negative = votes.negative + votes.toxic + votes.disliked
  
  if (positive > negative * 2) return '利好'
  if (negative > positive * 2) return '利空'
  return '中性'
}

export function extractMentionedTokens(news: CryptoPanicNews[]): string[] {
  const tokens = new Set<string>()
  
  for (const item of news) {
    if (item.currencies) {
      for (const currency of item.currencies) {
        tokens.add(currency.code.toUpperCase())
      }
    }
  }
  
  return Array.from(tokens)
}
