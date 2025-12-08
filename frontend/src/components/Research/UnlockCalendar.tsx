/**
 * Unlock Calendar Component
 *
 * A vertical timeline showing token vesting schedule including next unlock
 * date and monthly sell pressure. Part of the Red Flag Dashboard.
 *
 * @module components/Research/UnlockCalendar
 */

import { motion } from 'framer-motion'
import { Calendar, TrendingDown, Clock, AlertTriangle } from 'lucide-react'

// ============================================================================
// Types
// ============================================================================

export interface VestingData {
  /** Next major unlock date/description */
  next_unlock?: string
  /** Monthly sell pressure estimate */
  monthly_sell_pressure?: string
  /** Additional findings text */
  findings?: string
}

export interface UnlockCalendarProps {
  /** Vesting schedule data */
  vesting?: VestingData
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

// ============================================================================
// Subcomponents
// ============================================================================

interface TimelineItemProps {
  icon: React.ReactNode
  label: string
  value: string
  variant?: 'default' | 'warning' | 'danger'
  delay?: number
}

function TimelineItem({
  icon,
  label,
  value,
  variant = 'default',
  delay = 0,
}: TimelineItemProps) {
  const variantStyles = {
    default: {
      dot: 'bg-terminal-cyan',
      line: 'border-terminal-cyan/30',
      text: 'text-foreground',
    },
    warning: {
      dot: 'bg-terminal-amber',
      line: 'border-terminal-amber/30',
      text: 'text-terminal-amber',
    },
    danger: {
      dot: 'bg-terminal-red',
      line: 'border-terminal-red/30',
      text: 'text-terminal-red',
    },
  }[variant]

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      className="flex items-start gap-3 relative"
    >
      {/* Timeline dot and line */}
      <div className="flex flex-col items-center">
        <div
          className={`w-3 h-3 rounded-full ${variantStyles.dot} flex-shrink-0 z-10`}
        />
        <div
          className={`w-px h-full min-h-[40px] border-l-2 border-dashed ${variantStyles.line}`}
        />
      </div>

      {/* Content */}
      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-muted-foreground">{icon}</span>
          <span className="text-xs text-muted-foreground uppercase tracking-wider">
            {label}
          </span>
        </div>
        <p className={`text-sm font-medium ${variantStyles.text}`}>{value}</p>
      </div>
    </motion.div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-start gap-3">
          <div className="w-3 h-3 rounded-full bg-surface-2" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-20 bg-surface-2 rounded" />
            <div className="h-5 w-32 bg-surface-2 rounded" />
          </div>
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function UnlockCalendar({
  vesting,
  isLoading = false,
  className = '',
}: UnlockCalendarProps) {
  if (isLoading) {
    return (
      <div className={`terminal-panel p-4 ${className}`}>
        <h3 className="text-sm font-mono text-muted-foreground mb-4">
          Vesting Schedule
        </h3>
        <LoadingSkeleton />
      </div>
    )
  }

  if (!vesting || (!vesting.next_unlock && !vesting.monthly_sell_pressure)) {
    return (
      <div className={`terminal-panel p-4 ${className}`}>
        <h3 className="text-sm font-mono text-muted-foreground mb-4">
          Vesting Schedule
        </h3>
        <div className="text-center py-6">
          <Clock className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
          <span className="text-muted-foreground text-sm">
            No vesting data available
          </span>
        </div>
      </div>
    )
  }

  // Determine sell pressure severity
  const sellPressureVariant = (() => {
    if (!vesting.monthly_sell_pressure) return 'default'
    const pressure = vesting.monthly_sell_pressure.toLowerCase()
    if (pressure.includes('high') || pressure.includes('>5%') || pressure.includes('>10%')) {
      return 'danger'
    }
    if (pressure.includes('medium') || pressure.includes('>2%') || pressure.includes('>3%')) {
      return 'warning'
    }
    return 'default'
  })()

  return (
    <div className={`terminal-panel p-4 ${className}`}>
      <h3 className="text-sm font-mono text-muted-foreground mb-4">
        Vesting Schedule
      </h3>

      <div className="pl-1">
        {/* Next Unlock */}
        {vesting.next_unlock && (
          <TimelineItem
            icon={<Calendar className="w-3.5 h-3.5" />}
            label="Next Unlock"
            value={vesting.next_unlock}
            variant="warning"
            delay={0}
          />
        )}

        {/* Monthly Sell Pressure */}
        {vesting.monthly_sell_pressure && (
          <TimelineItem
            icon={<TrendingDown className="w-3.5 h-3.5" />}
            label="Monthly Sell Pressure"
            value={vesting.monthly_sell_pressure}
            variant={sellPressureVariant}
            delay={0.1}
          />
        )}

        {/* Findings (if available) */}
        {vesting.findings && (
          <TimelineItem
            icon={<AlertTriangle className="w-3.5 h-3.5" />}
            label="Analysis"
            value={vesting.findings}
            variant="default"
            delay={0.2}
          />
        )}
      </div>

      {/* Summary Footer */}
      {sellPressureVariant !== 'default' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className={`mt-4 pt-3 border-t border-border/50 text-xs ${
            sellPressureVariant === 'danger'
              ? 'text-terminal-red'
              : 'text-terminal-amber'
          }`}
        >
          {sellPressureVariant === 'danger' ? (
            <span className="flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              High unlock pressure may impact price
            </span>
          ) : (
            <span className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              Monitor upcoming unlock events
            </span>
          )}
        </motion.div>
      )}
    </div>
  )
}

export default UnlockCalendar
