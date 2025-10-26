/**
 * 项目监控列表类型定义
 */

export interface WatchlistItem {
  /** 项目符号（如BTC, ETH） */
  symbol: string
  /** 项目名称 */
  name: string
  /** 添加时间戳 */
  addedAt: string
  /** 项目图标URL（可选） */
  icon?: string
}

export interface UseWatchlistReturn {
  /** 监控列表 */
  watchlist: WatchlistItem[]
  /** 添加到监控列表 */
  addToWatchlist: (item: Omit<WatchlistItem, 'addedAt'>) => void
  /** 从监控列表移除 */
  removeFromWatchlist: (symbol: string) => void
  /** 检查是否在监控列表中 */
  isInWatchlist: (symbol: string) => boolean
  /** 清空监控列表 */
  clearWatchlist: () => void
}
