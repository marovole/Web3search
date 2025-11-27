import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Terminal, Zap, Search, ArrowRight } from 'lucide-react'
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
      if (newMessages.length > 0 && newMessages[newMessages.length - 1]?.content.includes('❌ 抱歉，发生错误')) {
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
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="min-h-[75vh] flex flex-col justify-center py-8"
              >
                {/* Hero Section - Premium Terminal Style */}
                <div className="w-full max-w-4xl mx-auto px-4 relative">
                  {/* Decorative Grid Background */}
                  <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
                    <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-secondary/5 rounded-full blur-3xl" />
                  </div>

                  {/* Top Tag with Status */}
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1, ease: [0.19, 1, 0.22, 1] }}
                    className="mb-8 flex items-center gap-3"
                  >
                    <span className="terminal-tag">
                      <Terminal className="w-3 h-3" />
                      WEB3 INTELLIGENCE
                    </span>
                    <span className="flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground/50">
                      <span className="status-dot status-dot-live" />
                      LIVE
                    </span>
                  </motion.div>

                  {/* Main Title - Premium Display Typography */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15, duration: 0.6, ease: [0.19, 1, 0.22, 1] }}
                    className="mb-10"
                  >
                    <h1 className="font-display text-display-xl text-foreground mb-6 tracking-tight">
                      <motion.span 
                        className="block"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2, duration: 0.5 }}
                      >
                        Research.
                      </motion.span>
                      <motion.span 
                        className="block gradient-text-premium"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3, duration: 0.5 }}
                      >
                        Analyze.
                      </motion.span>
                      <motion.span 
                        className="block text-muted-foreground/70"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4, duration: 0.5 }}
                      >
                        Discover.
                      </motion.span>
                    </h1>
                    <p className="text-base md:text-lg text-muted-foreground max-w-xl font-sans leading-relaxed">
                      AI-powered deep research for crypto markets. 
                      <span className="text-foreground/80"> Real-time insights</span>, 
                      <span className="text-primary/80"> on-chain analysis</span>, and 
                      <span className="text-secondary/80"> sentiment data</span>.
                    </p>
                  </motion.div>

                  {/* Mode Switcher */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4, ease: [0.19, 1, 0.22, 1] }}
                    className="mb-12"
                  >
                    <ModeSwitch mode={mode} onChange={handleModeChange} />
                  </motion.div>

                  {/* Quick Actions - Enhanced */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5, ease: [0.19, 1, 0.22, 1] }}
                    className="mb-12"
                  >
                    <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-muted-foreground/50 mb-4 flex items-center gap-2">
                      <span className="w-8 h-px bg-border" />
                      Quick Start
                    </p>
                    <div className="flex flex-wrap gap-2.5">
                      {[
                        { label: 'BTC Analysis', icon: <Zap className="w-3.5 h-3.5" />, color: 'primary' },
                        { label: 'ETH Sentiment', icon: <Search className="w-3.5 h-3.5" />, color: 'secondary' },
                        { label: 'SOL Ecosystem', icon: <ArrowRight className="w-3.5 h-3.5" />, color: 'cyan' },
                      ].map((item, i) => (
                        <motion.button
                          key={item.label}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: 0.55 + i * 0.08, ease: [0.19, 1, 0.22, 1] }}
                          onClick={() => setInputValue(item.label)}
                          className={cn(
                            "group inline-flex items-center gap-2.5 px-4 py-2",
                            "font-mono text-sm text-muted-foreground",
                            "bg-surface-2/50 border border-border/40 rounded-xl",
                            "hover:border-primary/40 hover:text-foreground hover:bg-primary/[0.06]",
                            "hover:shadow-glow-sm active:scale-[0.97]",
                            "transition-all duration-250 ease-out-expo"
                          )}
                        >
                          <span className="text-primary/70 group-hover:text-primary transition-colors">
                            {item.icon}
                          </span>
                          {item.label}
                        </motion.button>
                      ))}
                    </div>
                  </motion.div>

                  {/* Hotspots Panel */}
                  <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.65, duration: 0.5, ease: [0.19, 1, 0.22, 1] }}
                  >
                    <HotspotPanel
                      onSelectHotspot={(symbol, name) => {
                        setInputValue(`${symbol} (${name})`)
                      }}
                    />
                  </motion.div>
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
      <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-background via-background/98 to-transparent z-20">
        <div className="max-w-3xl mx-auto">
          <motion.div
            layout
            className={cn(
              "glass-card p-1.5 md:p-2 transition-all duration-300",
              "ring-1 ring-white/[0.06]",
              "focus-within:ring-primary/40 focus-within:shadow-glow-md",
              isLoading ? "opacity-70 pointer-events-none" : "opacity-100"
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
          <div className="text-center mt-3 flex items-center justify-center gap-3">
            <p className="text-[9px] md:text-[10px] uppercase tracking-[0.15em] text-muted-foreground/35 font-medium">
              AI-generated content may be inaccurate
            </p>
            <span className="text-muted-foreground/20">·</span>
            <p className="text-[9px] md:text-[10px] uppercase tracking-[0.15em] text-muted-foreground/35 font-medium">
              DYOR
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
