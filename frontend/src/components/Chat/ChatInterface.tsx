import React, { useState, useRef, useEffect, useCallback, Suspense } from 'react'
import type { Message, ChatMode } from '../../types'
import { quickChat, deepResearchStream } from '../../services/api'
import useNetworkRetry from '../../hooks/useNetworkRetry'
import * as Sentry from '../../services/sentry-lite'
import MessageList from './MessageList'
import AutocompleteInput from './AutocompleteInput'
import LoadingAnimation from '../Shared/LoadingAnimation'
import NetworkErrorRetry from '../Error/NetworkErrorRetry'
import { cn } from '@/lib/utils'
import type {
  ToolCallEvent,
  ThinkingEvent,
  TokenomicsAnalysis,
  AdversarialQuestion,
} from '@/types/deep-research'

const ChatEmptyState = React.lazy(() => import('./ChatEmptyState'))
const ChatDeepResearchPanels = React.lazy(() => import('./ChatDeepResearchPanels'))

const EMPTY_STATE_FALLBACK = (
  <div className="min-h-[75vh] flex flex-col justify-center py-8" aria-busy="true">
    <div className="max-w-4xl mx-auto px-4 space-y-6 animate-pulse">
      <div className="h-8 w-48 rounded-lg bg-muted/30" />
      <div className="h-24 w-full rounded-xl bg-muted/20" />
      <div className="h-12 w-full max-w-md rounded-xl bg-muted/25" />
    </div>
  </div>
)

const DEEP_PANELS_FALLBACK = (
  <div className="mt-4 h-32 rounded-xl bg-muted/15 animate-pulse" aria-busy="true" />
)

const MIN_QUICK_CHAT_RESPONSE_LENGTH = 10

const normalizeQuickChatResponse = (rawContent?: string): string => {
  const normalized = rawContent?.trim() ?? ''
  if (normalized.length >= MIN_QUICK_CHAT_RESPONSE_LENGTH) {
    return normalized
  }
  return [
    '⚠️ 快速回复异常：AI返回内容过短，请稍后再试或切换到深度研究模式。',
    normalized ? `原始响应：${normalized}` : '原始响应为空。',
  ].join('\n')
}

