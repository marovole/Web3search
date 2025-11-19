import React from 'react'
import { motion } from 'framer-motion'
import { Zap, Search } from 'lucide-react'
import type { ChatMode } from '../../types'
import { cn } from '@/lib/utils'

interface ModeSwitchProps {
  mode: ChatMode
  onChange: (mode: ChatMode) => void
}

const ModeSwitch: React.FC<ModeSwitchProps> = ({ mode, onChange }) => {
  return (
    <div className="flex flex-col items-center gap-6">
      <div className="relative flex bg-secondary/30 p-1.5 rounded-full border border-border/50 backdrop-blur-md">
        {/* Sliding Background */}
        <motion.div
          className="absolute top-1.5 bottom-1.5 bg-background rounded-full shadow-sm border border-border/50"
          initial={false}
          animate={{
            x: mode === 'quick' ? 0 : '100%',
            width: 'calc(50% - 6px)'
          }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          style={{ left: 6 }}
        />

        {/* Quick Chat Button */}
        <button
          onClick={() => onChange('quick')}
          className={cn(
            "relative z-10 flex items-center justify-center gap-2 px-8 py-2.5 text-sm font-medium rounded-full transition-colors duration-200 w-40",
            mode === 'quick' ? "text-foreground" : "text-muted-foreground hover:text-foreground/80"
          )}
        >
          <Zap className={cn("w-4 h-4", mode === 'quick' ? "text-amber-500 fill-amber-500" : "text-muted-foreground")} />
          <span>Quick Chat</span>
        </button>

        {/* Deep Research Button */}
        <button
          onClick={() => onChange('deep')}
          className={cn(
            "relative z-10 flex items-center justify-center gap-2 px-8 py-2.5 text-sm font-medium rounded-full transition-colors duration-200 w-40",
            mode === 'deep' ? "text-foreground" : "text-muted-foreground hover:text-foreground/80"
          )}
        >
          <Search className={cn("w-4 h-4", mode === 'deep' ? "text-blue-500" : "text-muted-foreground")} />
          <span>Deep Research</span>
        </button>
      </div>

      {/* Mode Description */}
      <motion.div
        key={mode}
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -5 }}
        className="text-xs font-medium text-muted-foreground/80 flex items-center gap-2 bg-secondary/20 px-4 py-1.5 rounded-full border border-border/30"
      >
        {mode === 'quick' ? (
          <>
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            <span>3s Instant AI Response</span>
          </>
        ) : (
          <>
            <Search className="w-3.5 h-3.5 text-blue-500" />
            <span>Comprehensive Deep Research Report</span>
          </>
        )}
      </motion.div>
    </div>
  )
}

export default ModeSwitch
