import React from 'react'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/theme-toggle'
import { useSidebar } from '@/hooks/useSidebar'
import { Menu } from 'lucide-react'
import ChatInterface from '../components/Chat/ChatInterface'

const ChatPage: React.FC = () => {
  const { toggle } = useSidebar()

  return (
    <div className="relative h-[calc(100vh-2rem)] md:h-screen overflow-hidden bg-transparent">
      {/* Minimal Top Bar - Floating */}
      <div className="absolute top-4 left-4 right-4 z-50 flex justify-between items-center pointer-events-none">
        <div className="pointer-events-auto">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggle}
            className="rounded-full bg-background/20 backdrop-blur-md border border-white/10 hover:bg-background/40 text-foreground hover:text-primary transition-colors"
            aria-label="Toggle Sidebar"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </div>

        <div className="pointer-events-auto">
          <ThemeToggle />
        </div>
      </div>

      {/* Main Content Area */}
      <main className="h-full w-full relative z-10">
        <ChatInterface />
      </main>

      {/* Dynamic Background Elements */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        {/* Primary Glow */}
        <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] animate-pulse-glow" />

        {/* Secondary Glow */}
        <div className="absolute bottom-[-20%] left-[-10%] w-[600px] h-[600px] bg-secondary/10 rounded-full blur-[120px] animate-pulse-glow" style={{ animationDelay: '1.5s' }} />

        {/* Accent Orbs */}
        <div className="absolute top-[20%] left-[10%] w-32 h-32 bg-primary/5 rounded-full blur-[50px] animate-float" />
        <div className="absolute bottom-[30%] right-[20%] w-48 h-48 bg-secondary/5 rounded-full blur-[60px] animate-float" style={{ animationDelay: '2s' }} />
      </div>
    </div>
  )
}

export default ChatPage
