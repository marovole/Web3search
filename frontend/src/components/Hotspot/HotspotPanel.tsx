/**
 * 市场热点展示面板
 * 显示当前最热门的加密货币项目
 */

import React, { useState, useEffect } from 'react'
import { getHotspots } from '../../services/api'
import type { HotspotItem } from '../../types/hotspot'
import { formatPrice, formatPriceChange } from '../../lib/safeFormatters'

interface HotspotPanelProps {
  onSelectHotspot?: (symbol: string, name: string) => void
}

const HotspotPanel: React.FC<HotspotPanelProps> = ({ onSelectHotspot }) => {
  const [hotspots, setHotspots] = useState<HotspotItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    loadHotspots()
  }, [])

  const loadHotspots = async () => {
    try {
      setLoading(true)
      const response = await getHotspots(10, false)
      setHotspots(response.hotspots)
      setError(null)
    } catch (err) {
      setError('加载热点失败')
      console.error('Failed to load hotspots:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    try {
      setLoading(true)
      const response = await getHotspots(10, true) // 强制刷新
      setHotspots(response.hotspots)
      setError(null)
    } catch (err) {
      setError('刷新失败')
    } finally {
      setLoading(false)
    }
  }

  const handleHotspotClick = (hotspot: HotspotItem) => {
    if (onSelectHotspot) {
      onSelectHotspot(hotspot.symbol, hotspot.name)
    }
  }

  if (loading && hotspots.length === 0) {
    return (
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            🔥 市场热点
          </h3>
        </div>
        <div className="text-center py-4 text-gray-500">
          加载中...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            🔥 市场热点
          </h3>
          <button
            onClick={handleRefresh}
            className="text-sm text-primary hover:text-blue-700 font-medium"
          >
            重试
          </button>
        </div>
        <div className="text-center py-4 text-red-600">
          {error}
        </div>
      </div>
    )
  }

  const displayHotspots = showAll ? hotspots : hotspots.slice(0, 5)

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mb-4 no-print">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          🔥 市场热点
          <span className="text-xs font-normal text-gray-500">
            每小时更新
          </span>
        </h3>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="text-sm text-primary hover:text-blue-700 font-medium disabled:opacity-50"
        >
          {loading ? '刷新中...' : '刷新'}
        </button>
      </div>

      {/* 热点列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-2">
        {displayHotspots.map((hotspot) => (
          <button
            key={hotspot.coin_id}
            onClick={() => handleHotspotClick(hotspot)}
            className="bg-white rounded-lg p-3 hover:shadow-md transition-shadow text-left border border-gray-200 hover:border-primary"
          >
            {/* 排名和名称 */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-500">
                  #{hotspot.market_cap_rank}
                </span>
                <span className="font-semibold text-gray-900">
                  {hotspot.symbol}
                </span>
              </div>
              {/* 热度分数 */}
              <span className="text-xs font-semibold text-orange-600 bg-orange-100 px-2 py-0.5 rounded">
                {hotspot.total_score?.toFixed(0) ?? 'N/A'}
              </span>
            </div>

            {/* 价格和变化 */}
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-medium text-gray-700">
                {formatPrice(hotspot.price_usd)}
              </span>
              <span className="text-xs">
                {formatPriceChange(hotspot.price_change_24h)}
              </span>
            </div>

            {/* 项目名称 */}
            <div className="text-xs text-gray-500 truncate mt-1">
              {hotspot.name}
            </div>
          </button>
        ))}
      </div>

      {/* 展开/收起按钮 */}
      {hotspots.length > 5 && (
        <div className="mt-3 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-sm text-primary hover:text-blue-700 font-medium"
          >
            {showAll ? '收起 ↑' : `查看更多 (${hotspots.length - 5}) ↓`}
          </button>
        </div>
      )}
    </div>
  )
}

export default HotspotPanel
