import React from 'react'
import { motion } from 'framer-motion'
import { Zap, Search, Clock, FileText } from 'lucide-react'
import type { ChatMode } from '../../types'
import { cn } from '@/lib/utils'

interface ModeSwitchProps {
  mode: ChatMode
  onChange: (mode: ChatMode) => void
}

const ModeSwitch: React.FC<ModeSwitchProps> = ({ mode, onChange }) => {
  return (
    <div className="flex flex-col gap-4">
      {/* Segmented Control - Premium Style */}
      <div className="inline-flex bg-surface-2/50 p-1 rounded-xl border border-border/40 backdrop-blur-sm relative overflow-hidden">
        {/* Animated Background Pill */}
        <motion.div
          layoutId="mode-pill"
          className={cn(
            "absolute inset-y-1 rounded-lg",
            "bg-gradient-to-r from-card to-card/80",
            "border border-primary/20 shadow-terminal"
          )}
          style={{
            left: mode === 'quick' ? '4px' : 'calc(50% + 2px)',
            width: 'calc(50% - 6px)',
          }}
          transition={{ type: "spring", stiffness: 500, damping: 35 }}
        />

        {/* Quick Chat Button */}
        <button
          onClick={() => onChange('quick')}
          className={cn(
            "relative flex items-center gap-2.5 px-5 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 z-10",
            "flex-1 justify-center",
            mode === 'quick' 
              ? "text-foreground" 
              : "text-muted-foreground hover:text-foreground/80"
          )}
        >
          <Zap className={cn(
            "w-4 h-4 transition-all duration-200",
            mode === 'quick' ? "text-secondary fill-secondary drop-shadow-[0_0_4px_rgba(245,166,35,0.5)]" : ""
          )} />
          <span className="font-mono font-medium">Quick</span>
        </button>

        {/* Deep Research Button */}
        <button
          onClick={() => onChange('deep')}
          className={cn(
            "relative flex items-center gap-2.5 px-5 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 z-10",
            "flex-1 justify-center",
            mode === 'deep' 
              ? "text-foreground" 
              : "text-muted-foreground hover:text-foreground/80"
          )}
        >
          <Search className={cn(
            "w-4 h-4 transition-all duration-200",
            mode === 'deep' ? "text-primary drop-shadow-[0_0_4px_rgba(45,212,191,0.5)]" : ""
          )} />
          <span className="font-mono font-medium">Deep Research</span>
        </button>
      </div>

      {/* Mode Info - Enhanced */}
      <motion.div
        key={mode}
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex items-center gap-3 text-[11px] font-mono"
      >
        {mode === 'quick' ? (
          <>
            <span className="flex items-center gap-1.5 text-secondary/90">
              <Clock className="w-3 h-3" />
              ~3s
            </span>
            <span className="w-1 h-1 rounded-full bg-border" />
            <span className="text-muted-foreground/60">General queries & quick answers</span>
          </>
        ) : (
          <>
            <span className="flex items-center gap-1.5 text-primary/90">
              <FileText className="w-3 h-3" />
              Full Report
            </span>
            <span className="w-1 h-1 rounded-full bg-border" />
            <span className="text-muted-foreground/60">On-chain + Sentiment + Technical</span>
          </>
        )}
      </motion.div>
    </div>
  )
}

export default ModeSwitch
