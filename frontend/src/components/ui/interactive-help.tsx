import React, { useState, useEffect, useRef, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { 
  HelpCircle, 
  X, 
  Info, 
  AlertTriangle, 
  CheckCircle,
  Lightbulb,
  BookOpen,
  Video,
  MessageSquare,
  Search,
  ExternalLink
} from 'lucide-react'

/**
 * 工具提示位置
 */
export type TooltipPosition = 
  | 'top' 
  | 'bottom' 
  | 'left' 
  | 'right'
  | 'top-start'
  | 'top-end'
  | 'bottom-start'
  | 'bottom-end'
  | 'left-start'
  | 'left-end'
  | 'right-start'
  | 'right-end'

/**
 * 工具提示类型
 */
export type TooltipType = 'info' | 'warning' | 'success' | 'error' | 'help'

/**
 * 工具提示配置
 */
export interface TooltipConfig {
  content: React.ReactNode
  position?: TooltipPosition
  type?: TooltipType
  trigger?: 'hover' | 'click' | 'focus' | 'manual'
  delay?: number
  hideDelay?: number
  arrow?: boolean
  maxWidth?: number
  persistent?: boolean
  disabled?: boolean
}

/**
 * 工具提示组件
 */
export const Tooltip: React.FC<{
  children: React.ReactNode
  config: TooltipConfig
  className?: string
}> = ({ children, config, className }) => {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const triggerRef = useRef<HTMLElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout>()

  const {
    content,
    position: desiredPosition = 'top',
    type = 'info',
    trigger = 'hover',
    delay = 300,
    hideDelay = 100,
    arrow = true,
    maxWidth = 300,
    persistent = false,
    disabled = false
  } = config

  const typeConfig = {
    info: { icon: <Info className="w-4 h-4" />, bgColor: 'bg-blue-50', borderColor: 'border-blue-200', textColor: 'text-blue-700' },
    warning: { icon: <AlertTriangle className="w-4 h-4" />, bgColor: 'bg-yellow-50', borderColor: 'border-yellow-200', textColor: 'text-yellow-700' },
    success: { icon: <CheckCircle className="w-4 h-4" />, bgColor: 'bg-green-50', borderColor: 'border-green-200', textColor: 'text-green-700' },
    error: { icon: <AlertTriangle className="w-4 h-4" />, bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-700' },
    help: { icon: <HelpCircle className="w-4 h-4" />, bgColor: 'bg-purple-50', borderColor: 'border-purple-200', textColor: 'text-purple-700' }
  }

  const currentTypeConfig = typeConfig[type]

  const calculatePosition = useCallback(() => {
    if (!triggerRef.current || !tooltipRef.current) return

    const triggerRect = triggerRef.current.getBoundingClientRect()
    const tooltipRect = tooltipRef.current.getBoundingClientRect()
    const viewport = {
      width: window.innerWidth,
      height: window.innerHeight
    }

    let top = 0
    let left = 0
    const offset = 8

    switch (desiredPosition) {
      case 'top':
        top = triggerRect.top - tooltipRect.height - offset
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
        break
      case 'bottom':
        top = triggerRect.bottom + offset
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2
        break
      case 'left':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
        left = triggerRect.left - tooltipRect.width - offset
        break
      case 'right':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2
        left = triggerRect.right + offset
        break
      case 'top-start':
        top = triggerRect.top - tooltipRect.height - offset
        left = triggerRect.left
        break
      case 'top-end':
        top = triggerRect.top - tooltipRect.height - offset
        left = triggerRect.right - tooltipRect.width
        break
      case 'bottom-start':
        top = triggerRect.bottom + offset
        left = triggerRect.left
        break
      case 'bottom-end':
        top = triggerRect.bottom + offset
        left = triggerRect.right - tooltipRect.width
        break
      case 'left-start':
        top = triggerRect.top
        left = triggerRect.left - tooltipRect.width - offset
        break
      case 'left-end':
        top = triggerRect.bottom - tooltipRect.height
        left = triggerRect.left - tooltipRect.width - offset
        break
      case 'right-start':
        top = triggerRect.top
        left = triggerRect.right + offset
        break
      case 'right-end':
        top = triggerRect.bottom - tooltipRect.height
        left = triggerRect.right + offset
        break
    }

    // 确保不超出视窗边界
    if (left < 10) left = 10
    if (left + tooltipRect.width > viewport.width - 10) {
      left = viewport.width - tooltipRect.width - 10
    }
    if (top < 10) top = 10
    if (top + tooltipRect.height > viewport.height - 10) {
      top = viewport.height - tooltipRect.height - 10
    }

    setPosition({ top, left })
  }, [desiredPosition])

  const show = useCallback(() => {
    if (disabled) return
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true)
      setTimeout(calculatePosition, 0)
    }, delay)
  }, [disabled, delay, calculatePosition])

  const hide = useCallback(() => {
    if (persistent) return
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    
    timeoutRef.current = setTimeout(() => {
      setIsVisible(false)
    }, hideDelay)
  }, [persistent, hideDelay])

  const handleMouseEnter = () => {
    if (trigger === 'hover') show()
  }

  const handleMouseLeave = () => {
    if (trigger === 'hover') hide()
  }

  const handleClick = () => {
    if (trigger === 'click') {
      setIsVisible(!isVisible)
    }
  }

  const handleFocus = () => {
    if (trigger === 'focus') show()
  }

  const handleBlur = () => {
    if (trigger === 'focus') hide()
  }

  useEffect(() => {
    const child = React.Children.only(children) as React.ReactElement
    const element = child.ref as React.RefObject<HTMLElement> || triggerRef
    
    if (element && element.current) {
      triggerRef.current = element.current
    }
  }, [children])

  useEffect(() => {
    if (isVisible) {
      calculatePosition()
      const handleResize = () => calculatePosition()
      window.addEventListener('resize', handleResize)
      window.addEventListener('scroll', handleResize)
      
      return () => {
        window.removeEventListener('resize', handleResize)
        window.removeEventListener('scroll', handleResize)
      }
    }
  }, [isVisible, calculatePosition])

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  const childElement = React.Children.only(children) as React.ReactElement
  const enhancedChild = React.cloneElement(childElement, {
    ref: triggerRef,
    onMouseEnter: handleMouseEnter,
    onMouseLeave: handleMouseLeave,
    onClick: handleClick,
    onFocus: handleFocus,
    onBlur: handleBlur
  })

  return (
    <>
      {enhancedChild}
      
      {isVisible && (
        <div
          ref={tooltipRef}
          className={cn(
            "fixed z-50 p-3 rounded-lg border shadow-lg animate-fade-in",
            currentTypeConfig.bgColor,
            currentTypeConfig.borderColor,
            className
          )}
          style={{
            top: position.top,
            left: position.left,
            maxWidth: maxWidth
          }}
        >
          <div className="flex items-start gap-2">
            <div className={cn("flex-shrink-0 mt-0.5", currentTypeConfig.textColor)}>
              {currentTypeConfig.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className={cn("text-sm", currentTypeConfig.textColor)}>
                {content}
              </div>
            </div>
            {!persistent && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsVisible(false)}
                className="flex-shrink-0 h-4 w-4 p-0 opacity-50 hover:opacity-100"
              >
                <X className="w-3 h-3" />
              </Button>
            )}
          </div>
          
          {arrow && (
            <div
              className={cn(
                "absolute w-2 h-2 bg-current border-current border transform rotate-45",
                currentTypeConfig.bgColor.replace('bg-', 'border-t-').replace('50', '200'),
                currentTypeConfig.borderColor
              )}
              style={{
                [desiredPosition.includes('top') ? 'bottom' : 
                 desiredPosition.includes('bottom') ? 'top' :
                 desiredPosition.includes('left') ? 'right' : 'left']: '-4px',
                [desiredPosition.includes('start') ? 'left' : 
                 desiredPosition.includes('end') ? 'right' : 'center']: '50%',
                transform: 'translateX(-50%) rotate(45deg)'
              }}
            />
          )}
        </div>
      )}
    </>
  )
}

