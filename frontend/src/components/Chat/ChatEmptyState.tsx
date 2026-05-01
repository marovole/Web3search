import React from 'react'
import { motion } from 'framer-motion'
import { Terminal, Zap, Search, ArrowRight } from 'lucide-react'
import type { ChatMode } from '../../types'
import ModeSwitch from './ModeSwitch'
import HotspotPanel from '../Hotspot/HotspotPanel'
import { cn } from '@/lib/utils'

export interface ChatEmptyStateProps {
  mode: ChatMode
  onModeChange: (mode: ChatMode) => void
  onQuickFill: (value: string) => void
}

/**
 * Lazy-loaded welcome / hero surface for chat (framer-motion + HotspotPanel).
 * Keeps the main ChatInterface bundle free of these deps until first paint of empty state.
 */
export default function ChatEmptyState({
  mode,
  onModeChange,
  onQuickFill,
}: ChatEmptyStateProps) {
  return (
    <div className="min-h-[75vh] flex flex-col justify-center py-8 transition-opacity duration-300">
      <div className="w-full max-w-4xl mx-auto px-4 relative">
        <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-secondary/5 rounded-full blur-3xl" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, ease: [0.19, 1, 0.22, 1] }}
          className="mb-8 flex items-center gap-3"
        >
          <span className="terminal-tag">
            <Terminal className="w-3 h-3" />
            WEB3 INTELLIGENCE
          </span>
          <span className="flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground/50">
            <span className="status-dot status-dot-live" />
            LIVE
          </span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.6, ease: [0.19, 1, 0.22, 1] }}
          className="mb-10"
        >
          <h1 className="font-display text-display-xl text-foreground mb-6 tracking-tight">
            <motion.span
              className="block"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              Research.
            </motion.span>
            <motion.span
              className="block gradient-text-premium"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              Analyze.
            </motion.span>
            <motion.span
              className="block text-muted-foreground/70"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4, duration: 0.5 }}
            >
              Discover.
            </motion.span>
          </h1>
          <p className="text-base md:text-lg text-muted-foreground max-w-xl font-sans leading-relaxed">
            AI-powered deep research for crypto markets.
            <span className="text-foreground/80"> Real-time insights</span>,
            <span className="text-primary/80"> on-chain analysis</span>, and
            <span className="text-secondary/80"> sentiment data</span>.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, ease: [0.19, 1, 0.22, 1] }}
          className="mb-12"
        >
          <ModeSwitch mode={mode} onChange={onModeChange} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, ease: [0.19, 1, 0.22, 1] }}
          className="mb-12"
        >
          <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-muted-foreground/50 mb-4 flex items-center gap-2">
            <span className="w-8 h-px bg-border" />
            Quick Start
          </p>
          <div className="flex flex-wrap gap-2.5">
            {[
              { label: 'BTC Analysis', icon: <Zap className="w-3.5 h-3.5" /> },
              { label: 'ETH Sentiment', icon: <Search className="w-3.5 h-3.5" /> },
              { label: 'SOL Ecosystem', icon: <ArrowRight className="w-3.5 h-3.5" /> },
            ].map((item, i) => (
              <motion.button
                key={item.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.55 + i * 0.08, ease: [0.19, 1, 0.22, 1] }}
                type="button"
                onClick={() => onQuickFill(item.label)}
                className={cn(
                  'group inline-flex items-center gap-2.5 px-4 py-2',
                  'font-mono text-sm text-muted-foreground',
                  'bg-surface-2/50 border border-border/40 rounded-xl',
                  'hover:border-primary/40 hover:text-foreground hover:bg-primary/[0.06]',
                  'hover:shadow-glow-sm active:scale-[0.97]',
                  'transition-all duration-250 ease-out-expo'
                )}
              >
                <span className="text-primary/70 group-hover:text-primary transition-colors">
                  {item.icon}
                </span>
                {item.label}
              </motion.button>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.65, duration: 0.5, ease: [0.19, 1, 0.22, 1] }}
        >
          <HotspotPanel
            onSelectHotspot={(symbol, name) => {
              onQuickFill(`${symbol} (${name})`)
            }}
          />
        </motion.div>
      </div>
    </div>
  )
}
