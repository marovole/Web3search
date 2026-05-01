import React from 'react'
import {
  GlassBoxPanel,
  RedFlagDashboard,
  AdversarialQA,
  ResearchErrorBoundary,
} from '../Research'
import type {
  ToolCallEvent,
  ThinkingEvent,
  TokenomicsAnalysis,
  AdversarialQuestion,
} from '@/types/deep-research'
import type { ChatMode } from '../../types'

export interface ChatDeepResearchPanelsProps {
  mode: ChatMode
  isLoading: boolean
  toolCalls: ToolCallEvent[]
  thoughts: ThinkingEvent[]
  tokenomics: TokenomicsAnalysis | undefined
  adversarialQuestions: AdversarialQuestion[]
  onQuestionClick: (question: string) => void
}

/**
 * Lazy-loaded deep-research visualization stack (Research barrel).
 */
export default function ChatDeepResearchPanels({
  mode,
  isLoading,
  toolCalls,
  thoughts,
  tokenomics,
  adversarialQuestions,
  onQuestionClick,
}: ChatDeepResearchPanelsProps) {
  return (
    <>
      {mode === 'deep' && (isLoading || toolCalls.length > 0 || thoughts.length > 0) && (
        <GlassBoxPanel toolCalls={toolCalls} thoughts={thoughts} className="mt-4" />
      )}

      {!isLoading && tokenomics && (
        <RedFlagDashboard tokenomics={tokenomics} className="mt-4" />
      )}

      {!isLoading && adversarialQuestions.length > 0 && (
        <ResearchErrorBoundary componentName="AdversarialQA">
          <AdversarialQA
            questions={adversarialQuestions}
            onQuestionClick={onQuestionClick}
            className="mt-4"
          />
        </ResearchErrorBoundary>
      )}
    </>
  )
}
