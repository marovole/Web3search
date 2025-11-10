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
  Star
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
        "w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200",
        "hover:bg-muted/50 active:bg-muted/80",
        "touch-manipulation", // Improve touch responsiveness
        isActive && "bg-primary/10 text-primary border-r-2 border-primary",
        !isActive && "text-foreground/80 hover:text-foreground"
      )}
    >
      <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
        {icon}
      </span>

      <span className="flex-1 text-left text-sm font-medium truncate">
        {label}
      </span>

      {badge && (
        <span className="flex-shrink-0 bg-primary/20 text-primary text-xs px-2 py-1 rounded-full">
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
    touchStartX.current = e.targetTouches[0].clientX
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    touchEndX.current = e.changedTouches[0].clientX
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
      {/* Overlay for mobile - 使用 CSS transitions 替代 framer-motion */}
      {isMobile && isOpen && (
        <div
          className={cn(
            "fixed inset-0 bg-black/50 z-40 md:hidden",
            "transition-opacity duration-200",
            isOpen ? "opacity-100" : "opacity-0"
          )}
          onClick={onToggle}
        />
      )}

      {/* Sidebar - 使用 CSS transitions 替代 framer-motion */}
      <aside
        ref={sidebarRef}
        className={cn(
          "fixed left-0 top-0 h-full z-50",
          "bg-card border-r border-border",
          "flex flex-col",
          "transition-all duration-300 ease-in-out",
          // Desktop styles
          "md:w-64",
          // Mobile styles
          "w-64 md:relative",
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
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">
            Web3Search
          </h2>

          <button
            onClick={onToggle}
            className={cn(
              "p-2 rounded-lg transition-all duration-200",
              "hover:bg-muted/50 active:bg-muted/80",
              "touch-manipulation",
              "text-foreground/60 hover:text-foreground"
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
        <nav className="flex-1 overflow-y-auto p-4 space-y-2">
          <div className="mb-6">
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3 px-3">
              主要功能
            </h3>
            <div className="space-y-1">
              {menuItems.slice(0, 6).map((item) => (
                <SidebarItem key={item.href} {...item} />
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3 px-3">
              其他
            </h3>
            <div className="space-y-1">
              {menuItems.slice(6).map((item) => (
                <SidebarItem key={item.href} {...item} />
              ))}
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border space-y-3">
          {/* 快捷键帮助按钮 */}
          <button
            onClick={toggleHelp}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200",
              "hover:bg-muted/50 active:bg-muted/80",
              "touch-manipulation",
              "text-foreground/60 hover:text-foreground",
              "text-sm"
            )}
            aria-label="显示快捷键帮助"
          >
            <Command size={18} />
            <span className="flex-1 text-left">快捷键帮助</span>
            <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs font-mono">
              ?
            </kbd>
          </button>

          <div className="text-xs text-muted-foreground pt-2 border-t border-border">
            <p>© 2024 Web3Search</p>
            <p className="mt-1">构建在Web3技术之上</p>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar