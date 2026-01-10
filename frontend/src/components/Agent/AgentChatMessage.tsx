/**
 * AgentChatMessage Component
 * Displays a single message in the agent chat interface
 */

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import type { AgentChatMessage as AgentChatMessageType } from '@/types/agent-chat'
import { INTENT_DESCRIPTIONS } from '@/types/agent-chat'

interface AgentChatMessageProps {
  message: AgentChatMessageType
  onConfirm?: () => void
  onCancel?: () => void
  showConfirmButtons?: boolean
}

const AgentChatMessage: React.FC<AgentChatMessageProps> = ({
  message,
  onConfirm,
  onCancel,
  showConfirmButtons = false,
}) => {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'

  // Get intent badge color
  const getIntentColor = (intentType: string) => {
    if (intentType.startsWith('create_')) return 'bg-green-500/20 text-green-400 border-green-500/30'
    if (intentType.startsWith('delete_') || intentType.startsWith('pause_')) return 'bg-red-500/20 text-red-400 border-red-500/30'
    if (intentType.startsWith('check_') || intentType.startsWith('get_') || intentType.startsWith('list_')) return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
    return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  }

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <div className="px-4 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-full text-xs text-yellow-400">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className={cn(
      "flex w-full mb-4 animate-fade-in",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "max-w-[85%] md:max-w-[75%] rounded-2xl px-4 py-3",
        isUser 
          ? "bg-blue-600 text-white rounded-br-md" 
          : "bg-gray-800/80 border border-gray-700/50 text-gray-100 rounded-bl-md"
      )}>
        {/* Intent Badge */}
        {!isUser && message.intent && (
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-700/30">
            <span className={cn(
              "text-xs px-2 py-0.5 rounded-full border",
              getIntentColor(message.intent.type)
            )}>
              {INTENT_DESCRIPTIONS[message.intent.type] || message.intent.type}
            </span>
            <span className="text-xs text-gray-500">
              置信度: {Math.round(message.intent.confidence * 100)}%
            </span>
          </div>
        )}

        {/* Message Content */}
        {isUser ? (
          <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        ) : (
          <div className="prose prose-sm prose-invert max-w-none
            prose-p:text-gray-200 prose-p:my-1
            prose-li:text-gray-200 prose-li:my-0.5
            prose-strong:text-white
            prose-code:text-blue-300 prose-code:bg-blue-900/30 prose-code:px-1 prose-code:rounded
          ">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Task Result Success Indicator */}
        {message.taskResult?.success && (
          <div className="mt-3 pt-2 border-t border-gray-700/30 flex items-center gap-2 text-green-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-xs">任务已创建</span>
          </div>
        )}

        {/* Confirmation Buttons */}
        {showConfirmButtons && message.requiresConfirmation && (
          <div className="mt-4 pt-3 border-t border-gray-700/30 flex gap-2">
            <button
              onClick={onConfirm}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              确认创建
            </button>
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm font-medium rounded-lg transition-colors"
            >
              取消
            </button>
          </div>
        )}

        {/* Timestamp */}
        <div className={cn(
          "text-xs mt-2 opacity-60",
          isUser ? "text-blue-100" : "text-gray-400"
        )}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  )
}

export default AgentChatMessage
