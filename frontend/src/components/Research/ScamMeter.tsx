/**
 * Scam Meter Component
 *
 * A semi-circular gauge displaying the risk score (0-100) with color-coded
 * rating and red flags list. Visual indicator for tokenomics risk assessment.
 *
 * @module components/Research/ScamMeter
 */

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import type { TokenomicsScorecard } from '@/types/deep-research'

// ============================================================================
// Types
// ============================================================================

export interface ScamMeterProps {
  /** Risk scorecard data */
  scorecard?: TokenomicsScorecard
  /** List of identified red flags */
  redFlags?: string[]
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

// ============================================================================
// Constants
// ============================================================================

const GAUGE_CONFIG = {
  /** SVG viewbox dimensions */
  width: 200,
  height: 120,
  /** Gauge arc parameters */
  radius: 80,
  strokeWidth: 12,
  /** Center point */
  cx: 100,
  cy: 100,
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Calculate the stroke-dasharray and stroke-dashoffset for the gauge arc
 */
function calculateArcPath(score: number): { dashArray: string; dashOffset: number } {
  // Semi-circle arc length (half circumference)
  const arcLength = Math.PI * GAUGE_CONFIG.radius
  // Score mapped to arc position (0 = left, 100 = right)
  const filledLength = (score / 100) * arcLength
  return {
    dashArray: `${arcLength} ${arcLength}`,
    dashOffset: arcLength - filledLength,
  }
}

/**
 * Get color based on score value
 */
function getScoreColor(score: number): string {
  if (score <= 40) return '#2DD4BF' // terminal-green
  if (score <= 70) return '#F5A623' // terminal-amber
  return '#EF4444' // terminal-red
}

/**
 * Get background gradient stops for the gauge track
 */
function getGradientStops(): { offset: string; color: string }[] {
  return [
    { offset: '0%', color: '#2DD4BF' },
    { offset: '40%', color: '#2DD4BF' },
    { offset: '50%', color: '#F5A623' },
    { offset: '70%', color: '#F5A623' },
    { offset: '85%', color: '#EF4444' },
    { offset: '100%', color: '#EF4444' },
  ]
}

// ============================================================================
// Subcomponents
// ============================================================================

interface GaugeSVGProps {
  score: number
}

function GaugeSVG({ score }: GaugeSVGProps) {
  const { cx, cy, radius, strokeWidth, width, height } = GAUGE_CONFIG
  const { dashArray, dashOffset } = useMemo(() => calculateArcPath(score), [score])
  const arcColor = useMemo(() => getScoreColor(score), [score])
  const gradientStops = useMemo(() => getGradientStops(), [])

  // SVG arc path for semi-circle (180 degrees, from left to right)
  const arcPath = `M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full max-w-[200px]"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="gauge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          {gradientStops.map((stop, idx) => (
            <stop key={idx} offset={stop.offset} stopColor={stop.color} />
          ))}
        </linearGradient>
      </defs>

      {/* Background track */}
      <path
        d={arcPath}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        className="text-surface-3"
      />

      {/* Gradient overlay for reference */}
      <path
        d={arcPath}
        fill="none"
        stroke="url(#gauge-gradient)"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        opacity={0.2}
      />

      {/* Filled arc */}
      <motion.path
        d={arcPath}
        fill="none"
        stroke={arcColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={dashArray}
        initial={{ strokeDashoffset: Math.PI * radius }}
        animate={{ strokeDashoffset: dashOffset }}
        transition={{ duration: 1, ease: 'easeOut' }}
      />

      {/* Score text */}
      <text
        x={cx}
        y={cy - 10}
        textAnchor="middle"
        className="fill-foreground font-mono text-3xl font-bold"
      >
        {score}
      </text>
      <text
        x={cx}
        y={cy + 10}
        textAnchor="middle"
        className="fill-muted-foreground text-xs"
      >
        / 100
      </text>

      {/* Min/Max labels */}
      <text
        x={cx - radius - 5}
        y={cy + 15}
        textAnchor="middle"
        className="fill-terminal-green text-xs font-mono"
      >
        0
      </text>
      <text
        x={cx + radius + 5}
        y={cy + 15}
        textAnchor="middle"
        className="fill-terminal-red text-xs font-mono"
      >
        100
      </text>
    </svg>
  )
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="w-full max-w-[200px] h-[120px] bg-surface-2 rounded-full mx-auto" />
      <div className="h-6 w-24 bg-surface-2 rounded mx-auto mt-3" />
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function ScamMeter({
  scorecard,
  redFlags = [],
  isLoading = false,
  className = '',
}: ScamMeterProps) {
  if (isLoading) {
    return (
      <div className={`terminal-panel p-4 ${className}`}>
        <h3 className="text-sm font-mono text-muted-foreground mb-4">Risk Score</h3>
        <LoadingSkeleton />
      </div>
    )
  }

  if (!scorecard) {
    return (
      <div className={`terminal-panel p-4 ${className}`}>
        <h3 className="text-sm font-mono text-muted-foreground mb-4">Risk Score</h3>
        <div className="text-center py-6">
          <span className="text-muted-foreground text-sm">No data available</span>
        </div>
      </div>
    )
  }

  const ratingColor = {
    'Ponzi Risk': 'text-terminal-red',
    'Speculative': 'text-terminal-amber',
    'Sustainable': 'text-terminal-green',
  }[scorecard.rating]

  const ratingBg = {
    'Ponzi Risk': 'bg-terminal-red/10 border-terminal-red/30',
    'Speculative': 'bg-terminal-amber/10 border-terminal-amber/30',
    'Sustainable': 'bg-terminal-green/10 border-terminal-green/30',
  }[scorecard.rating]

  return (
    <div className={`terminal-panel p-4 ${className}`}>
      <h3 className="text-sm font-mono text-muted-foreground mb-4">Risk Score</h3>

      {/* Gauge */}
      <div className="flex justify-center mb-4">
        <GaugeSVG score={scorecard.score} />
      </div>

      {/* Rating Badge */}
      <div className="flex justify-center mb-4">
        <span
          className={`px-3 py-1 rounded-full border text-sm font-medium ${ratingBg} ${ratingColor}`}
        >
          {scorecard.rating}
        </span>
      </div>

      {/* Red Flags */}
      {redFlags.length > 0 && (
        <div className="mt-4 pt-4 border-t border-border/50">
          <h4 className="text-xs font-mono text-terminal-red mb-2 uppercase tracking-wider">
            Red Flags ({redFlags.length})
          </h4>
          <ul className="space-y-1.5">
            {redFlags.slice(0, 5).map((flag, idx) => (
              <motion.li
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-start gap-2 text-sm"
              >
                <span className="text-terminal-red flex-shrink-0">&bull;</span>
                <span className="text-foreground/90">{flag}</span>
              </motion.li>
            ))}
            {redFlags.length > 5 && (
              <li className="text-xs text-muted-foreground pl-4">
                +{redFlags.length - 5} more flags
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}

export default ScamMeter