/**
 * 上下文帮助组件
 */
export interface ContextHelpItem {
  id: string
  title: string
  content: React.ReactNode
  type?: 'article' | 'video' | 'faq' | 'tutorial'
  category?: string
  tags?: string[]
  related?: string[]
}

export const ContextHelp: React.FC<{
  items: ContextHelpItem[]
  searchPlaceholder?: string
  categories?: string[]
  className?: string
}> = ({ 
  items, 
  searchPlaceholder = "搜索帮助内容...",
  categories = [],
  className 
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [filteredItems, setFilteredItems] = useState(items)

  useEffect(() => {
    let filtered = items

    // 按搜索词过滤
    if (searchTerm) {
      filtered = filtered.filter(item =>
        item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    // 按分类过滤
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(item => item.category === selectedCategory)
    }

    setFilteredItems(filtered)
  }, [searchTerm, selectedCategory, items])

  const getTypeIcon = (type?: string) => {
    switch (type) {
      case 'video':
        return <Video className="w-4 h-4" />
      case 'faq':
        return <HelpCircle className="w-4 h-4" />
      case 'tutorial':
        return <BookOpen className="w-4 h-4" />
      default:
        return <Info className="w-4 h-4" />
    }
  }

  return (
    <Card className={cn("p-6 space-y-4", className)}>
      {/* 搜索和筛选 */}
      <div className="space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {categories.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={selectedCategory === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory('all')}
            >
              全部
            </Button>
            {categories.map(category => (
              <Button
                key={category}
                variant={selectedCategory === category ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* 帮助内容列表 */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredItems.length > 0 ? (
          filteredItems.map(item => (
            <div
              key={item.id}
              className="p-3 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 text-primary mt-1">
                  {getTypeIcon(item.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-foreground mb-1">
                    {item.title}
                  </h4>
                  <div className="text-sm text-muted-foreground">
                    {item.content}
                  </div>
                  
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex gap-1 mt-2">
                      {item.tags.map(tag => (
                        <span
                          key={tag}
                          className="text-xs px-2 py-1 bg-primary/10 text-primary rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <HelpCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>没有找到相关帮助内容</p>
          </div>
        )}
      </div>
    </Card>
  )
}

/**
 * 快速帮助按钮
 */
export const QuickHelpButton: React.FC<{
  onClick: () => void
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
  className?: string
}> = ({ onClick, position = 'bottom-right', className }) => {
  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4'
  }

  return (
    <Button
      onClick={onClick}
      className={cn(
        "fixed z-40 rounded-full w-12 h-12 shadow-lg",
        positionClasses[position],
        className
      )}
    >
      <HelpCircle className="w-5 h-5" />
    </Button>
  )
}

/**
 * 帮助模态框
 */
export const HelpModal: React.FC<{
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  className?: string
}> = ({ isOpen, onClose, title = "帮助中心", children, className }) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className={cn("w-full max-w-4xl max-h-[80vh] overflow-hidden", className)}>
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <HelpCircle className="w-6 h-6 text-primary" />
            <h2 className="text-xl font-semibold">{title}</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* 内容 */}
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </Card>
    </div>
  )
}

/**
 * 智能提示组件
 */
export const SmartTip: React.FC<{
  context: string
  onDismiss: () => void
  autoClose?: boolean
  duration?: number
  className?: string
}> = ({ 
  context, 
  onDismiss, 
  autoClose = true, 
  duration = 8000,
  className 
}) => {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(() => {
        setIsVisible(false)
        setTimeout(onDismiss, 300)
      }, duration)

      return () => clearTimeout(timer)
    }
  }, [autoClose, duration, onDismiss])

  if (!isVisible) return null

  return (
    <Card className={cn(
      "fixed bottom-4 right-4 z-40 w-80 p-4 shadow-lg animate-slide-in",
      className
    )}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 text-blue-500">
          <Lightbulb className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-foreground text-sm mb-1">
            智能提示
          </h4>
          <p className="text-xs text-muted-foreground">
            {context}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setIsVisible(false)
            setTimeout(onDismiss, 300)
          }}
          className="flex-shrink-0 h-6 w-6 p-0"
        >
          <X className="w-3 h-3" />
        </Button>
      </div>
    </Card>
  )
}

/**
 * 帮助系统Hook
 */
export const useHelpSystem = () => {
  const [isHelpOpen, setIsHelpOpen] = useState(false)
  const [currentContext, setCurrentContext] = useState<string>('')
  const [showSmartTip, setShowSmartTip] = useState(false)
  const [smartTipContent, setSmartTipContent] = useState('')

  const openHelp = useCallback((context?: string) => {
    if (context) {
      setCurrentContext(context)
    }
    setIsHelpOpen(true)
  }, [])

  const closeHelp = useCallback(() => {
    setIsHelpOpen(false)
    setCurrentContext('')
  }, [])

  const showSmartTip = useCallback((content: string) => {
    setSmartTipContent(content)
    setShowSmartTip(true)
  }, [])

  const hideSmartTip = useCallback(() => {
    setShowSmartTip(false)
    setSmartTipContent('')
  }, [])

  return {
    isHelpOpen,
    currentContext,
    showSmartTip: showSmartTip,
    smartTipContent,
    openHelp,
    closeHelp,
    showSmartTip: showSmartTip,
    hideSmartTip
  }
}

/**
 * 帮助提供者组件
 */
export const HelpProvider: React.FC<{
  children: React.ReactNode
  helpItems: ContextHelpItem[]
}> = ({ children, helpItems }) => {
  const helpSystem = useHelpSystem()

  return (
    <>
      {children}
      
      {/* 快速帮助按钮 */}
      <QuickHelpButton onClick={() => helpSystem.openHelp()} />
      
      {/* 帮助模态框 */}
      <HelpModal
        isOpen={helpSystem.isHelpOpen}
        onClose={helpSystem.closeHelp}
      >
        <ContextHelp items={helpItems} />
      </HelpModal>
      
      {/* 智能提示 */}
      {helpSystem.showSmartTip && (
        <SmartTip
          context={helpSystem.smartTipContent}
          onDismiss={helpSystem.hideSmartTip}
        />
      )}
    </>
  )
}
