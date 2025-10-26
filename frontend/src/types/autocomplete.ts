/**
 * 搜索自动补全类型定义
 */

export interface AutocompleteItem {
  coingecko_id: string
  symbol: string
  name: string
  market_cap_rank?: number
  thumb?: string
}

export interface AutocompleteResponse {
  results: AutocompleteItem[]
  count: number
}
