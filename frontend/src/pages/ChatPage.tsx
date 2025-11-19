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
            className="rounded-full bg-background/20 backdrop-blur-md border border-white/10 hover:bg-background/40 text-foreground"
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
      <main className="h-full w-full relative">
        <ChatInterface />
      </main>
      
      {/* Background Elements (Optional extra flair) */}
      <div className="fixed inset-0 pointer-events-none z-[-1]">
        <div className="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] bg-primary/5 rounded-full blur-[100px]" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] bg-secondary/5 rounded-full blur-[100px]" />
      </div>
    </div>
  )
}

export default ChatPage
