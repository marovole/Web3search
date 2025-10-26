/**
 * 热点数据类型定义
 */

export interface ScoresBreakdown {
  twitter: number
  reddit: number
  price: number
  volume: number
  news: number
}

export interface HotspotItem {
  coin_id: string
  symbol: string
  name: string
  market_cap_rank: number
  price_usd?: number
  price_change_24h?: number
  volume_24h?: number
  total_score: number
  scores_breakdown: ScoresBreakdown
  timestamp: string
}

export interface HotspotsResponse {
  hotspots: HotspotItem[]
  count: number
  updated_at: string
}
