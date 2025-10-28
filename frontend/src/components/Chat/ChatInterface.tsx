import React, { useState, useRef, useEffect } from 'react'
import type { Message, ChatMode } from '../../types'
import { quickChat, deepResearchStream } from '../../services/api'
import ModeSwitch from './ModeSwitch'
import MessageList from './MessageList'
import AutocompleteInput from './AutocompleteInput'
import LoadingAnimation from '../Shared/LoadingAnimation'
import HotspotPanel from '../Hotspot/HotspotPanel'

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

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Handle mode change
  const handleModeChange = (newMode: ChatMode) => {
    setMode(newMode)
    localStorage.setItem('chatMode', newMode)
  }

  // Handle send message
  const handleSendMessage = async (userInput: string) => {
    if (!userInput.trim()) return

    // Clear input immediately
    setInputValue('')

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
        // Quick Chat mode
        const response = await quickChat({
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
      } else {
        // Deep Research mode (SSE streaming)
        handleDeepResearchStream(userInput)
      }
    } catch (error) {
      console.error('Error sending message:', error)
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

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Mode Switch */}
      <div className="px-6 py-4 border-b border-gray-200 no-print">
        <ModeSwitch mode={mode} onChange={handleModeChange} />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 custom-scrollbar">
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
              <div className="text-center max-w-md">
                <h2 className="text-2xl font-bold text-gray-800 mb-4">
                  👋 欢迎使用 Web3 AI 搜索引擎
                </h2>
                <p className="text-gray-600 mb-6">
                  {mode === 'quick'
                    ? '输入问题，3秒内获得快速回答'
                    : '输入项目名称，生成30秒深度研究报告'}
                </p>
                <div className="text-left bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-700 font-medium mb-2">
                    💡 试试这些问题：
                  </p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• 分析比特币最近的价格走势</li>
                    <li>• ETH 的链上数据如何？</li>
                    <li>• UNI 和其他 DEX 代币对比</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            <MessageList messages={messages} />
            {isLoading && <LoadingAnimation stage={loadingStage} mode={mode} />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Box */}
      <div className="border-t border-gray-200 p-4 no-print">
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
