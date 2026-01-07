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
        "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative overflow-hidden",
        "hover:bg-muted/40",
        isActive
          ? "bg-primary/[0.08] text-foreground"
          : "text-muted-foreground hover:text-foreground"
      )}
    >
      {/* Active indicator line */}
      <span className={cn(
        "absolute left-0 top-1/2 -translate-y-1/2 w-0.5 rounded-r transition-all duration-250",
        isActive ? "h-5 bg-primary shadow-glow-sm" : "h-0 bg-transparent"
      )} />

      <span className={cn(
        "flex-shrink-0 w-5 h-5 flex items-center justify-center transition-colors duration-200",
        isActive ? "text-primary" : "group-hover:text-foreground"
      )}>
        {icon}
      </span>

      <span className={cn(
        "flex-1 text-left text-sm truncate transition-colors duration-200",
        isActive ? "font-semibold text-foreground" : "font-medium"
      )}>
        {label}
      </span>

      {badge && (
        <span className={cn(
          "flex-shrink-0 text-[10px] font-mono px-1.5 py-0.5 rounded-md transition-colors duration-200",
          isActive
            ? "bg-primary/20 text-primary"
            : "bg-muted/60 text-muted-foreground"
        )}>
          {badge}
        </span>
      )}

      {/* Subtle hover glow */}
      {isActive && (
        <span className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent pointer-events-none" />
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
          "bg-surface-1/95 backdrop-blur-2xl border-r border-border/50",
          "flex flex-col",
          "transition-all duration-250 ease-out-expo",
          "md:w-64 w-64",
          isOpen
            ? "translate-x-0 opacity-100"
            : isMobile
              ? "-translate-x-full opacity-0"
              : "-translate-x-full md:translate-x-0 opacity-0 md:opacity-100"
        )}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-border/40">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary/25 to-primary/10 border border-primary/30 flex items-center justify-center shadow-glow-sm">
              <span className="font-mono font-bold text-primary text-sm">L</span>
            </div>
            <div>
              <h2 className="font-display font-bold text-foreground text-base tracking-tight">
                LULA
              </h2>
              <span className="font-mono text-[9px] text-muted-foreground/50 uppercase tracking-[0.2em]">
                Web3 Terminal
              </span>
            </div>
          </div>

          <button
            onClick={onToggle}
            className={cn(
              "p-2 rounded-lg transition-all duration-200",
              "hover:bg-muted/50 active:bg-muted/70",
              "text-muted-foreground hover:text-foreground"
            )}
            aria-label={isOpen ? "关闭侧边栏" : "打开侧边栏"}
          >
            {isMobile ? (
              <X size={18} />
            ) : isOpen ? (
              <ChevronLeft size={18} />
            ) : (
              <ChevronRight size={18} />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-5 space-y-6 custom-scrollbar">
          <div>
            <div className="flex items-center gap-2 mb-3 px-3">
              <span className="w-4 h-px bg-gradient-to-r from-primary/40 to-transparent" />
              <h3 className="text-[9px] font-mono font-medium text-muted-foreground/60 uppercase tracking-[0.2em]">
                Main
              </h3>
            </div>
            <div className="space-y-0.5">
              {menuItems.slice(0, 6).map((item) => (
                <SidebarItem key={item.href} {...item} />
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-3 px-3">
              <span className="w-4 h-px bg-gradient-to-r from-secondary/40 to-transparent" />
              <h3 className="text-[9px] font-mono font-medium text-muted-foreground/60 uppercase tracking-[0.2em]">
                Tools
              </h3>
            </div>
            <div className="space-y-0.5">
              {menuItems.slice(6).map((item) => (
                <SidebarItem key={item.href} {...item} />
              ))}
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="px-3 py-3 border-t border-border/40 space-y-2">
          {/* Keyboard Shortcuts */}
          <button
            onClick={toggleHelp}
            className={cn(
              "w-full flex items-center gap-2 px-3 py-2.5 rounded-xl transition-all duration-200",
              "hover:bg-muted/40 text-muted-foreground hover:text-foreground",
              "text-sm group"
            )}
            aria-label="显示快捷键帮助"
          >
            <Command size={15} className="group-hover:text-primary transition-colors duration-200" />
            <span className="flex-1 text-left text-sm font-medium">Shortcuts</span>
            <kbd className="kbd-hint">?</kbd>
          </button>

          <div className="text-[9px] font-mono text-muted-foreground/50 pt-1 text-center tracking-wider">
            <p>LULA v1.0 © 2024</p>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar