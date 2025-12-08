/**
 * Glass Box Panel Component
 *
 * Real-time visualization of the agent's tool calls and thinking process
 * during deep research. Provides transparency into the research pipeline.
 *
 * @module components/Research/GlassBoxPanel
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronUp } from 'lucide-react'
import type { ToolCallEvent, ThinkingEvent } from '@/types/deep-research'

// ============================================================================
// Types
// ============================================================================

export interface GlassBoxPanelProps {
  /** List of tool call events */
  toolCalls: ToolCallEvent[]
  /** List of thinking events */
  thoughts: ThinkingEvent[]
  /** Whether the panel is expanded */
  isExpanded?: boolean
  /** Callback when expand/collapse is toggled */
  onToggle?: () => void
  /** Additional CSS classes */
  className?: string
}

// ============================================================================
// Constants
// ============================================================================

const TOOL_ICONS: Record<ToolCallEvent['tool'], string> = {
  search: '\u{1F50D}',           // 🔍
  market_data: '\u{1F4CA}',      // 📊
  security_check: '\u{1F6E1}',   // 🛡️
  synthesis: '\u{1F4DD}',        // 📝
  plan_generation: '\u{1F4CB}',  // 📋
}

const TOOL_LABELS: Record<ToolCallEvent['tool'], string> = {
  search: 'Web Search',
  market_data: 'Market Data',
  security_check: 'Security Check',
  synthesis: 'Synthesis',
  plan_generation: 'Planning',
}

const STAGE_LABELS: Record<ThinkingEvent['stage'], string> = {
  planning: 'Planning',
  searching: 'Searching',
  analyzing: 'Analyzing',
  synthesizing: 'Synthesizing',
}

// ============================================================================
// Subcomponents
// ============================================================================

interface ToolCallItemProps {
  event: ToolCallEvent
  index: number
}

function ToolCallItem({ event, index }: ToolCallItemProps) {
  const statusColor = {
    started: 'text-terminal-amber',
    completed: 'text-terminal-green',
    failed: 'text-terminal-red',
  }[event.status]

  const statusBg = {
    started: 'bg-terminal-amber/10',
    completed: 'bg-terminal-green/10',
    failed: 'bg-terminal-red/10',
  }[event.status]

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`flex items-start gap-3 p-3 rounded-lg ${statusBg} border border-border/30`}
    >
      <span className="text-lg flex-shrink-0" role="img" aria-label={TOOL_LABELS[event.tool]}>
        {TOOL_ICONS[event.tool]}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="font-mono text-sm font-medium text-foreground">
            {TOOL_LABELS[event.tool]}
          </span>
          <span className={`text-xs font-mono ${statusColor}`}>
            {event.status === 'completed' && event.latency_ms > 0
              ? `${event.latency_ms}ms`
              : event.status}
          </span>
        </div>
        {event.query && (
          <p className="text-xs text-muted-foreground mt-1 truncate">
            {event.query}
          </p>
        )}
        {event.result_summary && event.status === 'completed' && (
          <p className="text-xs text-foreground/80 mt-1 line-clamp-2">
            {event.result_summary}
          </p>
        )}
        {event.source_count !== undefined && event.source_count > 0 && (
          <p className="text-xs text-terminal-cyan mt-1">
            {event.source_count} sources found
          </p>
        )}
        {event.provider && (
          <p className="text-xs text-muted-foreground mt-0.5">
            via {event.provider}
          </p>
        )}
      </div>
    </motion.div>
  )
}

interface ThinkingItemProps {
  event: ThinkingEvent
  index: number
}

function ThinkingItem({ event, index }: ThinkingItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      className="flex items-start gap-2 py-2"
    >
      <span className="text-terminal-purple text-xs font-mono flex-shrink-0">
        [{STAGE_LABELS[event.stage]}]
      </span>
      <p className="text-sm text-foreground/90 leading-relaxed">
        {event.thought}
      </p>
    </motion.div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function GlassBoxPanel({
  toolCalls,
  thoughts,
  isExpanded: controlledExpanded,
  onToggle,
  className = '',
}: GlassBoxPanelProps) {
  const [internalExpanded, setInternalExpanded] = useState(true)
  const isExpanded = controlledExpanded ?? internalExpanded

  const handleToggle = () => {
    if (onToggle) {
      onToggle()
    } else {
      setInternalExpanded(!internalExpanded)
    }
  }

  // Note: Timeline events could be used for unified view in future iterations
  // Currently showing tool calls and thoughts in separate sections

  const completedTools = toolCalls.filter(t => t.status === 'completed').length
  const totalLatency = toolCalls
    .filter(t => t.status === 'completed')
    .reduce((sum, t) => sum + t.latency_ms, 0)

  if (toolCalls.length === 0 && thoughts.length === 0) {
    return null
  }

  return (
    <div className={`terminal-panel overflow-hidden ${className}`}>
      {/* Header */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between p-3 hover:bg-surface-2/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-terminal-green font-mono text-sm">$</span>
          <span className="font-medium text-foreground">Agent Activity</span>
          <span className="text-xs text-muted-foreground font-mono">
            ({completedTools}/{toolCalls.length} tools)
          </span>
        </div>
        <div className="flex items-center gap-3">
          {totalLatency > 0 && (
            <span className="text-xs text-muted-foreground font-mono">
              {totalLatency}ms total
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-3 pt-0 space-y-3 max-h-80 overflow-y-auto">
              {/* Tool Calls Section */}
              {toolCalls.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                    Tool Calls
                  </h4>
                  <div className="space-y-2">
                    {toolCalls.map((event, idx) => (
                      <ToolCallItem key={`${event.tool}-${idx}`} event={event} index={idx} />
                    ))}
                  </div>
                </div>
              )}

              {/* Thinking Section */}
              {thoughts.length > 0 && (
                <div className="space-y-1">
                  <h4 className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                    Agent Reasoning
                  </h4>
                  <div className="pl-2 border-l-2 border-terminal-purple/30">
                    {thoughts.map((event, idx) => (
                      <ThinkingItem key={`thought-${idx}`} event={event} index={idx} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default GlassBoxPanel
