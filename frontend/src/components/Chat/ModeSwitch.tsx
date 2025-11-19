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
    <div className="flex flex-col items-center gap-4">
      <div className="relative flex bg-muted/50 p-1 rounded-xl border border-white/5 backdrop-blur-sm">
        {/* Sliding Background */}
        <motion.div
          className="absolute top-1 bottom-1 bg-primary rounded-lg shadow-lg shadow-primary/20"
          initial={false}
          animate={{
            x: mode === 'quick' ? 0 : '100%',
            width: 'calc(50% - 4px)'
          }}
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
          style={{ left: 4 }}
        />

        {/* Quick Chat Button */}
        <button
          onClick={() => onChange('quick')}
          className={cn(
            "relative z-10 flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-medium rounded-lg transition-colors duration-200 w-36",
            mode === 'quick' ? "text-primary-foreground" : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Zap className="w-4 h-4" />
          <span>Quick Chat</span>
        </button>

        {/* Deep Research Button */}
        <button
          onClick={() => onChange('deep')}
          className={cn(
            "relative z-10 flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-medium rounded-lg transition-colors duration-200 w-36",
            mode === 'deep' ? "text-primary-foreground" : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Search className="w-4 h-4" />
          <span>Deep Research</span>
        </button>
      </div>

      {/* Mode Description */}
      <motion.div
        key={mode}
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -5 }}
        className="text-xs font-medium text-muted-foreground/80 flex items-center gap-1.5 bg-muted/30 px-3 py-1 rounded-full border border-white/5"
      >
        {mode === 'quick' ? (
          <>
            <Zap className="w-3 h-3 text-primary" />
            <span>3s Instant Response</span>
          </>
        ) : (
          <>
            <Search className="w-3 h-3 text-secondary" />
            <span>Comprehensive Report</span>
          </>
        )}
      </motion.div>
    </div>
  )
}

export default ModeSwitch
