/**
 * Agent Chat Page
 * Conversational AI interface for creating and managing agent tasks
 */

import React, { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useAgentChat } from '../hooks/useAgentChat'
import { AgentChatMessage, AgentChatInput } from '../components/Agent'
import type { AgentChatMessage as AgentChatMessageType } from '../types/agent-chat'

const AgentChatPage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const {
    messages,
    isLoading,
    isConnected,
    sendMessage,
    confirmIntent,
    cancelIntent,
    clearMessages,
    pendingConfirmation,
  } = useAgentChat({
    onError: (error) => console.error('[AgentChat] Error:', error),
  })

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auth guard
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-gray-800 rounded-2xl shadow-xl p-8 text-center border border-gray-700">
          <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">AI 助手</h2>
          <p className="text-gray-400 mb-6">
            登录后即可与 AI 助手对话，创建价格提醒、风险监控等智能任务。
          </p>
          <button
            onClick={() => navigate('/auth/login')}
            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors"
          >
            立即登录
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="flex-shrink-0 bg-gray-800/80 backdrop-blur-sm border-b border-gray-700/50 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-lg font-semibold text-white">AI 助手</h1>
              <p className="text-xs text-gray-400">
                {isConnected ? '在线' : '离线'}
                <span className={`inline-block w-1.5 h-1.5 rounded-full ml-1.5 ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/agents')}
              className="px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors"
            >
              任务管理
            </button>
            {messages.length > 0 && (
              <button
                onClick={clearMessages}
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors"
              >
                新对话
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {messages.length === 0 ? (
            // Welcome State
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center mb-6">
                <svg className="w-10 h-10 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">我是您的 AI 助手</h2>
              <p className="text-gray-400 max-w-md mb-8">
                用自然语言告诉我您的需求，我可以帮您创建价格提醒、监控风险、分析持仓、发现投资机会。
              </p>
              
              {/* Quick Actions */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-2xl">
                {[
                  { icon: '📊', label: '价格提醒', example: '当BTC跌破50000时提醒我' },
                  { icon: '⚠️', label: '风险监控', example: '帮我监控ETH的风险变化' },
                  { icon: '📈', label: '持仓诊断', example: '分析一下我的持仓' },
                  { icon: '💡', label: '机会发现', example: '有什么推荐的项目吗' },
                  { icon: '💰', label: '查询价格', example: 'BTC现在多少钱' },
                  { icon: '📋', label: '查看任务', example: '查看我的所有任务' },
                ].map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(action.example)}
                    className="p-4 bg-gray-800/50 hover:bg-gray-800 border border-gray-700/50 hover:border-gray-600 rounded-xl text-left transition-all group"
                  >
                    <span className="text-2xl mb-2 block">{action.icon}</span>
                    <span className="text-sm font-medium text-white block mb-1">{action.label}</span>
                    <span className="text-xs text-gray-500 group-hover:text-gray-400 transition-colors">{action.example}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            // Messages List
            <div className="space-y-2">
              {messages.map((msg: AgentChatMessageType, idx: number) => (
                <AgentChatMessage
                  key={msg.id}
                  message={msg}
                  showConfirmButtons={pendingConfirmation?.id === msg.id}
                  onConfirm={confirmIntent}
                  onCancel={cancelIntent}
                />
              ))}
              
              {/* Loading Indicator */}
              {isLoading && (
                <div className="flex justify-start mb-4">
                  <div className="bg-gray-800/80 border border-gray-700/50 rounded-2xl rounded-bl-md px-4 py-3">
                    <div className="flex items-center gap-2 text-gray-400">
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      <span className="text-sm">正在思考...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </main>

      {/* Input Area */}
      <footer className="flex-shrink-0 bg-gray-800/50 backdrop-blur-sm border-t border-gray-700/50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <AgentChatInput
            onSend={sendMessage}
            disabled={isLoading}
          />
          <p className="text-center text-xs text-gray-500 mt-3">
            AI 助手可能会产生错误信息，请自行验证重要内容
          </p>
        </div>
      </footer>
    </div>
  )
}

export default AgentChatPage
