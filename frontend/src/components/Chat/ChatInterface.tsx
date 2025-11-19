import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Message, ChatMode } from '../../types'
import { quickChat, deepResearchStream } from '../../services/api'
import useNetworkRetry from '../../hooks/useNetworkRetry'
import * as Sentry from '../../services/sentry-lite'
import ModeSwitch from './ModeSwitch'
import MessageList from './MessageList'
import AutocompleteInput from './AutocompleteInput'
import LoadingAnimation from '../Shared/LoadingAnimation'
import HotspotPanel from '../Hotspot/HotspotPanel'
import NetworkErrorRetry from '../Error/NetworkErrorRetry'
import { cn } from '@/lib/utils'

const MIN_QUICK_CHAT_RESPONSE_LENGTH = 10

const normalizeQuickChatResponse = (rawContent?: string): string => {
  const normalized = rawContent?.trim() ?? ''
  if (normalized.length >= MIN_QUICK_CHAT_RESPONSE_LENGTH) {
    return normalized
  }
  return [
    '⚠️ 快速回复异常：AI返回内容过短，请稍后再试或切换到深度研究模式。',
    normalized ? `原始响应：${normalized}` : '原始响应为空。'
  ].join('\n')
}

const ChatInterface: React.FC = () => {
  // State
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

  // Network retry hook
  const quickChatWithRetry = useNetworkRetry(quickChat, {
    maxRetries: 3,
    retryDelay: 1000,
    exponentialBackoff: true,
  })

  // Refs
  const eventSourceRef = useRef<EventSource | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleModeChange = (newMode: ChatMode) => {
    setMode(newMode)
    localStorage.setItem('chatMode', newMode)
  }

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

    try {
      if (mode === 'quick') {
        const response = await quickChatWithRetry.execute({
          query: userInput,
          conversation_id: conversationId,
        })

        const sanitizedContent = normalizeQuickChatResponse(response.content)

        if (sanitizedContent !== (response.content?.trim() ?? '')) {
          Sentry.addBreadcrumb({
            message: 'Quick chat response sanitized',
            category: 'chat',
            level: 'warning',
            data: { rawLength: response.content?.length || 0, normalizedLength: sanitizedContent.length, sessionId: response.session_id },
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
        Sentry.captureException(error, { query: userInput, mode, conversationId, retryCount: quickChatWithRetry.state.retryCount })
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
      if (newMessages.length > 0 && newMessages[newMessages.length - 1].content.includes('❌ 抱歉，发生错误')) {
        newMessages.pop()
      }
      return newMessages
    })
    await handleSendMessage(lastFailedQuery)
  }

  const handleDeepResearchStream = (query: string) => {
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    }
    setMessages((prev) => [...prev, assistantMessage])

    const eventSource = deepResearchStream({
      query,
      conversation_id: conversationId,
    })
    eventSourceRef.current = eventSource

    let accumulatedContent = ''
    const loadingStages = ['正在采集市场数据...', '正在分析链上活动...', '正在评估社交情绪...', '正在生成技术面分析...', '正在组装报告...']

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'progress') {
          if (data.stage === 'data_collection') setLoadingStage(1)
          else if (data.stage === 'analysis') setLoadingStage(2)
          else if (data.stage === 'report_generation') setLoadingStage(3)

          setMessages((prev) => prev.map((msg) => msg.id === assistantMessage.id ? { ...msg, content: data.content || `${loadingStages[loadingStage] || '处理中...'}` } : msg))
        } else if (data.type === 'content') {
          if (data.content) {
            accumulatedContent = data.content
            setMessages((prev) => prev.map((msg) => msg.id === assistantMessage.id ? { ...msg, content: accumulatedContent } : msg))
          }
        } else if (data.type === 'error') {
          setMessages((prev) => prev.map((msg) => msg.id === assistantMessage.id ? { ...msg, content: `❌ 错误：${data.content}`, isStreaming: false } : msg))
          setIsLoading(false)
          eventSource.close()
          eventSourceRef.current = null
        } else if (data.type === 'complete' || data.done) {
          setMessages((prev) => prev.map((msg) => msg.id === assistantMessage.id ? { ...msg, isStreaming: false } : msg))
          setIsLoading(false)
          if (data.session_id) setConversationId(data.session_id)
          eventSource.close()
          eventSourceRef.current = null
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error)
      setMessages((prev) => prev.map((msg) => msg.id === assistantMessage.id ? { ...msg, content: accumulatedContent || '❌ 抱歉，连接中断。请检查网络连接后重试。', isStreaming: false } : msg))
      setIsLoading(false)
      eventSource.close()
      eventSourceRef.current = null
    }
  }

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [mode])

  return (
    <div className="flex flex-col h-full relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar pb-32">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
          <AnimatePresence mode='wait'>
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="min-h-[60vh] flex flex-col items-center justify-center"
              >
                {/* Branding */}
                <div className="text-center mb-12 relative">
                  <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-64 h-64 bg-primary/20 rounded-full blur-[100px] pointer-events-none" />

                  <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5 }}
                    className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-primary/20 to-secondary/20 border border-white/10 mb-8 shadow-2xl shadow-primary/10 animate-float"
                  >
                    <span className="text-4xl">⚡️</span>
                  </motion.div>

                  <h1 className="text-5xl md:text-6xl font-bold mb-6 tracking-tight">
                    <span className="text-foreground">Web3</span>
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary ml-3 neon-text">AI Search</span>
                  </h1>

                  <p className="text-muted-foreground text-lg md:text-xl max-w-lg mx-auto leading-relaxed">
                    Deep insights for the decentralized web. <br />
                    <span className="text-sm opacity-70">Powered by advanced AI agents.</span>
                  </p>
                </div>

                {/* Mode Switcher */}
                <div className="mb-12">
                  <ModeSwitch mode={mode} onChange={handleModeChange} />
                </div>

                {/* Hotspots */}
                <div className="w-full max-w-4xl">
                  <HotspotPanel
                    onSelectHotspot={(symbol, name) => {
                      setInputValue(`${symbol} (${name})`)
                    }}
                  />
                </div>
              </motion.div>
            ) : (
              <div className="space-y-8">
                <MessageList messages={messages} />

                {quickChatWithRetry.state.error && lastFailedQuery && (
                  <NetworkErrorRetry
                    onRetry={handleRetry}
                    error={quickChatWithRetry.state.error}
                    isRetrying={quickChatWithRetry.state.isLoading}
                    retryCount={quickChatWithRetry.state.retryCount}
                  />
                )}

                {isLoading && <LoadingAnimation stage={loadingStage} mode={mode} />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Floating Input Area */}
      <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-background via-background/95 to-transparent z-20">
        <div className="max-w-3xl mx-auto">
          <motion.div
            layout
            className={cn(
              "glass-card p-2 transition-all duration-300 ring-1 ring-white/10 focus-within:ring-primary/50 focus-within:shadow-[0_0_30px_-10px_rgba(0,242,255,0.3)]",
              isLoading ? "opacity-80 pointer-events-none grayscale" : "opacity-100"
            )}
          >
            <AutocompleteInput
              value={inputValue}
              onChange={setInputValue}
              onSend={handleSendMessage}
              disabled={isLoading}
              placeholder={mode === 'quick' ? 'Ask anything about crypto...' : 'Enter project name for deep research...'}
            />
          </motion.div>
          <div className="text-center mt-3">
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground/40 font-medium">
              AI-generated content may be inaccurate. DYOR.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
