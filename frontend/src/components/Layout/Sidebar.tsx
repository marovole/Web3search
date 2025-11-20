import React, { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import {
  MessageSquare,
  Search,
  Settings,
  X,
  ChevronLeft,
  ChevronRight,
  Home,
  BarChart3,
  FileText,
  Command,
  Code,
  Clock,
  Star,
  Menu
} from 'lucide-react'
import { useKeyboardShortcutsContext } from '@/contexts/KeyboardShortcutsContext'

interface SidebarItemProps {
  icon: React.ReactNode
  label: string
  href?: string
  isActive?: boolean
  onClick?: () => void
  badge?: string | number
  testId?: string
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  icon,
  label,
  href,
  isActive = false,
  onClick,
  badge,
  testId
}) => {
  const Component = href ? 'a' : 'button'

  return (
    <Component
      href={href}
      onClick={onClick}
      data-testid={testId}
      className={cn(
        "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden",
        "hover:bg-white/5",
        isActive
          ? "bg-primary/10 text-primary shadow-[0_0_15px_rgba(0,255,255,0.15)] border border-primary/20"
          : "text-muted-foreground hover:text-foreground hover:shadow-[0_0_10px_rgba(255,255,255,0.05)] border border-transparent"
      )}
    >
      {isActive && (
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary shadow-[0_0_10px_#00FFFF]" />
      )}

      <span className={cn(
        "flex-shrink-0 w-5 h-5 flex items-center justify-center transition-transform duration-300",
        isActive ? "scale-110 drop-shadow-[0_0_5px_rgba(0,255,255,0.5)]" : "group-hover:scale-110"
      )}>
        {icon}
      </span>

      <span className={cn(
        "flex-1 text-left text-sm font-medium truncate transition-all duration-300",
        isActive ? "translate-x-1" : "group-hover:translate-x-1"
      )}>
        {label}
      </span>

      {badge && (
        <span className={cn(
          "flex-shrink-0 text-xs px-2 py-0.5 rounded-full border",
          isActive
            ? "bg-primary/20 text-primary border-primary/30 shadow-[0_0_5px_rgba(0,255,255,0.2)]"
            : "bg-white/5 text-muted-foreground border-white/10"
        )}>
          {badge}
        </span>
      )}
    </Component>
  )
}

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  isMobile: boolean
  currentPath?: string
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  isMobile,
  currentPath = '/'
}) => {
  const sidebarRef = useRef<HTMLElement>(null)
  const touchStartX = useRef<number>(0)
  const touchEndX = useRef<number>(0)
  const { toggleHelp } = useKeyboardShortcutsContext()

  // Handle swipe gestures
  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.targetTouches[0]
    if (touch) {
      touchStartX.current = touch.clientX
    }
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    const touch = e.changedTouches[0]
    if (touch) {
      touchEndX.current = touch.clientX
    } else {
      return
    }
    const diff = touchStartX.current - touchEndX.current

    // Swipe threshold
    if (Math.abs(diff) > 50) {
      if (diff > 0 && isOpen && isMobile) {
        // Swipe left to close
        onToggle()
      } else if (diff < 0 && !isOpen && isMobile) {
        // Swipe right to open
        onToggle()
      }
    }
  }

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isMobile &&
        isOpen &&
        sidebarRef.current &&
        !sidebarRef.current.contains(event.target as Node)
      ) {
        onToggle()
      }
    }

    if (isMobile && isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
    return undefined
  }, [isMobile, isOpen, onToggle])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && isMobile) {
        onToggle()
      }
    }

    if (isMobile && isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
    return undefined
  }, [isMobile, isOpen, onToggle])

  const menuItems = [
    {
      icon: <Home size={18} />,
      label: '首页',
      href: '/',
      isActive: currentPath === '/'
    },
    {
      icon: <MessageSquare size={18} />,
      label: '对话',
      href: '/chat',
      isActive: currentPath === '/chat' || currentPath.startsWith('/chat/')
    },
    {
      icon: <Search size={18} />,
      label: '搜索',
      href: '/search',
      isActive: currentPath === '/search'
    },
    {
      icon: <Code size={18} />,
      label: 'GitHub搜索',
      href: '/github',
      isActive: currentPath === '/github'
    },
    {
      icon: <Clock size={18} />,
      label: '历史记录',
      href: '/history',
      isActive: currentPath === '/history',
      testId: 'sidebar-history'
    },
    {
      icon: <Star size={18} />,
      label: '监控列表',
      href: '/watchlist',
      isActive: currentPath === '/watchlist',
      testId: 'sidebar-watchlist'
    },
    {
      icon: <FileText size={18} />,
      label: '报告',
      href: '/reports',
      isActive: currentPath === '/reports'
    },
    {
      icon: <BarChart3 size={18} />,
      label: '分析',
      href: '/analytics',
      isActive: currentPath === '/analytics'
    },
    {
      icon: <Settings size={18} />,
      label: '设置',
      href: '/settings',
      isActive: currentPath === '/settings'
    }
  ]

  return (
    <>
      {/* Overlay for mobile */}
      {isMobile && isOpen && (
        <div
          className={cn(
            "fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden",
            "transition-opacity duration-300",
            isOpen ? "opacity-100" : "opacity-0"
          )}
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        ref={sidebarRef}
        className={cn(
          "fixed left-0 top-0 h-full z-50",
          "bg-background/60 backdrop-blur-xl border-r border-white/5 shadow-2xl", // Glassmorphism base
          "flex flex-col",
          "transition-all duration-300 ease-in-out",
          // Desktop styles
          "md:w-72", // Slightly wider for premium feel
          // Mobile styles
          "w-72",
          // Transform based on state
          isOpen
            ? "translate-x-0 opacity-100"
            : isMobile
              ? "-translate-x-full opacity-0"
              : "-translate-x-full md:translate-x-0 opacity-0 md:opacity-100"
        )}
        style={{
          transition: "transform 0.3s ease-in-out, opacity 0.3s ease-in-out"
        }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-[0_0_15px_rgba(0,255,255,0.3)]">
              <span className="font-bold text-black text-lg">W</span>
            </div>
            <h2 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-white/70 tracking-tight">
              Web3Search
            </h2>
          </div>

          <button
            onClick={onToggle}
            className={cn(
              "p-2 rounded-lg transition-all duration-200",
              "hover:bg-white/10 active:bg-white/20",
              "text-muted-foreground hover:text-foreground"
            )}
            aria-label={isOpen ? "关闭侧边栏" : "打开侧边栏"}
          >
            {isMobile ? (
              <X size={20} />
            ) : isOpen ? (
              <ChevronLeft size={20} />
            ) : (
              <ChevronRight size={20} />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
          <div>
            <h3 className="text-xs font-semibold text-primary/80 uppercase tracking-widest mb-4 px-4 neon-text">
              主要功能
            </h3>
            <div className="space-y-2">
              {menuItems.slice(0, 6).map((item) => (
                <SidebarItem key={item.href} {...item} />
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-xs font-semibold text-primary/80 uppercase tracking-widest mb-4 px-4 neon-text">
              其他
            </h3>
            <div className="space-y-2">
              {menuItems.slice(6).map((item) => (
                <SidebarItem key={item.href} {...item} />
              ))}
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-white/5 space-y-3 bg-black/20">
          {/* 快捷键帮助按钮 */}
          <button
            onClick={toggleHelp}
            className={cn(
              "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200",
              "bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10",
              "text-muted-foreground hover:text-foreground",
              "text-sm group"
            )}
            aria-label="显示快捷键帮助"
          >
            <Command size={18} className="group-hover:text-primary transition-colors" />
            <span className="flex-1 text-left">快捷键帮助</span>
            <kbd className="px-2 py-0.5 bg-black/40 rounded text-xs font-mono border border-white/10 text-primary/80">
              ?
            </kbd>
          </button>

          <div className="text-xs text-muted-foreground/60 pt-2 text-center">
            <p>© 2024 Web3Search</p>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar