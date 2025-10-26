/**
 * 报告历史记录类型定义
 */

export interface ReportHistoryItem {
  /** 项目符号（如BTC, ETH） */
  symbol: string
  /** 报告标题 */
  title: string
  /** 查看时间戳 */
  timestamp: string
  /** 分享令牌（如果有） */
  shareToken?: string
  /** 报告类型 */
  reportType: 'quick_chat' | 'deep_research'
  /** 会话ID（Quick Chat） */
  conversationId?: string
}

export interface UseReportHistoryReturn {
  /** 历史记录列表 */
  history: ReportHistoryItem[]
  /** 添加历史记录 */
  addToHistory: (item: Omit<ReportHistoryItem, 'timestamp'>) => void
  /** 清空历史记录 */
  clearHistory: () => void
  /** 删除单条记录 */
  removeFromHistory: (timestamp: string) => void
}
