/**
 * useAgentChat Hook
 * Manages conversational AI chat state and API interactions
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import type { 
  AgentChatMessage, 
  SendMessageResponse, 
  ParsedIntent,
  TaskCreationResult 
} from '../types/agent-chat'

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || ''

interface UseAgentChatOptions {
  conversationId?: string
  onError?: (error: string) => void
}

interface UseAgentChatReturn {
  messages: AgentChatMessage[]
  isLoading: boolean
  isConnected: boolean
  conversationId: string | null
  sendMessage: (message: string, confirmIntent?: boolean) => Promise<void>
  confirmIntent: () => Promise<void>
  cancelIntent: () => void
  clearMessages: () => void
  pendingConfirmation: AgentChatMessage | null
}

export function useAgentChat(options: UseAgentChatOptions = {}): UseAgentChatReturn {
  const { token } = useAuth()
  const [messages, setMessages] = useState<AgentChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(true)
  const [conversationId, setConversationId] = useState<string | null>(options.conversationId || null)
  const [pendingConfirmation, setPendingConfirmation] = useState<AgentChatMessage | null>(null)
  
  const abortControllerRef = useRef<AbortController | null>(null)
  const lastMessageRef = useRef<string>('')

  // Load conversation history on mount
  useEffect(() => {
    if (conversationId && token) {
      loadHistory(conversationId)
    }
  }, [conversationId, token])

  const loadHistory = async (convId: string) => {
    if (!token) return

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/agents/conversation/history?conversationId=${convId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        if (data.messages?.length > 0) {
          const loadedMessages: AgentChatMessage[] = data.messages.map((m: Record<string, unknown>) => ({
            id: m.id as string,
            role: m.role as 'user' | 'assistant' | 'system',
            content: m.content as string,
            timestamp: new Date(m.created_at as string),
            intent: m.intent ? JSON.parse(m.intent as string) : undefined,
            taskResult: m.task_result ? JSON.parse(m.task_result as string) : undefined,
          }))
          setMessages(loadedMessages.reverse())
        }
      }
    } catch (error) {
      console.error('[useAgentChat] Failed to load history:', error)
    }
  }

  const addMessage = useCallback((message: AgentChatMessage) => {
    setMessages(prev => [...prev, message])
  }, [])

  const updateLastMessage = useCallback((updates: Partial<AgentChatMessage>) => {
    setMessages(prev => {
      const newMessages = [...prev]
      const lastIdx = newMessages.length - 1
      if (lastIdx >= 0) {
        newMessages[lastIdx] = { ...newMessages[lastIdx], ...updates }
      }
      return newMessages
    })
  }, [])

  const sendMessage = useCallback(async (message: string, confirmIntent = false) => {
    if (!token) {
      options.onError?.('请先登录')
      return
    }

    if (!message.trim() && !confirmIntent) return

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setIsLoading(true)
    lastMessageRef.current = message

    // Add user message to chat
    if (!confirmIntent) {
      const userMessage: AgentChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: message,
        timestamp: new Date(),
      }
      addMessage(userMessage)
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/agents/conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: confirmIntent ? lastMessageRef.current : message,
          conversationId: conversationId,
          confirmIntent,
        }),
        signal: abortControllerRef.current.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: SendMessageResponse = await response.json()
      
      // Update conversation ID
      if (data.conversationId && !conversationId) {
        setConversationId(data.conversationId)
      }

      // Create assistant message
      const assistantMessage: AgentChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        intent: data.intent,
        taskResult: data.taskResult,
        requiresConfirmation: data.requiresConfirmation,
        confirmationDetails: data.confirmationDetails,
      }

      addMessage(assistantMessage)

      // If requires confirmation, store the pending message
      if (data.requiresConfirmation) {
        setPendingConfirmation(assistantMessage)
      } else {
        setPendingConfirmation(null)
      }

      setIsConnected(true)
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        return
      }

      console.error('[useAgentChat] Send error:', error)
      setIsConnected(false)

      const errorMessage: AgentChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '抱歉，处理您的请求时出现错误。请稍后重试。',
        timestamp: new Date(),
      }
      addMessage(errorMessage)

      options.onError?.(error instanceof Error ? error.message : '发送消息失败')
    } finally {
      setIsLoading(false)
    }
  }, [token, conversationId, addMessage, options])

  const confirmIntent = useCallback(async () => {
    if (!pendingConfirmation) return
    await sendMessage(lastMessageRef.current, true)
    setPendingConfirmation(null)
  }, [pendingConfirmation, sendMessage])

  const cancelIntent = useCallback(() => {
    setPendingConfirmation(null)
    const cancelMessage: AgentChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '好的，已取消操作。您可以继续告诉我其他需求。',
      timestamp: new Date(),
    }
    addMessage(cancelMessage)
  }, [addMessage])

  const clearMessages = useCallback(() => {
    setMessages([])
    setConversationId(null)
    setPendingConfirmation(null)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  return {
    messages,
    isLoading,
    isConnected,
    conversationId,
    sendMessage,
    confirmIntent,
    cancelIntent,
    clearMessages,
    pendingConfirmation,
  }
}

export default useAgentChat
