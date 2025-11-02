import React, { useState, useRef, useEffect } from 'react'
import type { Message, ChatMode } from '../../types'
import { quickChat, deepResearchStream } from '../../services/api'
import useNetworkRetry from '../../hooks/useNetworkRetry'
import * as Sentry from '../../services/sentry-lite'
import { Card } from '@/components/ui/card'
import ModeSwitch from './ModeSwitch'
import MessageList from './MessageList'
import AutocompleteInput from './AutocompleteInput'
import LoadingAnimation from '../Shared/LoadingAnimation'
import HotspotPanel from '../Hotspot/HotspotPanel'
import NetworkErrorRetry from '../Error/NetworkErrorRetry'

const ChatInterface: React.FC = () => {
  // State
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [mode, setMode] = useState<ChatMode>(() => {
    // Load from localStorage
    const saved = localStorage.getItem('chatMode')
    return (saved as ChatMode) || 'quick'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState(0)
  const [conversationId, setConversationId] = useState<string>()
  const [lastFailedQuery, setLastFailedQuery] = useState<string>('')

  // 网络请求重试 hook
  const quickChatWithRetry = useNetworkRetry(quickChat, {
    maxRetries: 3,
    retryDelay: 1000,
    exponentialBackoff: true,
  })

  // Refs
  const eventSourceRef = useRef<EventSource | null>(null)

  // Handle mode change
  const handleModeChange = (newMode: ChatMode) => {
    setMode(newMode)
    localStorage.setItem('chatMode', newMode)
  }

  // Handle send message
  const handleSendMessage = async (userInput: string) => {
    if (!userInput.trim()) return

    // 开始性能监控事务（暂时简化）
    Sentry.startTransaction(`chat-${mode}`, 'chat')
    // 注意：在新版本中，性能监控已简化

    // 添加面包屑导航
    Sentry.addBreadcrumb({
      message: 'User sent chat message',
      category: 'chat',
      level: 'info',
      data: {
        mode,
        queryLength: userInput.length,
        messageCount: messages.length,
      },
    })

    // Clear input immediately
    setInputValue('')
    setLastFailedQuery('') // 清除之前的失败查询

    // Add user message
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
        // Quick Chat mode with retry
        const response = await quickChatWithRetry.execute({
          query: userInput,
          conversation_id: conversationId,
        })

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.content,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, assistantMessage])
        setConversationId(response.session_id)

        // 记录成功的面包屑
        Sentry.addBreadcrumb({
          message: 'Quick chat completed successfully',
          category: 'chat',
          level: 'info',
          data: {
            responseLength: response.content.length,
            sessionId: response.session_id,
          },
        })
      } else {
        // Deep Research mode (SSE streaming)
        handleDeepResearchStream(userInput)
      }

      // 完成事务（在新版本中已简化）
      // transaction.finish() // 新版本中已不需要
    } catch (error) {
      console.error('Error sending message:', error)

      // 记录错误到 Sentry
      if (error instanceof Error) {
        Sentry.captureException(error, {
          query: userInput,
          mode,
          conversationId,
          retryCount: quickChatWithRetry.state.retryCount,
        })
      }

      // 添加面包屑导航用于调试
      Sentry.addBreadcrumb({
        message: 'Chat message failed',
        category: 'chat',
        level: 'error',
        data: {
          query: userInput,
          mode,
          retryCount: quickChatWithRetry.state.retryCount,
        },
      })

      setLastFailedQuery(userInput) // 保存失败的查询用于重试

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

  // 重试最后一次失败的请求
  const handleRetry = async () => {
    if (!lastFailedQuery.trim()) return

    // 移除最后一条错误消息
    setMessages((prev) => {
      const newMessages = [...prev]
      if (newMessages.length > 0 && newMessages[newMessages.length - 1].content.includes('❌ 抱歉，发生错误')) {
        newMessages.pop()
      }
      return newMessages
    })

    // 重新发送请求
    await handleSendMessage(lastFailedQuery)
  }

  // 重置错误状态（保留供未来使用）
  // const resetError = () => {
  //   setLastFailedQuery('')
  //   quickChatWithRetry.reset()
  // }

  // Handle Deep Research streaming
  const handleDeepResearchStream = (query: string) => {
    // Create placeholder message
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    }
    setMessages((prev) => [...prev, assistantMessage])

    // Create EventSource
    const eventSource = deepResearchStream({
      query,
      conversation_id: conversationId,
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

        // Handle different types of SSE events
        if (data.type === 'progress') {
          // Update loading stage based on progress
          if (data.stage === 'data_collection') {
            setLoadingStage(1)
          } else if (data.stage === 'analysis') {
            setLoadingStage(2)
          } else if (data.stage === 'report_generation') {
            setLoadingStage(3)
          }

          // Show progress message in content
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id
                ? { ...msg, content: data.content || `${loadingStages[loadingStage] || '处理中...'}` }
                : msg
            )
          )
        } else if (data.type === 'content') {
          // Append actual content
          if (data.content) {
            accumulatedContent = data.content // Replace with full content
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessage.id
                  ? { ...msg, content: accumulatedContent }
                  : msg
              )
            )
          }
        } else if (data.type === 'error') {
          // Handle error
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id
                ? {
                    ...msg,
                    content: `❌ 错误：${data.content}`,
                    isStreaming: false,
                  }
                : msg
            )
          )
          setIsLoading(false)
          eventSource.close()
          eventSourceRef.current = null
          return
        } else if (data.type === 'complete' || data.done) {
          // Handle completion
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id
                ? { ...msg, isStreaming: false }
                : msg
            )
          )
          setIsLoading(false)
          if (data.session_id) {
            setConversationId(data.session_id)
          }
          eventSource.close()
          eventSourceRef.current = null
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error)

      // Check if it's a connection error that might be worth retrying
      if (eventSource.readyState === EventSource.CLOSED) {
        // Optionally implement retry logic here
        console.log('EventSource connection closed')
      }

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
  }

  // Cleanup on unmount and mode change
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [mode])

  return (
    <div className="flex flex-col h-full bg-card rounded-xl shadow-sm border animate-fade-in">
      {/* Mode Switch */}
      <div className="px-4 py-3 sm:px-6 border-b no-print">
        <ModeSwitch mode={mode} onChange={handleModeChange} />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 sm:px-6 sm:py-4 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col">
            {/* 热点面板 */}
            <HotspotPanel
              onSelectHotspot={(symbol, name) => {
                setInputValue(`${symbol} (${name})`)
              }}
            />

            {/* 欢迎信息 */}
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-lg px-2">
                <div className="mb-4 sm:mb-6">
                  <div className="text-4xl sm:text-5xl mb-3 animate-bounce-subtle">👋</div>
                  <h2 className="text-xl sm:text-2xl font-bold text-foreground mb-3 sm:mb-4">
                    欢迎使用 Web3 AI 搜索引擎
                  </h2>
                  <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6 max-w-md mx-auto">
                    {mode === 'quick'
                      ? '输入问题，3秒内获得快速回答'
                      : '输入项目名称，生成30秒深度研究报告'}
                  </p>
                </div>

                <Card className="text-left p-4 sm:p-6 bg-muted/30 border-muted">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                      <span className="text-sm">💡</span>
                    </div>
                    <p className="text-sm font-medium text-foreground">
                      试试这些问题：
                    </p>
                  </div>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li className="flex items-start gap-2">
                      <span className="text-primary mt-0.5">•</span>
                      <span>分析比特币最近的价格走势</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary mt-0.5">•</span>
                      <span>ETH 的链上数据如何？</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary mt-0.5">•</span>
                      <span>UNI 和其他 DEX 代币对比</span>
                    </li>
                  </ul>
                </Card>
              </div>
            </div>
          </div>
        ) : (
          <>
            <MessageList messages={messages} />

            {/* 网络错误重试组件 */}
            {quickChatWithRetry.state.error && lastFailedQuery && (
              <NetworkErrorRetry
                onRetry={handleRetry}
                error={quickChatWithRetry.state.error}
                isRetrying={quickChatWithRetry.state.isLoading}
                retryCount={quickChatWithRetry.state.retryCount}
              />
            )}

            {isLoading && <LoadingAnimation stage={loadingStage} mode={mode} />}
          </>
        )}
      </div>

      {/* Input Box */}
      <div className="border-t p-3 sm:p-4 no-print bg-card/50 backdrop-blur-sm supports-[backdrop-filter]:bg-card/60">
        <AutocompleteInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSendMessage}
          disabled={isLoading}
          placeholder={
            mode === 'quick'
              ? '输入你的问题...'
              : '输入加密货币项目名称（如：BTC, ETH, UNI）...'
          }
        />
      </div>
    </div>
  )
}

export default ChatInterface