function needsDeepResearchPanels(
  mode: ChatMode,
  isLoading: boolean,
  toolCalls: ToolCallEvent[],
  thoughts: ThinkingEvent[],
  tokenomics: TokenomicsAnalysis | undefined,
  adversarialQuestions: AdversarialQuestion[]
): boolean {
  return (
    toolCalls.length > 0 ||
    thoughts.length > 0 ||
    !!tokenomics ||
    adversarialQuestions.length > 0 ||
    (mode === 'deep' && isLoading)
  )
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [mode, setMode] = useState<ChatMode>(() => {
    const saved = localStorage.getItem('chatMode')
    return (saved as ChatMode) || 'quick'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState(0)
  const [conversationId, setConversationId] = useState<string>()
  const [lastFailedQuery, setLastFailedQuery] = useState<string>('')

  const [toolCalls, setToolCalls] = useState<ToolCallEvent[]>([])
  const [thoughts, setThoughts] = useState<ThinkingEvent[]>([])
  const [tokenomics, setTokenomics] = useState<TokenomicsAnalysis | undefined>()
  const [adversarialQuestions, setAdversarialQuestions] = useState<AdversarialQuestion[]>([])

  const quickChatWithRetry = useNetworkRetry(quickChat, {
    maxRetries: 3,
    retryDelay: 1000,
    exponentialBackoff: true,
  })

  const eventSourceRef = useRef<ReturnType<typeof deepResearchStream> | null>(null)
  const chatScrollRef = useRef<HTMLDivElement>(null)
  const conversationIdRef = useRef<string | undefined>(conversationId)
  conversationIdRef.current = conversationId

  useEffect(() => {
    conversationIdRef.current = conversationId
  }, [conversationId])

  const handleModeChange = useCallback((newMode: ChatMode) => {
    setMode(newMode)
    localStorage.setItem('chatMode', newMode)
  }, [])

  const handleDeepResearchStream = useCallback((query: string) => {
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    }
    setMessages((prev) => [...prev, assistantMessage])

    setToolCalls([])
    setThoughts([])
    setTokenomics(undefined)
    setAdversarialQuestions([])

    const currentConversationId = conversationIdRef.current

    const eventSource = deepResearchStream({
      query,
      conversation_id: currentConversationId,
    })
    eventSourceRef.current = eventSource

    let accumulatedContent = ''
    const loadingStages = [
      '正在采集市场数据...',
      '正在分析链上活动...',
      '正在评估社交情绪...',
      '正在生成技术面分析...',
      '正在组装报告...',
    ]

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const eventType = data.type || data.event
        const payload = data.data || data

        if (eventType === 'tool_call') {
          const toolEvent: ToolCallEvent = {
            type: 'tool_call',
            tool: payload.tool ?? 'search',
            query: payload.query,
            provider: payload.provider,
            latency_ms: payload.latency_ms ?? 0,
            result_summary: payload.result_summary ?? '',
            source_count: payload.source_count,
            status: payload.status ?? 'started',
            timestamp: payload.timestamp,
          }
          setToolCalls((prev) => [...prev, toolEvent])
        }

        if (eventType === 'thinking') {
          const thinkingEvent: ThinkingEvent = {
            type: 'thinking',
            stage: payload.stage ?? 'planning',
            thought: payload.thought ?? '',
            timestamp: payload.timestamp,
          }
          setThoughts((prev) => [...prev, thinkingEvent])
        }

        if (eventType === 'progress') {
          let stageIdx = 0
          if (data.stage === 'data_collection') {
            setLoadingStage(1)
            stageIdx = 1
          } else if (data.stage === 'analysis') {
            setLoadingStage(2)
            stageIdx = 2
          } else if (data.stage === 'report_generation') {
            setLoadingStage(3)
            stageIdx = 3
          }

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id
                ? {
                    ...msg,
                    content: data.content || `${loadingStages[stageIdx] || '处理中...'}`,
                  }
                : msg
            )
          )
        } else if (eventType === 'content') {
          if (data.content) {
            accumulatedContent = data.content
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessage.id ? { ...msg, content: accumulatedContent } : msg
              )
            )
          }
        } else if (eventType === 'error') {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id
                ? { ...msg, content: `❌ 错误：${data.content}`, isStreaming: false }
                : msg
            )
          )
          setIsLoading(false)
          eventSource.close()
          eventSourceRef.current = null
        } else if (eventType === 'complete' || data.done) {
          if (payload.tokenomics_analysis || payload.tokenomics) {
            setTokenomics((payload.tokenomics_analysis || payload.tokenomics) as TokenomicsAnalysis)
          }
          if (Array.isArray(payload.adversarial_questions)) {
            setAdversarialQuestions(payload.adversarial_questions as AdversarialQuestion[])
          }

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id ? { ...msg, isStreaming: false } : msg
            )
          )
          setIsLoading(false)
          if (data.session_id) setConversationId(data.session_id)
          eventSource.close()
          eventSourceRef.current = null
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error)
      }
    }

    eventSource.onerror = () => {
      console.error('EventSource error')
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? {
                ...msg,
                content:
                  accumulatedContent ||
                  '❌ 抱歉，连接中断。请检查网络连接后重试。',
                isStreaming: false,
              }
            : msg
        )
      )
      setIsLoading(false)
      eventSource.close()
      eventSourceRef.current = null
    }
  }, [])

  const handleSendMessage = async (userInput: string) => {
    if (!userInput.trim()) return

    Sentry.startTransaction(`chat-${mode}`, 'chat')
    Sentry.addBreadcrumb({
      message: 'User sent chat message',
      category: 'chat',
      level: 'info',
      data: { mode, queryLength: userInput.length, messageCount: messages.length },
    })

    setInputValue('')
    setLastFailedQuery('')

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userInput,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])

    setIsLoading(true)
    setLoadingStage(0)

    const currentConversationId = conversationIdRef.current

    try {
      if (mode === 'quick') {
        const response = await quickChatWithRetry.execute({
          query: userInput,
          conversation_id: currentConversationId,
        })

        const sanitizedContent = normalizeQuickChatResponse(response.content)

        if (sanitizedContent !== (response.content?.trim() ?? '')) {
          Sentry.addBreadcrumb({
            message: 'Quick chat response sanitized',
            category: 'chat',
            level: 'warning',
            data: {
              rawLength: response.content?.length || 0,
              normalizedLength: sanitizedContent.length,
              sessionId: response.session_id,
            },
          })
        }

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: sanitizedContent,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, assistantMessage])
        setConversationId(response.session_id)
      } else {
        handleDeepResearchStream(userInput)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      if (error instanceof Error) {
        Sentry.captureException(error, {
          query: userInput,
          mode,
          conversationId: currentConversationId,
          retryCount: quickChatWithRetry.state.retryCount,
        })
      }
      setLastFailedQuery(userInput)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ 抱歉，发生错误：${error instanceof Error ? error.message : '未知错误'}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      if (mode === 'quick') {
        setIsLoading(false)
      }
    }
  }

  const handleRetry = async () => {
    if (!lastFailedQuery.trim()) return
    setMessages((prev) => {
      const newMessages = [...prev]
      if (
        newMessages.length > 0 &&
        newMessages[newMessages.length - 1]?.content.includes('❌ 抱歉，发生错误')
      ) {
        newMessages.pop()
      }
      return newMessages
    })
    await handleSendMessage(lastFailedQuery)
  }

  const handleQuestionClick = useCallback(
    (question: string) => {
      setMode('deep')
      localStorage.setItem('chatMode', 'deep')
      setTimeout(() => {
        handleDeepResearchStream(question)
      }, 0)
    },
    [handleDeepResearchStream]
  )

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [mode])

  const loadDeepPanels = needsDeepResearchPanels(
    mode,
    isLoading,
    toolCalls,
    thoughts,
    tokenomics,
    adversarialQuestions
  )

  return (
    <div className="flex flex-col h-full relative min-h-0">
      <div
        ref={chatScrollRef}
        className="flex-1 min-h-0 overflow-y-auto custom-scrollbar pb-32"
      >
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
          <div className="transition-opacity duration-300 ease-out">
            {messages.length === 0 ? (
              <Suspense fallback={EMPTY_STATE_FALLBACK}>
                <ChatEmptyState
                  mode={mode}
                  onModeChange={handleModeChange}
                  onQuickFill={setInputValue}
                />
              </Suspense>
            ) : (
              <div className="space-y-8 transition-opacity duration-300">
                <MessageList messages={messages} scrollParentRef={chatScrollRef} />

                {loadDeepPanels && (
                  <Suspense fallback={DEEP_PANELS_FALLBACK}>
                    <ChatDeepResearchPanels
                      mode={mode}
                      isLoading={isLoading}
                      toolCalls={toolCalls}
                      thoughts={thoughts}
                      tokenomics={tokenomics}
                      adversarialQuestions={adversarialQuestions}
                      onQuestionClick={handleQuestionClick}
                    />
                  </Suspense>
                )}

                {quickChatWithRetry.state.error && lastFailedQuery && (
                  <NetworkErrorRetry
                    onRetry={handleRetry}
                    error={quickChatWithRetry.state.error}
                    isRetrying={quickChatWithRetry.state.isLoading}
                    retryCount={quickChatWithRetry.state.retryCount}
                  />
                )}

                {isLoading && <LoadingAnimation stage={loadingStage} mode={mode} />}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-background via-background/98 to-transparent z-30">
        <div className="max-w-3xl mx-auto">
          <div
            className={cn(
              'glass-card p-1.5 md:p-2 transition-all duration-300',
              'ring-1 ring-white/[0.06]',
              'focus-within:ring-primary/40 focus-within:shadow-glow-md',
              isLoading ? 'opacity-70 pointer-events-none' : 'opacity-100'
            )}
          >
            <AutocompleteInput
              value={inputValue}
              onChange={setInputValue}
              onSend={handleSendMessage}
              disabled={isLoading}
              placeholder={
                mode === 'quick'
                  ? 'Ask anything about crypto...'
                  : 'Enter project name for deep research...'
              }
            />
          </div>
          <div className="text-center mt-3 flex items-center justify-center gap-3">
            <p className="text-[9px] md:text-[10px] uppercase tracking-[0.15em] text-muted-foreground/60 font-medium">
              AI-generated content may be inaccurate
            </p>
            <span className="text-muted-foreground/40">·</span>
            <p className="text-[9px] md:text-[10px] uppercase tracking-[0.15em] text-muted-foreground/60 font-medium">
              DYOR
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
