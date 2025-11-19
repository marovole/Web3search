/**
 * Market Hotspots Panel
 * Displays trending crypto projects with premium UI
 */

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TrendingUp, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
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
      <div className="w-full glass-card p-6 animate-pulse">
        <div className="h-6 w-32 bg-white/10 rounded mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-white/5 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  if (error && hotspots.length === 0) return null

  const displayHotspots = showAll ? hotspots : hotspots.slice(0, 5)

  return (
    <div className="w-full">
      <div className="relative flex items-center justify-center mb-6 px-2">
        <div className="flex items-center gap-2 text-foreground/90">
          <TrendingUp className="w-5 h-5 text-orange-500" />
          <h3 className="font-semibold tracking-wide text-lg">Market Hotspots</h3>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className={cn(
            "absolute right-0 p-2 rounded-full hover:bg-secondary/50 transition-colors text-muted-foreground hover:text-primary",
            loading && "animate-spin"
          )}
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <AnimatePresence mode='popLayout'>
          {displayHotspots.map((hotspot, index) => (
            <motion.button
              key={hotspot.coin_id}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
              onClick={() => onSelectHotspot?.(hotspot.symbol, hotspot.name)}
              className="group relative flex flex-col p-4 rounded-2xl bg-card/50 border border-border/50 hover:border-primary/30 hover:bg-card/80 transition-all duration-300 text-left overflow-hidden shadow-sm hover:shadow-md"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              <div className="relative z-10 w-full">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-muted-foreground/70 bg-secondary/50 px-1.5 py-0.5 rounded">#{hotspot.market_cap_rank}</span>
                    <span className="font-bold text-foreground group-hover:text-primary transition-colors">{hotspot.symbol}</span>
                  </div>
                  <div className={cn(
                    "text-xs font-medium px-2 py-0.5 rounded-full",
                    (hotspot.price_change_24h ?? 0) >= 0
                      ? "bg-green-500/10 text-green-500"
                      : "bg-red-500/10 text-red-500"
                  )}>
                    {formatPriceChange(hotspot.price_change_24h ?? 0)}
                  </div>
                </div>

                <div className="flex justify-between items-end">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs text-muted-foreground truncate max-w-[80px]">{hotspot.name}</span>
                    <span className="text-sm font-medium text-foreground/90">{formatPrice(hotspot.price_usd)}</span>
                  </div>
                  <div className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-500 border border-orange-500/20">
                    {formatScore(hotspot.total_score, 0, 'N/A')}
                  </div>
                </div>
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>

      {hotspots.length > 5 && (
        <div className="flex justify-center mt-6">
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-primary transition-colors px-4 py-2 rounded-full hover:bg-secondary/50"
          >
            {showAll ? (
              <>Show Less <ChevronUp className="w-3 h-3" /></>
            ) : (
              <>View All ({hotspots.length}) <ChevronDown className="w-3 h-3" /></>
            )}
          </button>
        </div>
      )}
    </div>
  )
}

export default HotspotPanel
