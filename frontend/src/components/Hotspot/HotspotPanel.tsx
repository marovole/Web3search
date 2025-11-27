/**
 * Market Hotspots Panel
 * Terminal-style data table for trending crypto projects
 */

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, RefreshCw, ChevronDown, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react'
import { getHotspots } from '../../services/api'
import type { HotspotItem } from '../../types/hotspot'
import { formatPrice, formatPriceChange, formatScore } from '../../lib/safeFormatters'
import { cn } from '@/lib/utils'

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

      if (response?.hotspots && Array.isArray(response.hotspots)) {
        const validHotspots = response.hotspots.filter(h => h && h.symbol && h.name)
        setHotspots(validHotspots)
        setError(null)
      }
    } catch (err) {
      setError('Failed to load trending data')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setLoading(true)
    try {
      const response = await getHotspots(10, true)
      if (response?.hotspots && Array.isArray(response.hotspots)) {
        setHotspots(response.hotspots.filter(h => h && h.symbol && h.name))
        setError(null)
      }
    } catch (err) {
      setError('Refresh failed')
    } finally {
      setLoading(false)
    }
  }

  if (loading && hotspots.length === 0) {
    return (
      <div className="terminal-panel p-4">
        <div className="flex items-center gap-2 mb-4">
          <div className="h-4 w-4 bg-muted rounded animate-pulse" />
          <div className="h-4 w-32 bg-muted rounded animate-pulse" />
        </div>
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-10 bg-muted/30 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error && hotspots.length === 0) return null

  const displayHotspots = showAll ? hotspots : hotspots.slice(0, 5)

  return (
    <div className="terminal-panel overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3.5 border-b border-border/30 bg-surface-2/30">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            <span className="font-mono text-sm font-semibold text-foreground tracking-tight">MARKET_HOTSPOTS</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="status-dot status-dot-live" />
            <span className="terminal-tag-amber text-[9px] py-0.5">LIVE</span>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className={cn(
            "p-2 rounded-lg hover:bg-muted/40 transition-all duration-200 text-muted-foreground hover:text-primary",
            loading && "animate-spin"
          )}
          aria-label="Refresh data"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Table Header */}
      <div className="grid grid-cols-12 gap-2 px-4 py-2.5 text-[9px] font-mono uppercase tracking-[0.15em] text-muted-foreground/45 border-b border-border/20 bg-surface-1/50">
        <div className="col-span-1">#</div>
        <div className="col-span-3">Asset</div>
        <div className="col-span-3 text-right">Price</div>
        <div className="col-span-3 text-right">24h</div>
        <div className="col-span-2 text-right">Score</div>
      </div>

      {/* Data Rows */}
      <div className="divide-y divide-border/10">
        <AnimatePresence mode='popLayout'>
          {displayHotspots.map((hotspot, index) => {
            const isPositive = (hotspot.price_change_24h ?? 0) >= 0
            const isTopRank = hotspot.market_cap_rank <= 3
            
            return (
              <motion.button
                key={hotspot.coin_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.2, delay: index * 0.04, ease: [0.19, 1, 0.22, 1] }}
                onClick={() => onSelectHotspot?.(hotspot.symbol, hotspot.name)}
                className={cn(
                  "w-full grid grid-cols-12 gap-2 px-4 py-3.5 text-left relative",
                  "hover:bg-primary/[0.04] transition-all duration-150",
                  "group cursor-pointer"
                )}
              >
                {/* Hover indicator */}
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-0 bg-primary rounded-r transition-all duration-200 group-hover:h-1/2" />

                {/* Rank */}
                <div className="col-span-1 flex items-center">
                  <span className={cn(
                    "rank-badge",
                    isTopRank && "rank-badge-top"
                  )}>
                    {hotspot.market_cap_rank}
                  </span>
                </div>

                {/* Asset */}
                <div className="col-span-3 flex items-center gap-2 min-w-0">
                  <span className="font-mono font-semibold text-foreground group-hover:text-primary transition-colors duration-150">
                    {hotspot.symbol}
                  </span>
                  <span className="text-xs text-muted-foreground/45 truncate hidden sm:inline">
                    {hotspot.name}
                  </span>
                </div>

                {/* Price */}
                <div className="col-span-3 flex items-center justify-end">
                  <span className="data-cell text-foreground/85">
                    {formatPrice(hotspot.price_usd)}
                  </span>
                </div>

                {/* 24h Change */}
                <div className="col-span-3 flex items-center justify-end gap-1.5">
                  {isPositive ? (
                    <TrendingUp className="w-3.5 h-3.5 text-terminal-green" />
                  ) : (
                    <TrendingDown className="w-3.5 h-3.5 text-terminal-red" />
                  )}
                  <span className={cn(
                    "data-cell font-medium",
                    isPositive ? "data-positive" : "data-negative"
                  )}>
                    {formatPriceChange(hotspot.price_change_24h ?? 0)}
                  </span>
                </div>

                {/* Score */}
                <div className="col-span-2 flex items-center justify-end">
                  <span className={cn(
                    "px-2.5 py-1 rounded-md text-xs font-mono font-semibold",
                    "bg-secondary/10 text-secondary border border-secondary/20",
                    "transition-all duration-150 group-hover:bg-secondary/15 group-hover:border-secondary/30"
                  )}>
                    {formatScore(hotspot.total_score, 0, '—')}
                  </span>
                </div>
              </motion.button>
            )
          })}
        </AnimatePresence>
      </div>

      {/* Footer - Show more/less */}
      {hotspots.length > 5 && (
        <div className="px-4 py-2.5 border-t border-border/20 bg-surface-1/30">
          <button
            onClick={() => setShowAll(!showAll)}
            className={cn(
              "w-full flex items-center justify-center gap-1.5 text-[10px] font-mono uppercase tracking-wider",
              "text-muted-foreground hover:text-primary transition-all duration-200 py-1.5 rounded-lg",
              "hover:bg-primary/[0.04]"
            )}
          >
            {showAll ? (
              <>
                <ChevronUp className="w-3.5 h-3.5" />
                COLLAPSE
              </>
            ) : (
              <>
                VIEW_ALL ({hotspots.length})
                <ChevronDown className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}

export default HotspotPanel
