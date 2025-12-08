/**
 * Holder Distribution Component
 *
 * A donut chart displaying token allocation breakdown with centralization
 * risk indicator. Visualizes insider vs public token distribution.
 *
 * @module components/Research/HolderDistribution
 */

import { useMemo } from 'react'
import { motion } from 'framer-motion'

// ============================================================================
// Types
// ============================================================================

export interface HolderDistributionProps {
  /** Token allocation breakdown (category -> percentage) */
  breakdown?: Record<string, number>
  /** Centralization risk level */
  centralizationRisk?: 'Low' | 'Medium' | 'High'
  /** Insider ownership percentage */
  insiderPercentage?: number
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

// ============================================================================
// Constants
// ============================================================================

const CHART_CONFIG = {
  size: 160,
  radius: 60,
  strokeWidth: 20,
}

/** Color palette for pie segments */
const SEGMENT_COLORS = [
  '#2DD4BF', // terminal-green
  '#F5A623', // terminal-amber
  '#38BDF8', // terminal-cyan
  '#A78BFA', // terminal-purple
  '#EF4444', // terminal-red
  '#EC4899', // pink
  '#8B5CF6', // violet
  '#14B8A6', // teal
]

// ============================================================================
// Helpers
// ============================================================================

interface PieSegment {
  label: string
  value: number
  color: string
  startAngle: number
  endAngle: number
}

/**
 * Calculate pie chart segments from breakdown data
 */
function calculateSegments(breakdown: Record<string, number>): PieSegment[] {
  const entries = Object.entries(breakdown).filter(([, v]) => v > 0)
  const total = entries.reduce((sum, [, v]) => sum + v, 0)

  if (total === 0) return []

  let currentAngle = -90 // Start from top

  return entries.map(([label, value], idx) => {
    const percentage = (value / total) * 100
    const angle = (percentage / 100) * 360
    const segment: PieSegment = {
      label,
      value: percentage,
      color: SEGMENT_COLORS[idx % SEGMENT_COLORS.length] ?? '#2DD4BF',
      startAngle: currentAngle,
      endAngle: currentAngle + angle,
    }
    currentAngle += angle
    return segment
  })
}

/**
 * Convert polar coordinates to cartesian
 */
function polarToCartesian(
  cx: number,
  cy: number,
  radius: number,
  angleInDegrees: number
): { x: number; y: number } {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180
  return {
    x: cx + radius * Math.cos(angleInRadians),
    y: cy + radius * Math.sin(angleInRadians),
  }
}

/**
 * Generate SVG arc path
 */
function describeArc(
  cx: number,
  cy: number,
  radius: number,
  startAngle: number,
  endAngle: number
): string {
  const start = polarToCartesian(cx, cy, radius, endAngle)
  const end = polarToCartesian(cx, cy, radius, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'

  return [
    'M',
    start.x,
    start.y,
    'A',
    radius,
    radius,
    0,
    largeArcFlag,
    0,
    end.x,
    end.y,
  ].join(' ')
}

// ============================================================================
// Subcomponents
// ============================================================================

interface DonutChartProps {
  segments: PieSegment[]
}

function DonutChart({ segments }: DonutChartProps) {
  const { size, radius, strokeWidth } = CHART_CONFIG
  const cx = size / 2
  const cy = size / 2

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="w-full max-w-[160px]">
      {/* Background circle */}
      <circle
        cx={cx}
        cy={cy}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        className="text-surface-3"
      />

      {/* Segments */}
      {segments.map((segment, idx) => (
        <motion.path
          key={segment.label}
          d={describeArc(cx, cy, radius, segment.startAngle, segment.endAngle)}
          fill="none"
          stroke={segment.color}
          strokeWidth={strokeWidth}
          strokeLinecap="butt"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 0.5, delay: idx * 0.1 }}
        />
      ))}

      {/* Center text */}
      <text
        x={cx}
        y={cy - 5}
        textAnchor="middle"
        className="fill-muted-foreground text-xs font-mono"
      >
        Allocation
      </text>
      <text
        x={cx}
        y={cy + 12}
        textAnchor="middle"
        className="fill-foreground text-sm font-medium"
      >
        {segments.length} groups
      </text>
    </svg>
  )
}

interface LegendProps {
  segments: PieSegment[]
}

function Legend({ segments }: LegendProps) {
  return (
    <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 mt-3">
      {segments.slice(0, 6).map((segment) => (
        <div key={segment.label} className="flex items-center gap-2 min-w-0">
          <span
            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: segment.color }}
          />
          <span className="text-xs text-foreground/80 truncate">
            {segment.label}
          </span>
          <span className="text-xs text-muted-foreground font-mono flex-shrink-0">
            {segment.value.toFixed(1)}%
          </span>
        </div>
      ))}
      {segments.length > 6 && (
        <div className="col-span-2 text-xs text-muted-foreground">
          +{segments.length - 6} more categories
        </div>
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="w-[160px] h-[160px] bg-surface-2 rounded-full mx-auto" />
      <div className="grid grid-cols-2 gap-2 mt-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-4 bg-surface-2 rounded" />
        ))}
      </div>
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function HolderDistribution({
  breakdown,
  centralizationRisk,
  insiderPercentage,
  isLoading = false,
  className = '',
}: HolderDistributionProps) {
  const segments = useMemo(
    () => (breakdown ? calculateSegments(breakdown) : []),
    [breakdown]
  )

  if (isLoading) {
    return (
      <div className={`terminal-panel p-4 ${className}`}>
        <h3 className="text-sm font-mono text-muted-foreground mb-4">
          Token Allocation
        </h3>
        <LoadingSkeleton />
      </div>
    )
  }

  if (!breakdown || segments.length === 0) {
    return (
      <div className={`terminal-panel p-4 ${className}`}>
        <h3 className="text-sm font-mono text-muted-foreground mb-4">
          Token Allocation
        </h3>
        <div className="text-center py-6">
          <span className="text-muted-foreground text-sm">No data available</span>
        </div>
      </div>
    )
  }

  const riskColor = {
    Low: 'text-terminal-green',
    Medium: 'text-terminal-amber',
    High: 'text-terminal-red',
  }[centralizationRisk || 'Low']

  const riskBg = {
    Low: 'bg-terminal-green/10 border-terminal-green/30',
    Medium: 'bg-terminal-amber/10 border-terminal-amber/30',
    High: 'bg-terminal-red/10 border-terminal-red/30',
  }[centralizationRisk || 'Low']

  return (
    <div className={`terminal-panel p-4 ${className}`}>
      <h3 className="text-sm font-mono text-muted-foreground mb-4">
        Token Allocation
      </h3>

      {/* Donut Chart */}
      <div className="flex justify-center">
        <DonutChart segments={segments} />
      </div>

      {/* Legend */}
      <Legend segments={segments} />

      {/* Risk Indicator */}
      {(centralizationRisk || insiderPercentage !== undefined) && (
        <div className="mt-4 pt-4 border-t border-border/50 space-y-2">
          {centralizationRisk && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                Centralization Risk
              </span>
              <span
                className={`px-2 py-0.5 rounded border text-xs font-medium ${riskBg} ${riskColor}`}
              >
                {centralizationRisk}
              </span>
            </div>
          )}
          {insiderPercentage !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                Insider Ownership
              </span>
              <span
                className={`text-sm font-mono ${
                  insiderPercentage > 50
                    ? 'text-terminal-red'
                    : insiderPercentage > 30
                    ? 'text-terminal-amber'
                    : 'text-foreground'
                }`}
              >
                {insiderPercentage.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default HolderDistribution
