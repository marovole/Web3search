import React, { useEffect, useState, useCallback, useRef, forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { 
  Keyboard, 
  Volume2, 
  VolumeX, 
  Navigation, 
  Focus,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Tab,
  Enter,
  Escape,
  Space,
  Home,
  End,
  PageUp,
  PageDown,
  Play,
  Pause
} from 'lucide-react'

/**
 * 键盘导航配置
 */
export interface KeyboardNavigationConfig {
  enabled: boolean
  trapFocus: boolean
  wrapNavigation: boolean
  visualFocusIndicator: boolean
  announceFocus: boolean
  skipToContent: boolean
  focusShortcuts: Record<string, string>
}

/**
 * 屏幕阅读器配置
 */
export interface ScreenReaderConfig {
  enabled: boolean
  autoAnnounce: boolean
  verboseMode: boolean
  pauseAnimations: boolean
  announceErrors: boolean
  announceNavigation: boolean
  customLabels: Record<string, string>
}

/**
 * 焦点管理Hook
 */
export const useFocusManagement = (config: KeyboardNavigationConfig) => {
  const [focusedElement, setFocusedElement] = useState<HTMLElement | null>(null)
  const [focusHistory, setFocusHistory] = useState<HTMLElement[]>([])
  const focusableElementsRef = useRef<HTMLElement[]>([])

  // 获取可聚焦元素
  const getFocusableElements = useCallback((container: HTMLElement = document.body) => {
    const selectors = [
      'button:not([disabled])',
      'a[href]',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ')

    return Array.from(container.querySelectorAll(selectors)) as HTMLElement[]
  }, [])

  // 更新可聚焦元素列表
  const updateFocusableElements = useCallback(() => {
    focusableElementsRef.current = getFocusableElements()
  }, [getFocusableElements])

  // 设置焦点到元素
  const setFocus = useCallback((element: HTMLElement | null) => {
    if (element && config.enabled) {
      element.focus()
      setFocusedElement(element)
      setFocusHistory(prev => [...prev, element].slice(-10)) // 保留最近10个焦点历史
    }
  }, [config.enabled])

  // 移动焦点到下一个元素
  const focusNext = useCallback(() => {
    if (!config.enabled || focusableElementsRef.current.length === 0) return

    const currentIndex = focusableElementsRef.current.indexOf(
      focusedElement || document.activeElement as HTMLElement
    )
    
    let nextIndex = currentIndex + 1
    
    if (config.wrapNavigation && nextIndex >= focusableElementsRef.current.length) {
      nextIndex = 0
    } else if (nextIndex >= focusableElementsRef.current.length) {
      return
    }

    setFocus(focusableElementsRef.current[nextIndex])
  }, [config.enabled, config.wrapNavigation, focusedElement, setFocus])

  // 移动焦点到上一个元素
  const focusPrevious = useCallback(() => {
    if (!config.enabled || focusableElementsRef.current.length === 0) return

    const currentIndex = focusableElementsRef.current.indexOf(
      focusedElement || document.activeElement as HTMLElement
    )
    
    let prevIndex = currentIndex - 1
    
    if (config.wrapNavigation && prevIndex < 0) {
      prevIndex = focusableElementsRef.current.length - 1
    } else if (prevIndex < 0) {
      return
    }

    setFocus(focusableElementsRef.current[prevIndex])
  }, [config.enabled, config.wrapNavigation, focusedElement, setFocus])

  // 移动焦点到第一个元素
  const focusFirst = useCallback(() => {
    if (!config.enabled || focusableElementsRef.current.length === 0) return
    setFocus(focusableElementsRef.current[0])
  }, [config.enabled, setFocus])

  // 移动焦点到最后一个元素
  const focusLast = useCallback(() => {
    if (!config.enabled || focusableElementsRef.current.length === 0) return
    setFocus(focusableElementsRef.current[focusableElementsRef.current.length - 1])
  }, [config.enabled, setFocus])

  // 焦点陷阱
  const trapFocusInContainer = useCallback((container: HTMLElement) => {
    if (!config.trapFocus) return

    const focusableElements = getFocusableElements(container)
    if (focusableElements.length === 0) return

    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault()
            lastElement.focus()
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault()
            firstElement.focus()
          }
        }
      }
    }

    container.addEventListener('keydown', handleKeyDown)
    
    return () => {
      container.removeEventListener('keydown', handleKeyDown)
    }
  }, [config.trapFocus, getFocusableElements])

  // 初始化
  useEffect(() => {
    updateFocusableElements()
    
    // 监听DOM变化
    const observer = new MutationObserver(() => {
      updateFocusableElements()
    })
    
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['disabled', 'tabindex']
    })

    return () => {
      observer.disconnect()
    }
  }, [updateFocusableElements])

  return {
    focusedElement,
    focusHistory,
    focusableElements: focusableElementsRef.current,
    setFocus,
    focusNext,
    focusPrevious,
    focusFirst,
    focusLast,
    trapFocusInContainer,
    updateFocusableElements
  }
}

