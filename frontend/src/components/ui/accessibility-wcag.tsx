import React, { useEffect, useState, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { 
  Eye, 
  EyeOff, 
  Type, 
  Minus, 
  Plus, 
  Sun, 
  Moon, 
  Contrast,
  Monitor,
  Accessibility,
  Check,
  AlertTriangle,
  Info
} from 'lucide-react'

/**
 * 可访问性配置接口
 */
export interface AccessibilityConfig {
  // 视觉辅助
  highContrast: boolean
  largeText: boolean
  reducedMotion: boolean
  focusVisible: boolean
  
  // 颜色和主题
  colorBlindMode: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia'
  darkMode: boolean
  
  // 字体和阅读
  fontSize: number // 100-200%
  lineHeight: number // 1.0-2.0
  letterSpacing: number // 0-2px
  
  // 导航和交互
  keyboardNavigation: boolean
  screenReaderOptimized: boolean
  ariaLabels: boolean
  
  // 其他辅助
  autoAnnounce: boolean
  skipLinks: boolean
  errorAnnouncements: boolean
}

/**
 * 默认可访问性配置
 */
const DEFAULT_ACCESSIBILITY_CONFIG: AccessibilityConfig = {
  highContrast: false,
  largeText: false,
  reducedMotion: false,
  focusVisible: true,
  colorBlindMode: 'none',
  darkMode: false,
  fontSize: 100,
  lineHeight: 1.5,
  letterSpacing: 0,
  keyboardNavigation: true,
  screenReaderOptimized: false,
  ariaLabels: true,
  autoAnnounce: true,
  skipLinks: true,
  errorAnnouncements: true
}

/**
 * WCAG 2.1 AA 可访问性Hook
 */
export const useAccessibility = () => {
  const [config, setConfig] = useState<AccessibilityConfig>(DEFAULT_ACCESSIBILITY_CONFIG)
  const [isInitialized, setIsInitialized] = useState(false)

  // 从存储中加载配置
  useEffect(() => {
    try {
      const saved = localStorage.getItem('accessibility_config')
      if (saved) {
        const parsedConfig = JSON.parse(saved)
        setConfig({ ...DEFAULT_ACCESSIBILITY_CONFIG, ...parsedConfig })
      }
      
      // 检测系统偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      
      setConfig(prev => ({
        ...prev,
        darkMode: prev.darkMode || prefersDark,
        reducedMotion: prev.reducedMotion || prefersReducedMotion
      }))
      
      setIsInitialized(true)
    } catch (error) {
      console.warn('Failed to load accessibility config:', error)
      setIsInitialized(true)
    }
  }, [])

  // 保存配置到存储
  const saveConfig = useCallback((newConfig: AccessibilityConfig) => {
    try {
      localStorage.setItem('accessibility_config', JSON.stringify(newConfig))
    } catch (error) {
      console.warn('Failed to save accessibility config:', error)
    }
  }, [])

  // 更新配置
  const updateConfig = useCallback((updates: Partial<AccessibilityConfig>) => {
    const newConfig = { ...config, ...updates }
    setConfig(newConfig)
    saveConfig(newConfig)
  }, [config, saveConfig])

  // 应用可访问性样式到文档
  useEffect(() => {
    if (!isInitialized) return

    const root = document.documentElement
    
    // 高对比度
    if (config.highContrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }
    
    // 大字体
    if (config.largeText) {
      root.classList.add('large-text')
    } else {
      root.classList.remove('large-text')
    }
    
    // 减少动画
    if (config.reducedMotion) {
      root.classList.add('reduce-motion')
    } else {
      root.classList.remove('reduce-motion')
    }
    
    // 焦点可见
    if (config.focusVisible) {
      root.classList.add('focus-visible')
    } else {
      root.classList.remove('focus-visible')
    }
    
    // 色盲模式
    root.classList.remove('protanopia', 'deuteranopia', 'tritanopia')
    if (config.colorBlindMode !== 'none') {
      root.classList.add(config.colorBlindMode)
    }
    
    // 深色模式
    if (config.darkMode) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    
    // 字体大小
    root.style.fontSize = `${config.fontSize}%`
    
    // 行高
    root.style.lineHeight = config.lineHeight.toString()
    
    // 字间距
    root.style.letterSpacing = `${config.letterSpacing}px`
    
    // 屏幕阅读器优化
    if (config.screenReaderOptimized) {
      root.setAttribute('aria-live', 'polite')
    } else {
      root.removeAttribute('aria-live')
    }
    
  }, [config, isInitialized])

  // 重置配置
  const resetConfig = useCallback(() => {
    setConfig(DEFAULT_ACCESSIBILITY_CONFIG)
    saveConfig(DEFAULT_ACCESSIBILITY_CONFIG)
  }, [saveConfig])

  // 检查WCAG合规性
  const checkCompliance = useCallback(() => {
    const issues: string[] = []
    
    // 检查颜色对比度
    if (!config.highContrast) {
      const testElements = document.querySelectorAll('button, a, .text-primary')
      testElements.forEach(element => {
        const styles = window.getComputedStyle(element)
        const color = styles.color
        const backgroundColor = styles.backgroundColor
        
        // 这里应该使用实际的对比度计算库
        // 简化示例
        if (color === 'rgb(128, 128, 128)' && backgroundColor === 'rgb(248, 248, 248)') {
          issues.push('低对比度文本')
        }
      })
    }
    
    // 检查焦点管理
    if (!config.focusVisible) {
      issues.push('焦点指示器不可见')
    }
    
    // 检查ARIA标签
    if (!config.ariaLabels) {
      const interactiveElements = document.querySelectorAll('button, a, input, select, textarea')
      interactiveElements.forEach(element => {
        if (!element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
          const textContent = element.textContent?.trim()
          if (!textContent) {
            issues.push('交互元素缺少可访问性标签')
          }
        }
      })
    }
    
    return {
      compliant: issues.length === 0,
      issues,
      score: Math.max(0, 100 - (issues.length * 10))
    }
  }, [config])

  return {
    config,
    updateConfig,
    resetConfig,
    isInitialized,
    checkCompliance
  }
}

/**
 * 屏幕阅读器通知Hook
 */
export const useScreenReaderAnnouncer = () => {
  const announcerRef = useRef<HTMLDivElement>(null)

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
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
  }, [])

  const announceError = useCallback((message: string) => {
    announce(`错误: ${message}`, 'assertive')
  }, [announce])

  const announceSuccess = useCallback((message: string) => {
    announce(`成功: ${message}`, 'polite')
  }, [announce])

  const announceNavigation = useCallback((message: string) => {
    announce(`导航到: ${message}`, 'polite')
  }, [announce])

  return {
    announce,
    announceError,
    announceSuccess,
    announceNavigation,
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
 * 跳转链接组件
 */
export const SkipLinks: React.FC<{
  links: Array<{
    id: string
    label: string
  }>
  className?: string
}> = ({ links, className }) => {
  return (
    <div className={cn(
      "sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 bg-primary text-primary-foreground p-2 rounded",
      className
    )}>
      {links.map(link => (
        <a
          key={link.id}
          href={`#${link.id}`}
          className="block px-3 py-2 hover:bg-primary/80 rounded"
        >
          {link.label}
        </a>
      ))}
    </div>
  )
}

/**
 * 可访问性面板组件
 */
export const AccessibilityPanel: React.FC<{
  config: AccessibilityConfig
  onConfigChange: (updates: Partial<AccessibilityConfig>) => void
  onReset: () => void
  className?: string
}> = ({ config, onConfigChange, onReset, className }) => {
  const [compliance, setCompliance] = useState<{ compliant: boolean; issues: string[]; score: number } | null>(null)

  const checkCompliance = () => {
    // 模拟合规性检查
    const issues: string[] = []
    
    if (!config.highContrast) issues.push('建议启用高对比度模式')
    if (!config.focusVisible) issues.push('焦点指示器已禁用')
    if (!config.ariaLabels) issues.push('ARIA标签已禁用')
    if (config.fontSize < 100) issues.push('字体大小小于推荐值')
    
    const score = Math.max(0, 100 - (issues.length * 15))
    
    setCompliance({
      compliant: issues.length === 0,
      issues,
      score
    })
  }

  return (
    <Card className={cn("p-6 space-y-6", className)}>
      {/* 头部 */}
      <div className="flex items-center gap-3">
        <Accessibility className="w-6 h-6 text-primary" />
        <h2 className="text-xl font-semibold">可访问性设置</h2>
      </div>

      {/* 合规性检查 */}
      <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
        <div className="flex items-center gap-2">
          {compliance?.compliant ? (
            <Check className="w-5 h-5 text-green-600" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
          )}
          <span className="font-medium">
            WCAG 2.1 AA 合规性: {compliance?.score || 0}%
          </span>
        </div>
        <Button variant="outline" size="sm" onClick={checkCompliance}>
          检查合规性
        </Button>
      </div>

      {compliance && !compliance.compliant && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
            <div>
              <div className="font-medium text-yellow-800">建议改进:</div>
              <ul className="text-sm text-yellow-700 mt-1 space-y-1">
                {compliance.issues.map((issue, index) => (
                  <li key={index}>• {issue}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 视觉辅助 */}
      <div className="space-y-3">
        <h3 className="font-semibold flex items-center gap-2">
          <Eye className="w-4 h-4" />
          视觉辅助
        </h3>
        
        <div className="grid gap-3">
          <label className="flex items-center justify-between">
            <span>高对比度模式</span>
            <input
              type="checkbox"
              checked={config.highContrast}
              onChange={(e) => onConfigChange({ highContrast: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>大字体模式</span>
            <input
              type="checkbox"
              checked={config.largeText}
              onChange={(e) => onConfigChange({ largeText: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>减少动画</span>
            <input
              type="checkbox"
              checked={config.reducedMotion}
              onChange={(e) => onConfigChange({ reducedMotion: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>焦点指示器</span>
            <input
              type="checkbox"
              checked={config.focusVisible}
              onChange={(e) => onConfigChange({ focusVisible: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
        </div>
      </div>

      {/* 颜色和主题 */}
      <div className="space-y-3">
        <h3 className="font-semibold flex items-center gap-2">
          <Contrast className="w-4 h-4" />
          颜色和主题
        </h3>
        
        <div className="grid gap-3">
          <label className="flex items-center justify-between">
            <span>深色模式</span>
            <input
              type="checkbox"
              checked={config.darkMode}
              onChange={(e) => onConfigChange({ darkMode: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <div>
            <label className="block text-sm font-medium mb-2">色盲模式</label>
            <select
              value={config.colorBlindMode}
              onChange={(e) => onConfigChange({ colorBlindMode: e.target.value as any })}
              className="w-full border rounded px-3 py-2"
            >
              <option value="none">无</option>
              <option value="protanopia">红色盲</option>
              <option value="deuteranopia">绿色盲</option>
              <option value="tritanopia">蓝色盲</option>
            </select>
          </div>
        </div>
      </div>

      {/* 字体和阅读 */}
      <div className="space-y-3">
        <h3 className="font-semibold flex items-center gap-2">
          <Type className="w-4 h-4" />
          字体和阅读
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              字体大小: {config.fontSize}%
            </label>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onConfigChange({ fontSize: Math.max(100, config.fontSize - 10) })}
              >
                <Minus className="w-4 h-4" />
              </Button>
              <div className="flex-1 bg-muted rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{ width: `${((config.fontSize - 100) / 100) * 100}%` }}
                />
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onConfigChange({ fontSize: Math.min(200, config.fontSize + 10) })}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              行高: {config.lineHeight}
            </label>
            <input
              type="range"
              min="1.0"
              max="2.0"
              step="0.1"
              value={config.lineHeight}
              onChange={(e) => onConfigChange({ lineHeight: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* 导航和交互 */}
      <div className="space-y-3">
        <h3 className="font-semibold flex items-center gap-2">
          <Monitor className="w-4 h-4" />
          导航和交互
        </h3>
        
        <div className="grid gap-3">
          <label className="flex items-center justify-between">
            <span>键盘导航</span>
            <input
              type="checkbox"
              checked={config.keyboardNavigation}
              onChange={(e) => onConfigChange({ keyboardNavigation: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>屏幕阅读器优化</span>
            <input
              type="checkbox"
              checked={config.screenReaderOptimized}
              onChange={(e) => onConfigChange({ screenReaderOptimized: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>ARIA 标签</span>
            <input
              type="checkbox"
              checked={config.ariaLabels}
              onChange={(e) => onConfigChange({ ariaLabels: e.target.checked })}
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
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2 pt-4 border-t">
        <Button variant="outline" onClick={onReset}>
          重置为默认
        </Button>
        <Button className="flex-1">
          保存设置
        </Button>
      </div>
    </Card>
  )
}

/**
 * 可访问性工具栏组件
 */
export const AccessibilityToolbar: React.FC<{
  config: AccessibilityConfig
  onConfigChange: (updates: Partial<AccessibilityConfig>) => void
  onTogglePanel: () => void
  className?: string
}> = ({ config, onConfigChange, onTogglePanel, className }) => {
  return (
    <div className={cn(
      "fixed top-4 right-4 z-40 flex items-center gap-2 bg-background border rounded-lg shadow-lg p-2",
      className
    )}>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onConfigChange({ highContrast: !config.highContrast })}
        className={cn(config.highContrast && "bg-primary text-primary-foreground")}
        title="切换高对比度"
      >
        <Contrast className="w-4 h-4" />
      </Button>
      
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onConfigChange({ largeText: !config.largeText })}
        className={cn(config.largeText && "bg-primary text-primary-foreground")}
        title="切换大字体"
      >
        <Type className="w-4 h-4" />
      </Button>
      
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onConfigChange({ darkMode: !config.darkMode })}
        className={cn(config.darkMode && "bg-primary text-primary-foreground")}
        title="切换深色模式"
      >
        {config.darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      </Button>
      
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onConfigChange({ reducedMotion: !config.reducedMotion })}
        className={cn(config.reducedMotion && "bg-primary text-primary-foreground")}
        title="切换动画"
      >
        <Eye className="w-4 h-4" />
      </Button>
      
      <div className="w-px h-6 bg-border" />
      
      <Button
        variant="ghost"
        size="sm"
        onClick={onTogglePanel}
        title="打开可访问性面板"
      >
        <Accessibility className="w-4 h-4" />
      </Button>
    </div>
  )
}

/**
 * 可访问性提供者组件
 */
export const AccessibilityProvider: React.FC<{
  children: React.ReactNode
}> = ({ children }) => {
  const accessibility = useAccessibility()
  const [showPanel, setShowPanel] = useState(false)
  const announcer = useScreenReaderAnnouncer()

  // 自动设置跳转链接
  useEffect(() => {
    if (accessibility.config.skipLinks) {
      // 确保主要内容区域有ID
      const mainContent = document.querySelector('main, [role="main"]')
      if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content'
      }
      
      // 确保导航区域有ID
      const nav = document.querySelector('nav, [role="navigation"]')
      if (nav && !nav.id) {
        nav.id = 'main-navigation'
      }
    }
  }, [accessibility.config.skipLinks])

  return (
    <>
      {/* 跳转链接 */}
      {accessibility.config.skipLinks && (
        <SkipLinks
          links={[
            { id: 'main-navigation', label: '跳转到导航' },
            { id: 'main-content', label: '跳转到主要内容' }
          ]}
        />
      )}
      
      {/* 屏幕阅读器通知器 */}
      <announcer.AnnouncerComponent />
      
      {/* 可访问性工具栏 */}
      <AccessibilityToolbar
        config={accessibility.config}
        onConfigChange={accessibility.updateConfig}
        onTogglePanel={() => setShowPanel(!showPanel)}
      />
      
      {/* 可访问性面板 */}
      {showPanel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <AccessibilityPanel
            config={accessibility.config}
            onConfigChange={accessibility.updateConfig}
            onReset={accessibility.resetConfig}
          />
          <Button
            variant="ghost"
            size="lg"
            onClick={() => setShowPanel(false)}
            className="fixed top-4 right-4"
          >
            <EyeOff className="w-4 h-4" />
          </Button>
        </div>
      )}
      
      {/* 主要内容 */}
      <div 
        className={cn(
          "min-h-screen transition-all duration-300",
          accessibility.config.reducedMotion && "transition-none"
        )}
      >
        {children}
      </div>
    </>
  )
}
