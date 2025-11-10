/**
 * CoinGecko API Client
 * Fetches real-time cryptocurrency price data
 */

export interface CoinGeckoPrice {
  symbol: string
  name: string
  price_usd: number
  price_change_24h: number
  market_cap: number
  market_cap_rank: number | null
}

export interface CoinGeckoError {
  error: string
  message: string
}

/**
 * CoinGecko API 客户端
 * 免费版 API，无需 API Key，每分钟限制 10-50 次请求
 */
export class CoinGeckoClient {
  private readonly baseUrl = 'https://api.coingecko.com/api/v3'
  private readonly timeout = 5000 // 5 seconds

  /**
   * 解析币种符号到 CoinGecko ID
   * 支持常见币种的符号映射
   */
  private resolveCoinId(symbol: string): string {
    const symbolMap: Record<string, string> = {
      btc: 'bitcoin',
      eth: 'ethereum',
      usdt: 'tether',
      bnb: 'binancecoin',
      sol: 'solana',
      xrp: 'ripple',
      usdc: 'usd-coin',
      ada: 'cardano',
      doge: 'dogecoin',
      trx: 'tron',
      dot: 'polkadot',
      matic: 'matic-network',
      dai: 'dai',
      shib: 'shiba-inu',
      avax: 'avalanche-2',
      link: 'chainlink',
      uni: 'uniswap',
      atom: 'cosmos',
      etc: 'ethereum-classic',
      xlm: 'stellar',
      bch: 'bitcoin-cash',
      ltc: 'litecoin',
      near: 'near',
      algo: 'algorand',
      fil: 'filecoin',
    }

    const normalized = symbol.toLowerCase().trim()
    return symbolMap[normalized] || normalized
  }

  /**
   * 从用户查询中提取币种符号
   */
  extractSymbol(query: string): string | null {
    const lowerQuery = query.toLowerCase()

    // 常见模式：Bitcoin, BTC, 比特币
    const patterns = [
      /\b(bitcoin|btc|比特币)\b/i,
      /\b(ethereum|eth|以太坊|以太币)\b/i,
      /\b(solana|sol)\b/i,
      /\b(bnb|币安币)\b/i,
      /\b(ripple|xrp|瑞波币)\b/i,
      /\b(cardano|ada|艾达币)\b/i,
      /\b(dogecoin|doge|狗狗币)\b/i,
      /\b(polkadot|dot|波卡)\b/i,
      /\b(avalanche|avax|雪崩)\b/i,
      /\b(chainlink|link)\b/i,
    ]

    for (const pattern of patterns) {
      const match = lowerQuery.match(pattern)
      if (match) {
        // 返回英文符号（优先）
        const term = match[1].toLowerCase()
        if (term.length <= 4) return term // 可能是符号
        // 映射中文到符号
        const cnMap: Record<string, string> = {
          '比特币': 'btc',
          '以太坊': 'eth',
          '以太币': 'eth',
          '币安币': 'bnb',
          '瑞波币': 'xrp',
          '艾达币': 'ada',
          '狗狗币': 'doge',
          '波卡': 'dot',
          '雪崩': 'avax',
        }
        return cnMap[term] || term
      }
    }

    return null
  }

  /**
   * 获取币种市场数据
   */
  async getCoinPrice(coinId: string): Promise<CoinGeckoPrice | CoinGeckoError> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), this.timeout)

      const response = await fetch(
        `${this.baseUrl}/coins/${coinId}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false`,
        {
          signal: controller.signal,
          headers: {
            'Accept': 'application/json',
          },
        }
      )

      clearTimeout(timeoutId)

      if (!response.ok) {
        if (response.status === 429) {
          return {
            error: 'RATE_LIMIT',
            message: 'CoinGecko API 请求过于频繁，请稍后重试',
          }
        }
        if (response.status === 404) {
          return {
            error: 'NOT_FOUND',
            message: `未找到币种: ${coinId}`,
          }
        }
        return {
          error: 'API_ERROR',
          message: `CoinGecko API 错误: ${response.status}`,
        }
      }

      const data = await response.json<any>()

      if (!data.market_data || !data.market_data.current_price) {
        return {
          error: 'NO_DATA',
          message: '未获取到市场数据',
        }
      }

      const priceUsd = data.market_data.current_price.usd
      if (priceUsd === undefined || priceUsd === null) {
        return {
          error: 'NO_PRICE',
          message: '未获取到美元价格',
        }
      }

      return {
        symbol: data.symbol?.toUpperCase() || '',
        name: data.name || coinId,
        price_usd: priceUsd,
        price_change_24h: data.market_data.price_change_percentage_24h || 0,
        market_cap: data.market_data.market_cap?.usd || 0,
        market_cap_rank: data.market_data.market_cap_rank || null,
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return {
          error: 'TIMEOUT',
          message: 'CoinGecko API 请求超时',
        }
      }
      return {
        error: 'UNKNOWN_ERROR',
        message: `获取价格数据失败: ${error}`,
      }
    }
  }

  /**
   * 从用户查询中自动检测并获取价格数据
   */
  async getPriceFromQuery(query: string): Promise<CoinGeckoPrice | null> {
    const symbol = this.extractSymbol(query)
    if (!symbol) return null

    const coinId = this.resolveCoinId(symbol)
    const result = await this.getCoinPrice(coinId)

    if ('error' in result) {
      console.warn(`CoinGecko error for ${symbol}:`, result.message)
      return null
    }

    return result
  }
}

/**
 * 创建 CoinGecko 客户端实例
 */
export function createCoinGeckoClient(): CoinGeckoClient {
  return new CoinGeckoClient()
}
