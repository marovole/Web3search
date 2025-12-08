/**
 * Adversarial Q&A Component
 *
 * Displays critical follow-up questions generated from research analysis.
 * Clicking a question triggers a new deep research session.
 *
 * @module components/Research/AdversarialQA
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { HelpCircle, ChevronRight, AlertCircle } from 'lucide-react'
import type { AdversarialQuestion } from '@/types/deep-research'

// ============================================================================
// Types
// ============================================================================

export interface AdversarialQAProps {
  /** List of adversarial questions */
  questions: AdversarialQuestion[]
  /** Callback when a question is clicked */
  onQuestionClick?: (question: string) => void
  /** Loading state */
  isLoading?: boolean
  /** Additional CSS classes */
  className?: string
}

// ============================================================================
// Subcomponents
// ============================================================================

interface QuestionCardProps {
  question: AdversarialQuestion
  index: number
  onClick?: () => void
}

function QuestionCard({ question, index, onClick }: QuestionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const handleClick = () => {
    if (onClick) {
      onClick()
    }
  }

  const handleExpandToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsExpanded(!isExpanded)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="group"
    >
      <div
        onClick={handleClick}
        className={`
          relative p-4 rounded-lg cursor-pointer
          bg-surface-2/50 border border-terminal-amber/20
          hover:border-terminal-amber/50 hover:bg-surface-2/80
          transition-all duration-200
        `}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleClick()
          }
        }}
      >
        {/* Question Number Badge */}
        <div className="absolute -top-2 -left-2 w-6 h-6 rounded-full bg-terminal-amber/20 border border-terminal-amber/40 flex items-center justify-center">
          <span className="text-xs font-mono text-terminal-amber">{index + 1}</span>
        </div>

        {/* Question Content */}
        <div className="flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-terminal-amber flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground leading-relaxed pr-8">
              {question.question}
            </p>

            {/* Rationale (expandable) */}
            <AnimatePresence>
              {isExpanded && question.rationale && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="text-xs text-muted-foreground mt-2 leading-relaxed"
                >
                  <span className="text-terminal-amber font-medium">Why it matters:</span>{' '}
                  {question.rationale}
                </motion.p>
              )}
            </AnimatePresence>
          </div>

          {/* Expand/Action Button */}
          <div className="flex items-center gap-1 flex-shrink-0">
            {question.rationale && (
              <button
                onClick={handleExpandToggle}
                className="p-1 rounded hover:bg-surface-3 transition-colors"
                aria-label={isExpanded ? 'Collapse rationale' : 'Show rationale'}
              >
                <HelpCircle className="w-4 h-4 text-muted-foreground" />
              </button>
            )}
            <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-terminal-amber transition-colors" />
          </div>
        </div>

        {/* Hover hint */}
        <div className="absolute bottom-1 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="text-xs text-muted-foreground">Click to research</span>
        </div>
      </div>
    </motion.div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="p-4 rounded-lg bg-surface-2/50 border border-border/30">
          <div className="flex items-start gap-3">
            <div className="w-4 h-4 bg-surface-3 rounded-full" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-surface-3 rounded w-full" />
              <div className="h-4 bg-surface-3 rounded w-3/4" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function AdversarialQA({
  questions,
  onQuestionClick,
  isLoading = false,
  className = '',
}: AdversarialQAProps) {
  if (isLoading) {
    return (
      <div className={`terminal-panel p-4 ${className}`}>
        <div className="flex items-center gap-2 mb-4">
          <HelpCircle className="w-4 h-4 text-terminal-amber" />
          <h3 className="text-sm font-mono text-muted-foreground">
            Generating Critical Questions...
          </h3>
        </div>
        <LoadingSkeleton />
      </div>
    )
  }

  if (!questions || questions.length === 0) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className={`terminal-panel p-4 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-terminal-amber" />
          <h3 className="text-sm font-medium text-foreground">
            Critical Questions to Consider
          </h3>
        </div>
        <span className="text-xs text-muted-foreground font-mono">
          {questions.length} questions
        </span>
      </div>

      {/* Description */}
      <p className="text-xs text-muted-foreground mb-4">
        These questions challenge the research findings. Click any question to dive deeper.
      </p>

      {/* Questions List */}
      <div className="space-y-3">
        {questions.map((q, idx) => (
          <QuestionCard
            key={`q-${idx}`}
            question={q}
            index={idx}
            onClick={() => onQuestionClick?.(q.question)}
          />
        ))}
      </div>

      {/* Footer Hint */}
      <div className="mt-4 pt-3 border-t border-border/30">
        <p className="text-xs text-muted-foreground text-center">
          Click a question to start a new research session
        </p>
      </div>
    </motion.div>
  )
}

export default AdversarialQA