/**
 * 屏幕阅读器Hook
 */
export const useScreenReader = (config: ScreenReaderConfig) => {
  const [isReading, setIsReading] = useState(false)
  const [announcementQueue, setAnnouncementQueue] = useState<string[]>([])
  const announcerRef = useRef<HTMLDivElement>(null)

  // 通知屏幕阅读器
  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!config.enabled) return

    if (config.autoAnnounce) {
      // 自动通知模式
      if (announcerRef.current) {
        announcerRef.current.setAttribute('aria-live', priority)
        announcerRef.current.textContent = message
        
        // 清除消息以便下次可以重复通知相同内容
        setTimeout(() => {
          if (announcerRef.current) {
            announcerRef.current.textContent = ''
          }
        }, 1000)
      }
    } else {
      // 手动通知模式，添加到队列
      setAnnouncementQueue(prev => [...prev, message])
    }
  }, [config.enabled, config.autoAnnounce])

  // 通知错误
  const announceError = useCallback((message: string) => {
    if (config.announceErrors) {
      announce(`错误: ${message}`, 'assertive')
    }
  }, [announce, config.announceErrors])

  // 通知导航
  const announceNavigation = useCallback((destination: string) => {
    if (config.announceNavigation) {
      announce(`导航到: ${destination}`, 'polite')
    }
  }, [announce, config.announceNavigation])

  // 通知焦点变化
  const announceFocus = useCallback((element: HTMLElement) => {
    if (config.announceFocus) {
      const label = element.getAttribute('aria-label') || 
                   element.getAttribute('title') || 
                   element.textContent?.trim() || 
                   element.tagName.toLowerCase()
      
      announce(`聚焦到: ${label}`, 'polite')
    }
  }, [announce, config.announceFocus])

  // 开始/停止阅读
  const toggleReading = useCallback(() => {
    setIsReading(prev => !prev)
  }, [])

  // 播报队列中的下一条消息
  const playNextAnnouncement = useCallback(() => {
    if (announcementQueue.length > 0) {
      const [next, ...rest] = announcementQueue
      setAnnouncementQueue(rest)
      announce(next)
    }
  }, [announcementQueue, announce])

  // 清空通知队列
  const clearAnnouncements = useCallback(() => {
    setAnnouncementQueue([])
  }, [])

  return {
    isReading,
    announcementQueue,
    announce,
    announceError,
    announceNavigation,
    announceFocus,
    toggleReading,
    playNextAnnouncement,
    clearAnnouncements,
    AnnouncerComponent: () => (
      <div
        ref={announcerRef}
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
      />
    )
  }
}

/**
 * 键盘快捷键Hook
 */
export const useKeyboardShortcuts = (shortcuts: Record<string, () => void>) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const key = []
      
      if (e.ctrlKey) key.push('ctrl')
      if (e.altKey) key.push('alt')
      if (e.shiftKey) key.push('shift')
      if (e.metaKey) key.push('meta')
      
      key.push(e.key.toLowerCase())
      
      const shortcut = key.join('+')
      
      if (shortcuts[shortcut]) {
        e.preventDefault()
        shortcuts[shortcut]()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [shortcuts])
}

/**
 * 可聚焦组件包装器
 */
export const FocusableElement = forwardRef<
  HTMLElement,
  React.ComponentProps<'button'> & {
    as?: keyof JSX.IntrinsicElements
    onFocus?: () => void
    onBlur?: () => void
  }
>(({ as: Component = 'button', onFocus, onBlur, className, ...props }, ref) => {
  const [isFocused, setIsFocused] = useState(false)

  const handleFocus = () => {
    setIsFocused(true)
    onFocus?.()
  }

  const handleBlur = () => {
    setIsFocused(false)
    onBlur?.()
  }

  const focusableProps = {
    ...props,
    ref,
    onFocus: handleFocus,
    onBlur: handleBlur,
    className: cn(
      'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
      isFocused && 'ring-2 ring-primary ring-offset-2',
      className
    )
  }

  return <Component {...focusableProps} />
})

FocusableElement.displayName = 'FocusableElement'

