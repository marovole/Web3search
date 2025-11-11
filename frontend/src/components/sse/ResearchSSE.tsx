/**
 * Deep Research Streaming Component
 * Real-time progress tracking for Deep Research tasks
 * Part of Week 2 T13: Frontend SSE Integration
 */

import { useState, useEffect, useMemo } from 'react'
import { useResearchSSE } from '../../hooks/useSSE'
import type { ResearchSSEvent } from '../../lib/sse'
import { xssProtection } from '@/services/xssProtection'

export interface ResearchSSEProps {
  apiUrl: string
  query: string
  onComplete?: (result: any) => void
  onError?: (error: Error) => void
  onProgress?: (progress: number, step: string) => void
}

export interface ResearchStep {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  result?: any
}

export function ResearchSSE({
  apiUrl,
  query,
  onComplete,
  onError,
  onProgress,
}: ResearchSSEProps) {
  const [isStarted, setIsStarted] = useState(false)
  const [researchSteps, setResearchSteps] = useState<ResearchStep[]>([
    { id: 'plan', name: 'Generating Research Plan', status: 'pending', progress: 0 },
    { id: 'search', name: 'Searching Sources', status: 'pending', progress: 0 },
    { id: 'analyze', name: 'Analyzing Content', status: 'pending', progress: 0 },
    { id: 'synthesize', name: 'Synthesizing Insights', status: 'pending', progress: 0 },
    { id: 'compile', name: 'Compiling Report', status: 'pending', progress: 0 },
  ])
  const [currentStep, setCurrentStep] = useState<string>('')
  const [result, setResult] = useState<any>(null)
  const [errorMessage, setErrorMessage] = useState<string>('')

  // 清理 HTML 内容以防止 XSS 攻击
  const sanitizedResultHtml = useMemo(
    () => xssProtection.sanitizeHTML(result?.html || ''),
    [result?.html]
  )

  const {
    events,
    currentEvent,
    isConnected,
    error,
    progress,
    start,
    stop,
    reset,
  } = useResearchSSE(apiUrl, {
    onMessage: (data: ResearchSSEvent) => {
      setErrorMessage('')

      // Parse the event
      switch (data.event) {
        case 'research.started':
          updateStepStatus('plan', 'running')
          setCurrentStep('Generating research plan...')
          break

        case 'research.progress':
          if (data.data.task_id) {
            updateStepProgress(data.data.task_id, data.data.progress_percent || 0)
          }
          onProgress?.(data.data.progress_percent || 0, currentStep)
          break

        case 'research.step':
          if (data.data.step === 'plan_complete') {
            updateStepStatus('plan', 'completed')
            updateStepStatus('search', 'running')
            setCurrentStep('Searching and analyzing sources...')
          } else if (data.data.step === 'search_complete') {
            updateStepStatus('search', 'completed')
            updateStepStatus('analyze', 'running')
            setCurrentStep('Analyzing content...')
          } else if (data.data.step === 'analysis_complete') {
            updateStepStatus('analyze', 'completed')
            updateStepStatus('synthesize', 'running')
            setCurrentStep('Synthesizing insights...')
          } else if (data.data.step === 'synthesis_complete') {
            updateStepStatus('synthesize', 'completed')
            updateStepStatus('compile', 'running')
            setCurrentStep('Compiling final report...')
          }
          break

        case 'research.completed':
          updateStepStatus('compile', 'completed')
          setResult(data.data.result)
          onComplete?.(data.data.result)
          setIsStarted(false)
          break

        case 'research.failed':
          setErrorMessage(data.data.error_message || 'Research failed')
          updateStepStatus(currentStep.toLowerCase() || 'plan', 'failed')
          onError?.(new Error(data.data.error_message || 'Research failed'))
          setIsStarted(false)
          break
      }
    },
    onError: (err) => {
      setErrorMessage(err.message)
      onError?.(err)
      setIsStarted(false)
    },
  })

  // Update step status helper
  const updateStepStatus = (stepId: string, status: 'pending' | 'running' | 'completed' | 'failed') => {
    setResearchSteps(prev => prev.map(step =>
      step.id === stepId ? { ...step, status } : step
    ))
  }

  // Update step progress helper
  const updateStepProgress = (stepId: string, progressPercent: number) => {
    setResearchSteps(prev => prev.map(step =>
      step.id === stepId ? { ...step, progress: progressPercent } : step
    ))
  }

  // Handle start research
  const handleStart = () => {
    if (!query.trim()) {
      setErrorMessage('Please enter a research query')
      return
    }

    // Reset state
    reset()
    setIsStarted(true)
    setErrorMessage('')
    setResult(null)
    setResearchSteps([
      { id: 'plan', name: 'Generating Research Plan', status: 'running', progress: 0 },
      { id: 'search', name: 'Searching Sources', status: 'pending', progress: 0 },
      { id: 'analyze', name: 'Analyzing Content', status: 'pending', progress: 0 },
      { id: 'synthesize', name: 'Synthesizing Insights', status: 'pending', progress: 0 },
      { id: 'compile', name: 'Compiling Report', status: 'pending', progress: 0 },
    ])

    // Start SSE connection
    start()

    // In real implementation, this would trigger the research task
    // For demo, we'll simulate the API call
    console.log('Starting deep research for query:', query)
  }

  // Handle cancel research
  const handleCancel = () => {
    stop()
    setIsStarted(false)
    setErrorMessage('Research cancelled')
  }

  // Get status indicator color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-500'
      case 'completed': return 'bg-green-500'
      case 'failed': return 'bg-red-500'
      default: return 'bg-gray-300'
    }
  }

  // Get progress bar color
  const getProgressColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-500'
      case 'completed': return 'bg-green-500'
      case 'failed': return 'bg-red-500'
      default: return 'bg-gray-300'
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Deep Research
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Track real-time progress of your research task
        </p>
      </div>

      {/* Query Display */}
      <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
          Research Query
        </h3>
        <p className="text-gray-900 dark:text-gray-100 font-medium">{query}</p>
      </div>

      {/* Connection Status */}
      {isStarted && (
        <div className="mb-6 px-4 py-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full animate-pulse ${
              isConnected ? 'bg-green-500' : 'bg-yellow-500'
            }`} />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {isConnected ? 'Connected' : 'Connecting...'}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Progress: {progress}%
            </span>
            {currentStep && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                • {currentStep}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Research Steps */}
      <div className="mb-6 space-y-4">
        {researchSteps.map((step, index) => (
          <div
            key={step.id}
            className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                  step.status === 'completed' ? 'bg-green-500' :
                  step.status === 'running' ? 'bg-blue-500' :
                  step.status === 'failed' ? 'bg-red-500' : 'bg-gray-300'
                }`}>
                  {step.status === 'completed' ? '✓' : index + 1}
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {step.name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {step.status === 'running' ? 'In progress...' :
                     step.status === 'completed' ? 'Completed' :
                     step.status === 'failed' ? 'Failed' :
                     'Waiting...'}
                  </p>
                </div>
              </div>
              <div className={`w-3 h-3 rounded-full ${getStatusColor(step.status)}`} />
            </div>

            {step.status === 'running' && (
              <div className="px-4 pb-4">
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${getProgressColor(step.status)}`}
                    style={{ width: `${step.progress}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-right">
                  {step.progress}%
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-700 dark:text-red-400">{errorMessage}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mb-6">
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-4">
            <h3 className="text-lg font-medium text-green-800 dark:text-green-300 mb-2">
              ✓ Research Completed
            </h3>
            <p className="text-sm text-green-700 dark:text-green-400">
              Your deep research task has been completed successfully.
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Research Results
            </h3>
            <div className="prose dark:prose-invert max-w-none">
              {result.markdown ? (
                <div dangerouslySetInnerHTML={{ __html: sanitizedResultHtml }} />
              ) : (
                <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto">
                  <code className="text-sm text-gray-700 dark:text-gray-300">
                    {JSON.stringify(result, null, 2)}
                  </code>
                </pre>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Control Buttons */}
      <div className="flex space-x-4">
        {!isStarted ? (
          <button
            onClick={handleStart}
            disabled={!query.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Start Research
          </button>
        ) : (
          <button
            onClick={handleCancel}
            className="px-6 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
          >
            Cancel Research
          </button>
        )}

        {result && (
          <button
            onClick={() => {
              reset()
              setResult(null)
              setErrorMessage('')
              setResearchSteps([
                { id: 'plan', name: 'Generating Research Plan', status: 'pending', progress: 0 },
                { id: 'search', name: 'Searching Sources', status: 'pending', progress: 0 },
                { id: 'analyze', name: 'Analyzing Content', status: 'pending', progress: 0 },
                { id: 'synthesize', name: 'Synthesizing Insights', status: 'pending', progress: 0 },
                { id: 'compile', name: 'Compiling Report', status: 'pending', progress: 0 },
              ])
            }}
            className="px-6 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors"
          >
            Reset
          </button>
        )}
      </div>

      {/* Debug Info (optional) */}
      {process.env.NODE_ENV === 'development' && events.length > 0 && (
        <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Debug Events ({events.length})
          </h3>
          <div className="max-h-40 overflow-y-auto space-y-1">
            {events.slice(-5).map((event, i) => (
              <pre key={i} className="text-xs text-gray-600 dark:text-gray-400">
                {JSON.stringify(event, null, 2)}
              </pre>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ResearchSSE
