import React from 'react'
import type { Recommendation } from '../../hooks/useRecommendations'

interface RecommendationCardProps {
  recommendation: Recommendation
  onLike: (id: string) => void
  onDislike: (id: string) => void
  onDismiss: (id: string) => void
  onClick?: (id: string) => void
}

const typeLabels: Record<string, { label: string; color: string }> = {
  trending: { label: '热门趋势', color: 'bg-orange-100 text-orange-700' },
  undervalued: { label: '价值洼地', color: 'bg-green-100 text-green-700' },
  new_listing: { label: '新上市', color: 'bg-purple-100 text-purple-700' },
  sector_match: { label: '行业匹配', color: 'bg-blue-100 text-blue-700' },
  similar_to_holdings: { label: '相似持仓', color: 'bg-cyan-100 text-cyan-700' },
  high_potential: { label: '高潜力', color: 'bg-yellow-100 text-yellow-700' },
  recovery_play: { label: '抄底机会', color: 'bg-red-100 text-red-700' },
  ai_picked: { label: 'AI 精选', color: 'bg-indigo-100 text-indigo-700' }
}

const riskLabels: Record<string, { label: string; color: string }> = {
  low: { label: '低风险', color: 'text-green-600' },
  medium: { label: '中风险', color: 'text-yellow-600' },
  high: { label: '高风险', color: 'text-orange-600' },
  very_high: { label: '极高风险', color: 'text-red-600' }
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onLike,
  onDislike,
  onDismiss,
  onClick
}) => {
  const typeInfo = typeLabels[recommendation.recommendation_type] || { label: recommendation.recommendation_type, color: 'bg-gray-100 text-gray-700' }
  const riskInfo = riskLabels[recommendation.risk_level] || { label: recommendation.risk_level, color: 'text-gray-600' }
  
  const formatPrice = (price?: number) => {
    if (!price) return '--'
    if (price < 0.01) return `$${price.toFixed(6)}`
    if (price < 1) return `$${price.toFixed(4)}`
    return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatMarketCap = (cap?: number) => {
    if (!cap) return '--'
    if (cap >= 1_000_000_000) return `$${(cap / 1_000_000_000).toFixed(2)}B`
    if (cap >= 1_000_000) return `$${(cap / 1_000_000).toFixed(2)}M`
    return `$${cap.toLocaleString()}`
  }

  const hasUserFeedback = !!recommendation.user_feedback

  return (
    <div 
      className={`bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all overflow-hidden ${onClick ? 'cursor-pointer' : ''}`}
      onClick={() => onClick?.(recommendation.id)}
    >
      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            {recommendation.logo_url ? (
              <img 
                src={recommendation.logo_url} 
                alt={recommendation.symbol} 
                className="w-12 h-12 rounded-full bg-gray-50"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center text-indigo-600 font-bold">
                {recommendation.symbol.slice(0, 2)}
              </div>
            )}
            <div>
              <h3 className="font-bold text-gray-900 text-lg">{recommendation.symbol}</h3>
              <p className="text-sm text-gray-500">{recommendation.name}</p>
            </div>
          </div>
          
          <div className="flex flex-col items-end gap-2">
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${typeInfo.color}`}>
              {typeInfo.label}
            </span>
            <div className="flex items-center gap-1">
              <span className="text-xs text-gray-500">置信度</span>
              <span className="text-sm font-semibold text-indigo-600">{recommendation.confidence_score}%</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="text-xs text-gray-500 mb-1">当前价格</div>
            <div className="font-mono font-medium text-gray-900">
              {formatPrice(recommendation.market_data.current_price)}
            </div>
            {recommendation.market_data.price_change_24h !== undefined && (
              <div className={`text-xs ${recommendation.market_data.price_change_24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {recommendation.market_data.price_change_24h >= 0 ? '+' : ''}
                {recommendation.market_data.price_change_24h.toFixed(2)}% (24h)
              </div>
            )}
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">市值</div>
            <div className="font-medium text-gray-900">
              {formatMarketCap(recommendation.market_data.market_cap)}
            </div>
            {recommendation.market_data.market_cap_rank && (
              <div className="text-xs text-gray-500">
                排名 #{recommendation.market_data.market_cap_rank}
              </div>
            )}
          </div>
        </div>

        {recommendation.match_reasons.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-500 mb-2">推荐理由</div>
            <div className="flex flex-wrap gap-2">
              {recommendation.match_reasons.slice(0, 3).map((reason, i) => (
                <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                  {reason}
                </span>
              ))}
            </div>
          </div>
        )}

        {recommendation.ai_analysis && (
          <div className="mb-4 p-3 bg-indigo-50 rounded-lg">
            <div className="text-xs font-medium text-indigo-700 mb-1">AI 分析</div>
            <p className="text-sm text-gray-700">{recommendation.ai_analysis}</p>
          </div>
        )}

        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex items-center gap-4 text-xs">
            <span className={riskInfo.color}>{riskInfo.label}</span>
            {recommendation.potential_upside && (
              <span className="text-green-600">
                潜在涨幅 +{recommendation.potential_upside}%
              </span>
            )}
            {recommendation.time_horizon && (
              <span className="text-gray-500">{recommendation.time_horizon}</span>
            )}
          </div>
        </div>
      </div>

      {!hasUserFeedback && (
        <div className="px-5 py-3 bg-gray-50 flex items-center justify-between border-t border-gray-100">
          <span className="text-xs text-gray-500">这个推荐对你有帮助吗？</span>
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => { e.stopPropagation(); onLike(recommendation.id); }}
              className="p-2 rounded-full hover:bg-green-100 text-gray-400 hover:text-green-600 transition-colors"
              title="喜欢"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDislike(recommendation.id); }}
              className="p-2 rounded-full hover:bg-red-100 text-gray-400 hover:text-red-600 transition-colors"
              title="不喜欢"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
              </svg>
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDismiss(recommendation.id); }}
              className="p-2 rounded-full hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-colors"
              title="不再显示"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {hasUserFeedback && (
        <div className="px-5 py-3 bg-gray-50 border-t border-gray-100">
          <span className={`text-xs ${recommendation.user_feedback === 'like' ? 'text-green-600' : 'text-gray-500'}`}>
            {recommendation.user_feedback === 'like' ? '已喜欢' : 
             recommendation.user_feedback === 'dislike' ? '已标记为不感兴趣' : 
             '已反馈'}
          </span>
        </div>
      )}
    </div>
  )
}

export default RecommendationCard