/**
 * 键盘导航指南组件
 */
export const KeyboardNavigationGuide: React.FC<{
  shortcuts: Record<string, string>
  className?: string
}> = ({ shortcuts, className }) => {
  const [isVisible, setIsVisible] = useState(false)

  const shortcutGroups = {
    '导航': {
      'Tab': '移动到下一个可聚焦元素',
      'Shift + Tab': '移动到上一个可聚焦元素',
      'Enter': '激活按钮或链接',
      'Space': '激活按钮或切换复选框',
      'Escape': '关闭模态框或取消操作'
    },
    '页面导航': {
      'Home': '移动到页面开头',
      'End': '移动到页面末尾',
      'Page Up': '向上滚动一页',
      'Page Down': '向下滚动一页',
      'Arrow Keys': '在列表或菜单中导航'
    },
    '应用快捷键': shortcuts
  }

  return (
    <div className={cn("fixed bottom-4 left-4 z-40", className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsVisible(!isVisible)}
        className="mb-2"
      >
        <Keyboard className="w-4 h-4 mr-2" />
        键盘快捷键
      </Button>

      {isVisible && (
        <Card className="w-80 p-4 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">键盘导航指南</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsVisible(false)}
            >
              ×
            </Button>
          </div>

          <div className="space-y-4 max-h-96 overflow-y-auto">
            {Object.entries(shortcutGroups).map(([group, groupShortcuts]) => (
              <div key={group}>
                <h4 className="font-medium text-sm text-muted-foreground mb-2">
                  {group}
                </h4>
                <div className="space-y-1">
                  {Object.entries(groupShortcuts).map(([shortcut, description]) => (
                    <div key={shortcut} className="flex justify-between text-sm">
                      <kbd className="px-2 py-1 bg-muted rounded text-xs">
                        {shortcut}
                      </kbd>
                      <span className="text-muted-foreground ml-2">
                        {description}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

/**
 * 屏幕阅读器控制面板
 */
export const ScreenReaderControls: React.FC<{
  config: ScreenReaderConfig
  onConfigChange: (updates: Partial<ScreenReaderConfig>) => void
  onAnnounce: (message: string) => void
  isReading: boolean
  onToggleReading: () => void
  announcementQueue: string[]
  onPlayNext: () => void
  onClearQueue: () => void
  className?: string
}> = ({ 
  config, 
  onConfigChange, 
  onAnnounce, 
  isReading, 
  onToggleReading, 
  announcementQueue, 
  onPlayNext, 
  onClearQueue, 
  className 
}) => {
  const [customMessage, setCustomMessage] = useState('')

  const handleAnnounce = () => {
    if (customMessage.trim()) {
      onAnnounce(customMessage)
      setCustomMessage('')
    }
  }

  return (
    <Card className={cn("p-6 space-y-4", className)}>
      {/* 头部 */}
      <div className="flex items-center gap-3">
        <Volume2 className="w-6 h-6 text-primary" />
        <h2 className="text-xl font-semibold">屏幕阅读器控制</h2>
      </div>

      {/* 状态指示器 */}
      <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
        <div className={cn(
          "w-3 h-3 rounded-full",
          config.enabled ? "bg-green-500" : "bg-gray-400"
        )} />
        <span className="font-medium">
          {config.enabled ? '屏幕阅读器已启用' : '屏幕阅读器已禁用'}
        </span>
        {isReading && (
          <div className="flex items-center gap-1 text-blue-600">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
            <span className="text-sm">正在朗读</span>
          </div>
        )}
      </div>

      {/* 基本设置 */}
      <div className="space-y-3">
        <h3 className="font-semibold">基本设置</h3>
        
        <label className="flex items-center justify-between">
          <span>启用屏幕阅读器</span>
          <input
            type="checkbox"
            checked={config.enabled}
            onChange={(e) => onConfigChange({ enabled: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>自动通知</span>
          <input
            type="checkbox"
            checked={config.autoAnnounce}
            onChange={(e) => onConfigChange({ autoAnnounce: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>详细模式</span>
          <input
            type="checkbox"
            checked={config.verboseMode}
            onChange={(e) => onConfigChange({ verboseMode: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>暂停动画</span>
          <input
            type="checkbox"
            checked={config.pauseAnimations}
            onChange={(e) => onConfigChange({ pauseAnimations: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>通知错误</span>
          <input
            type="checkbox"
            checked={config.announceErrors}
            onChange={(e) => onConfigChange({ announceErrors: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>通知导航</span>
          <input
            type="checkbox"
            checked={config.announceNavigation}
            onChange={(e) => onConfigChange({ announceNavigation: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
      </div>

      {/* 通知队列 */}
      <div className="space-y-3">
        <h3 className="font-semibold">通知队列</h3>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            队列中的消息: {announcementQueue.length}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onPlayNext}
              disabled={announcementQueue.length === 0}
            >
              <Play className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onClearQueue}
              disabled={announcementQueue.length === 0}
            >
              清空
            </Button>
          </div>
        </div>
        
        {announcementQueue.length > 0 && (
          <div className="max-h-32 overflow-y-auto space-y-1 p-2 bg-muted rounded">
            {announcementQueue.map((message, index) => (
              <div key={index} className="text-sm p-1 bg-background rounded">
                {message}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 自定义通知 */}
      <div className="space-y-3">
        <h3 className="font-semibold">测试通知</h3>
        
        <div className="flex gap-2">
          <input
            type="text"
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
            placeholder="输入测试消息..."
            className="flex-1 border rounded px-3 py-2"
            onKeyPress={(e) => e.key === 'Enter' && handleAnnounce()}
          />
          <Button onClick={handleAnnounce} disabled={!customMessage.trim()}>
            朗读
          </Button>
        </div>
      </div>

      {/* 控制按钮 */}
      <div className="flex gap-2 pt-4 border-t">
        <Button
          variant="outline"
          onClick={onToggleReading}
          className="flex-1"
        >
          {isReading ? (
            <>
              <Pause className="w-4 h-4 mr-2" />
              暂停朗读
            </>
          ) : (
            <>
              <Play className="w-4 h-4 mr-2" />
              开始朗读
            </>
          )}
        </Button>
      </div>
    </Card>
  )
}

/**
 * 键盘导航和屏幕阅读器提供者
 */
export const AccessibilityNavigationProvider: React.FC<{
  children: React.ReactNode
  keyboardConfig?: Partial<KeyboardNavigationConfig>
  screenReaderConfig?: Partial<ScreenReaderConfig>
}> = ({ 
  children, 
  keyboardConfig = {},
  screenReaderConfig = {}
}) => {
  const [keyboardNavConfig, setKeyboardNavConfig] = useState<KeyboardNavigationConfig>({
    enabled: true,
    trapFocus: false,
    wrapNavigation: true,
    visualFocusIndicator: true,
    announceFocus: true,
    skipToContent: true,
    focusShortcuts: {
      'alt+h': '跳转到主页',
      'alt+n': '跳转到导航',
      'alt+s': '跳转到搜索',
      'alt+c': '跳转到内容',
      'alt+f': '跳转到页脚'
    }
  })

  const [screenReaderConfigState, setScreenReaderConfigState] = useState<ScreenReaderConfig>({
    enabled: false,
    autoAnnounce: true,
    verboseMode: false,
    pauseAnimations: false,
    announceErrors: true,
    announceNavigation: true,
    customLabels: {}
  })

  const focusManager = useFocusManagement(keyboardNavConfig)
  const screenReader = useScreenReader(screenReaderConfigState)

  // 键盘快捷键
  const shortcuts = {
    'alt+1': () => focusManager.focusFirst(),
    'alt+2': () => focusManager.focusLast(),
    'alt+/': () => setKeyboardNavConfig(prev => ({ ...prev, enabled: !prev.enabled })),
    'alt+r': () => screenReader.toggleReading()
  }

  useKeyboardShortcuts(shortcuts)

  // 监听焦点变化
  useEffect(() => {
    const handleFocusIn = (e: FocusEvent) => {
      const target = e.target as HTMLElement
      focusManager.setFocusedElement(target)
      
      if (screenReaderConfigState.announceFocus) {
        screenReader.announceFocus(target)
      }
    }

    document.addEventListener('focusin', handleFocusIn)
    
    return () => {
      document.removeEventListener('focusin', handleFocusIn)
    }
  }, [focusManager, screenReader, screenReaderConfigState.announceFocus])

  return (
    <>
      {/* 屏幕阅读器通知器 */}
      <screenReader.AnnouncerComponent />
      
      {/* 键盘导航指南 */}
      {keyboardNavConfig.enabled && (
        <KeyboardNavigationGuide shortcuts={keyboardNavConfig.focusShortcuts} />
      )}
      
      {/* 主要内容 */}
      <div className={cn(
        "min-h-screen",
        keyboardNavConfig.visualFocusIndicator && "focus-visible",
        screenReaderConfigState.pauseAnimations && "reduce-motion"
      )}>
        {children}
      </div>
    </>
  )
}
