import React from 'react'
import { useNavigate } from 'react-router-dom'
import ChatInterface from '../components/Chat/ChatInterface'

const ChatPage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 no-print">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary">
            Web3 AI Search Engine
          </h1>

          <div className="flex items-center gap-4">
            {/* 导航按钮 */}
            <button
              onClick={() => navigate('/history')}
              className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-primary hover:bg-gray-100 rounded-lg transition-colors"
              title="历史记录"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="hidden md:inline text-sm">历史</span>
            </button>

            <button
              onClick={() => navigate('/watchlist')}
              className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-primary hover:bg-gray-100 rounded-lg transition-colors"
              title="监控列表"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
              <span className="hidden md:inline text-sm">监控</span>
            </button>

            <span className="text-sm text-gray-600 hidden lg:inline">
              免费 · 开源 · 专业级
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <div className="h-full max-w-7xl mx-auto px-4 py-6">
          <ChatInterface />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-6 py-3 no-print">
        <div className="max-w-7xl mx-auto text-center text-sm text-gray-500">
          <p>
            Powered by OpenRouter AI · Data from CoinGecko, Twitter, Reddit, Etherscan
          </p>
        </div>
      </footer>
    </div>
  )
}

export default ChatPage
