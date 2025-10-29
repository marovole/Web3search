import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ThemeToggle } from '@/components/theme-toggle'
import { useSidebar } from '@/hooks/useSidebar'
import { Menu } from 'lucide-react'
import ChatInterface from '../components/Chat/ChatInterface'

const ChatPage: React.FC = () => {
  const navigate = useNavigate()
  const { toggle } = useSidebar()

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header - 简化设计，侧边栏承担导航功能 */}
      <header className="border-b bg-card/50 backdrop-blur-sm supports-[backdrop-filter]:bg-card/60 no-print">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Sidebar Toggle and Title */}
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggle}
              className="touch-manipulation"
              aria-label="切换侧边栏"
            >
              <Menu className="h-5 w-5" />
            </Button>

            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center">
                <span className="text-white font-bold text-sm">W3</span>
              </div>
              <h1 className="text-lg sm:text-xl font-bold text-foreground">
                Web3 AI Search
              </h1>
            </div>
          </div>

          {/* Right side actions */}
          <div className="flex items-center gap-2">
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Content - 优化的响应式布局 */}
      <main className="flex-1 overflow-hidden">
        <div className="h-full max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-4 sm:py-6">
          <ChatInterface />
        </div>
      </main>

      {/* Footer - 现代化设计 */}
      <footer className="border-t bg-card/30 backdrop-blur-sm supports-[backdrop-filter]:bg-card/40 no-print">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="text-center">
            <p className="text-xs sm:text-sm text-muted-foreground">
              Powered by OpenRouter AI · Data from CoinGecko, Twitter, Reddit, Etherscan
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default ChatPage