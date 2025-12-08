/**
 * Red Flag Dashboard Component
 *
 * Container component that combines ScamMeter, HolderDistribution, and
 * UnlockCalendar into a comprehensive risk visualization dashboard.
 *
 * @module components/Research/RedFlagDashboard
 */

import { motion } from 'framer-motion'
import { AlertTriangle } from 'lucide-react'
import { ScamMeter } from './ScamMeter'
import { HolderDistribution } from './HolderDistribution'
import { UnlockCalendar } from './UnlockCalendar'
import type { TokenomicsAnalysis } from '@/types/deep-research'

// ============================================================================
// Types
// ============================================================================

export interface RedFlagDashboardProps {
  /** Tokenomics analysis data from deep research */
  tokenomics?: TokenomicsAnalysis
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

// ============================================================================
// Main Component
// ============================================================================

export function RedFlagDashboard({
  tokenomics,
  isLoading = false,
  className = '',
}: RedFlagDashboardProps) {
  const hasData = tokenomics && (
    tokenomics.scorecard ||
    tokenomics.analysis?.allocation?.breakdown ||
    tokenomics.analysis?.vesting
  )

  if (!hasData && !isLoading) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`mb-6 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-4 h-4 text-terminal-amber" />
        <h2 className="text-lg font-medium text-foreground">
          Risk Assessment Dashboard
        </h2>
        {tokenomics?.scorecard && (
          <span
            className={`ml-auto text-sm font-mono ${
              tokenomics.scorecard.color === 'red'
                ? 'text-terminal-red'
                : tokenomics.scorecard.color === 'yellow'
                ? 'text-terminal-amber'
                : 'text-terminal-green'
            }`}
          >
            Score: {tokenomics.scorecard.score}/100
          </span>
        )}
      </div>

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* ScamMeter */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <ScamMeter
            scorecard={tokenomics?.scorecard}
            redFlags={tokenomics?.red_flags}
            isLoading={isLoading}
          />
        </motion.div>

        {/* HolderDistribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <HolderDistribution
            breakdown={tokenomics?.analysis?.allocation?.breakdown}
            centralizationRisk={tokenomics?.analysis?.allocation?.centralization_risk}
            insiderPercentage={tokenomics?.analysis?.allocation?.insider_percentage}
            isLoading={isLoading}
          />
        </motion.div>

        {/* UnlockCalendar */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <UnlockCalendar
            vesting={tokenomics?.analysis?.vesting}
            isLoading={isLoading}
          />
        </motion.div>
      </div>

      {/* Verdict Section */}
      {tokenomics?.verdict && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-4 terminal-panel p-4"
        >
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-mono text-muted-foreground">
              Investment Verdict
            </h3>
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                tokenomics.verdict.recommendation === 'Avoid'
                  ? 'bg-terminal-red/10 text-terminal-red border border-terminal-red/30'
                  : tokenomics.verdict.recommendation === 'Short-term flip'
                  ? 'bg-terminal-amber/10 text-terminal-amber border border-terminal-amber/30'
                  : 'bg-terminal-green/10 text-terminal-green border border-terminal-green/30'
              }`}
            >
              {tokenomics.verdict.recommendation}
            </span>
          </div>
          <p className="text-sm text-foreground/90 leading-relaxed">
            {tokenomics.verdict.summary}
          </p>
        </motion.div>
      )}

      {/* Stress Test Summary */}
      {tokenomics?.stress_test?.findings && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-3 px-4 py-3 bg-surface-2/50 border border-border/50 rounded-lg"
        >
          <h4 className="text-xs font-mono text-muted-foreground mb-1 uppercase tracking-wider">
            Stress Test: {tokenomics.stress_test.scenario}
          </h4>
          <p className="text-sm text-foreground/80">
            {tokenomics.stress_test.findings}
          </p>
          {(tokenomics.stress_test.treasury_runway || tokenomics.stress_test.staking_impact) && (
            <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
              {tokenomics.stress_test.treasury_runway && (
                <span>Treasury: {tokenomics.stress_test.treasury_runway}</span>
              )}
              {tokenomics.stress_test.staking_impact && (
                <span>Staking Impact: {tokenomics.stress_test.staking_impact}</span>
              )}
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  )
}

export default RedFlagDashboard
