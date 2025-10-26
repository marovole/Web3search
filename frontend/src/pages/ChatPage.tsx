import React from 'react'
import ChatInterface from '../components/Chat/ChatInterface'

const ChatPage: React.FC = () => {
  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 no-print">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary">
            Web3 AI Search Engine
          </h1>
          <p className="text-sm text-gray-600">
            免费 · 开源 · 专业级
          </p>
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
