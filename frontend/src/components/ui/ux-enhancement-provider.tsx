import React, { useState, useEffect } from 'react'
import { AccessibilityProvider } from './accessibility-wcag'
import { AccessibilityNavigationProvider } from './accessibility-navigation'
import { MicroInteractionProvider } from './micro-interactions'
import { UXTestProvider } from './ux-testing'
import { TouchOptimized } from './mobile-touch'
import { useDeviceDetection } from './mobile-touch'
import { ErrorBoundary } from './error-boundary'
import { ErrorHandlingProvider } from './error-handling'
import { LoadingProvider } from './loading'
import { OfflineSupport } from './offline-support'

/**
 * UX增强配置接口
 */
export interface UXEnhancementConfig {
  // 性能优化
  enableSmartPreload: boolean
  enableOptimisticUpdates: boolean
  enableSkeletonScreens: boolean
  enableOfflineSupport: boolean
  
  // 错误处理
  enableErrorBoundaries: boolean
  enableErrorRecovery: boolean
  enableErrorFeedback: boolean
  
  // 用户引导
  enableOnboarding: boolean
  enableInteractiveHelp: boolean
  enableFeatureDiscovery: boolean
  enableHelpDocumentation: boolean
  enableUserFeedback: boolean
  
  // 可访问性
  enableWCAGCompliance: boolean
  enableScreenReaderSupport: boolean
  enableKeyboardNavigation: boolean
  enableTouchOptimization: boolean
  
  // 微交互
  enableMicroInteractions: boolean
  enableAnimations: boolean
  enableGestureSupport: boolean
  
  // 测试和监控
  enableUXTesting: boolean
  enablePerformanceMonitoring: boolean
  showUXControls: boolean
  
  // 渐进式部署
  phase: 'development' | 'testing' | 'production'
  features: {
    phase1: boolean // 性能和加载优化
    phase2: boolean // 错误处理和用户支持
    phase3: boolean // 用户引导和帮助系统
    phase4: boolean // 可访问性和交互优化
  }
}

/**
 * 默认配置
 */
const DEFAULT_CONFIG: UXEnhancementConfig = {
  enableSmartPreload: true,
  enableOptimisticUpdates: true,
  enableSkeletonScreens: true,
  enableOfflineSupport: true,
  
  enableErrorBoundaries: true,
  enableErrorRecovery: true,
  enableErrorFeedback: true,
  
  enableOnboarding: true,
  enableInteractiveHelp: true,
  enableFeatureDiscovery: true,
  enableHelpDocumentation: true,
  enableUserFeedback: true,
  
  enableWCAGCompliance: true,
  enableScreenReaderSupport: true,
  enableKeyboardNavigation: true,
  enableTouchOptimization: true,
  
  enableMicroInteractions: true,
  enableAnimations: true,
  enableGestureSupport: true,
  
  enableUXTesting: true,
  enablePerformanceMonitoring: true,
  showUXControls: false,
  
  phase: 'development',
  features: {
    phase1: true,
    phase2: true,
    phase3: true,
    phase4: true
  }
}

/**
 * UX增强提供者组件
 */
export const UXEnhancementProvider: React.FC<{
  children: React.ReactNode
  config?: Partial<UXEnhancementConfig>
}> = ({ children, config = {} }) => {
  const [uxConfig, setUXConfig] = useState<UXEnhancementConfig>({
    ...DEFAULT_CONFIG,
    ...config
  })
  
  const device = useDeviceDetection()
  
  // 根据设备类型调整配置
  useEffect(() => {
    setUXConfig(prev => ({
      ...prev,
      enableTouchOptimization: device.isTouchDevice,
      enableGestureSupport: device.isTouchDevice,
      enableAnimations: !device.isReducedMotion,
      enableMicroInteractions: !device.isReducedMotion
    }))
  }, [device])

  // 根据部署阶段调整配置
  useEffect(() => {
    const envConfig = {
      development: {
        showUXControls: true,
        enableUXTesting: true,
        enablePerformanceMonitoring: true
      },
      testing: {
        showUXControls: true,
        enableUXTesting: true,
        enablePerformanceMonitoring: true
      },
      production: {
        showUXControls: false,
        enableUXTesting: false,
        enablePerformanceMonitoring: false
      }
    }
    
    setUXConfig(prev => ({
      ...prev,
      ...envConfig[uxConfig.phase]
    }))
  }, [uxConfig.phase])

  // Phase 1: 性能和加载优化
  const Phase1Providers = () => (
    <>
      {uxConfig.enableOfflineSupport && <OfflineSupport />}
      {uxConfig.enableSkeletonScreens && (
        <LoadingProvider 
          config={{
            enableSkeleton: uxConfig.enableSkeletonScreens,
            enableSmartLoading: uxConfig.enableSmartPreload,
            enableProgressiveLoading: uxConfig.enableSmartPreload
          }}
        />
      )}
    </>
  )

  // Phase 2: 错误处理和用户支持
  const Phase2Providers = () => (
    <>
      {uxConfig.enableErrorBoundaries && (
        <ErrorBoundary
          config={{
            enableErrorRecovery: uxConfig.enableErrorRecovery,
            enableErrorReporting: uxConfig.enableErrorFeedback,
            showRetryButton: uxConfig.enableErrorRecovery
          }}
        >
          {uxConfig.enableErrorRecovery && (
            <ErrorHandlingProvider
              config={{
                enableAutoRetry: uxConfig.enableErrorRecovery,
                enableErrorFeedback: uxConfig.enableErrorFeedback,
                maxRetries: 3
              }}
            />
          )}
        </ErrorBoundary>
      )}
    </>
  )

  // Phase 3: 用户引导和帮助系统
  const Phase3Providers = () => (
    <>
      {/* 这些提供者将在具体页面中按需使用 */}
    </>
  )

  // Phase 4: 可访问性和交互优化
  const Phase4Providers = () => (
    <>
      {uxConfig.enableWCAGCompliance && (
        <AccessibilityProvider>
          {uxConfig.enableScreenReaderSupport && (
            <AccessibilityNavigationProvider
              keyboardConfig={{
                enabled: uxConfig.enableKeyboardNavigation,
                trapFocus: true,
                wrapNavigation: true,
                visualFocusIndicator: true,
                announceFocus: true,
                skipToContent: true
              }}
              screenReaderConfig={{
                enabled: uxConfig.enableScreenReaderSupport,
                autoAnnounce: true,
                verboseMode: false,
                pauseAnimations: device.isReducedMotion,
                announceErrors: true,
                announceNavigation: true
              }}
            />
          )}
        </AccessibilityProvider>
      )}
      
      {uxConfig.enableMicroInteractions && (
        <MicroInteractionProvider
          config={{
            enabled: uxConfig.enableAnimations && !device.isReducedMotion,
            reducedMotion: device.isReducedMotion,
            respectPreferences: true,
            defaultDuration: 300,
            defaultEasing: 'ease-out',
            staggerDelay: 100,
            hoverEffects: uxConfig.enableMicroInteractions,
            clickEffects: uxConfig.enableMicroInteractions,
            focusEffects: uxConfig.enableKeyboardNavigation,
            loadingEffects: uxConfig.enableSkeletonScreens,
            enableGPU: true,
            throttleAnimations: false,
            maxConcurrentAnimations: 10,
            pauseOnHover: false,
            showControls: uxConfig.showUXControls,
            announceAnimations: false
          }}
        />
      )}
      
      {uxConfig.enableTouchOptimization && device.isTouchDevice && (
        <TouchOptimized
          config={{
            enabled: true,
            preventDefault: false,
            stopPropagation: false,
            tapThreshold: 300,
            doubleTapThreshold: 300,
            longPressThreshold: 500,
            swipeThreshold: 50,
            pinchThreshold: 20,
            rotateThreshold: 15,
            hapticFeedback: device.isMobile,
            visualFeedback: true,
            soundFeedback: false,
            throttleMs: 16,
            debounceMs: 100,
            reducedMotion: device.isReducedMotion,
            largeTouchTargets: device.isMobile,
            highContrast: false
          }}
        />
      )}
      
      {uxConfig.enableUXTesting && (
        <UXTestProvider
          config={{
            testTypes: ['performance', 'accessibility', 'usability'],
            includePerformance: uxConfig.enablePerformanceMonitoring,
            includeAccessibility: uxConfig.enableWCAGCompliance,
            includeUsability: true,
            performanceThresholds: {
              firstContentfulPaint: 1800,
              largestContentfulPaint: 2500,
              firstInputDelay: 100,
              cumulativeLayoutShift: 0.1,
              timeToInteractive: 3800
            },
            accessibilityLevel: 'AA',
            testColorContrast: uxConfig.enableWCAGCompliance,
            testKeyboardNavigation: uxConfig.enableKeyboardNavigation,
            testScreenReader: uxConfig.enableScreenReaderSupport,
            testTouchTargets: uxConfig.enableTouchOptimization,
            testReadability: true,
            testNavigation: true,
            browsers: ['chrome', 'firefox', 'safari', 'edge'],
            viewports: [
              { width: 375, height: 667, name: 'Mobile' },
              { width: 768, height: 1024, name: 'Tablet' },
              { width: 1920, height: 1080, name: 'Desktop' }
            ],
            enableRealUserMonitoring: uxConfig.enablePerformanceMonitoring,
            enableA11yTesting: uxConfig.enableWCAGCompliance,
            enablePerformanceMonitoring: uxConfig.enablePerformanceMonitoring
          }}
          showPanel={uxConfig.showUXControls}
        />
      )}
    </>
  )

  // 根据功能阶段渲染提供者
  const renderProviders = () => {
    let content = children

    // Phase 1: 性能和加载优化
    if (uxConfig.features.phase1) {
      content = <Phase1Providers>{content}</Phase1Providers>
    }

    // Phase 2: 错误处理和用户支持
    if (uxConfig.features.phase2) {
      content = <Phase2Providers>{content}</Phase2Providers>
    }

    // Phase 3: 用户引导和帮助系统
    if (uxConfig.features.phase3) {
      content = <Phase3Providers>{content}</Phase3Providers>
    }

    // Phase 4: 可访问性和交互优化
    if (uxConfig.features.phase4) {
      content = <Phase4Providers>{content}</Phase4Providers>
    }

    return content
  }

  return <>{renderProviders()}</>
}

/**
 * UX增强Hook
 */
export const useUXEnhancement = () => {
  const [config, setConfig] = useState<UXEnhancementConfig>(DEFAULT_CONFIG)
  const [isInitialized, setIsInitialized] = useState(false)

  // 从localStorage加载配置
  useEffect(() => {
    try {
      const saved = localStorage.getItem('ux-enhancement-config')
      if (saved) {
        const parsedConfig = JSON.parse(saved)
        setConfig({ ...DEFAULT_CONFIG, ...parsedConfig })
      }
      setIsInitialized(true)
    } catch (error) {
      console.warn('Failed to load UX enhancement config:', error)
      setIsInitialized(true)
    }
  }, [])

  // 更新配置
  const updateConfig = (updates: Partial<UXEnhancementConfig>) => {
    const newConfig = { ...config, ...updates }
    setConfig(newConfig)
    
    try {
      localStorage.setItem('ux-enhancement-config', JSON.stringify(newConfig))
    } catch (error) {
      console.warn('Failed to save UX enhancement config:', error)
    }
  }

  // 启用/禁用功能阶段
  const togglePhase = (phase: keyof UXEnhancementConfig['features']) => {
    updateConfig({
      features: {
        ...config.features,
        [phase]: !config.features[phase]
      }
    })
  }

  // 重置为默认配置
  const resetConfig = () => {
    setConfig(DEFAULT_CONFIG)
    try {
      localStorage.setItem('ux-enhancement-config', JSON.stringify(DEFAULT_CONFIG))
    } catch (error) {
      console.warn('Failed to reset UX enhancement config:', error)
    }
  }

  return {
    config,
    updateConfig,
    togglePhase,
    resetConfig,
    isInitialized
  }
}

/**
 * UX增强控制面板组件
 */
export const UXEnhancementControlPanel: React.FC<{
  config: UXEnhancementConfig
  onConfigChange: (updates: Partial<UXEnhancementConfig>) => void
  className?: string
}> = ({ config, onConfigChange, className }) => {
  const [activeTab, setActiveTab] = useState<'phases' | 'features' | 'advanced'>('phases')

  return (
    <div className={cn("w-80 max-h-[80vh] overflow-y-auto bg-background border rounded-lg shadow-lg", className)}>
      <div className="p-4 border-b">
        <h3 className="font-semibold text-lg">UX增强控制</h3>
      </div>
      
      <div className="border-b">
        <div className="flex">
          <button
            className={cn(
              "flex-1 px-4 py-2 text-sm font-medium",
              activeTab === 'phases' && "bg-primary text-primary-foreground"
            )}
            onClick={() => setActiveTab('phases')}
          >
            阶段
          </button>
          <button
            className={cn(
              "flex-1 px-4 py-2 text-sm font-medium",
              activeTab === 'features' && "bg-primary text-primary-foreground"
            )}
            onClick={() => setActiveTab('features')}
          >
            功能
          </button>
          <button
            className={cn(
              "flex-1 px-4 py-2 text-sm font-medium",
              activeTab === 'advanced' && "bg-primary text-primary-foreground"
            )}
            onClick={() => setActiveTab('advanced')}
          >
            高级
          </button>
        </div>
      </div>
      
      <div className="p-4 space-y-4">
        {activeTab === 'phases' && (
          <div className="space-y-3">
            <h4 className="font-medium">功能阶段</h4>
            {Object.entries(config.features).map(([phase, enabled]) => (
              <label key={phase} className="flex items-center justify-between">
                <span className="text-sm">
                  {phase === 'phase1' && 'Phase 1: 性能优化'}
                  {phase === 'phase2' && 'Phase 2: 错误处理'}
                  {phase === 'phase3' && 'Phase 3: 用户引导'}
                  {phase === 'phase4' && 'Phase 4: 可访问性'}
                </span>
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => onConfigChange({
                    features: {
                      ...config.features,
                      [phase]: e.target.checked
                    }
                  })}
                  className="w-4 h-4"
                />
              </label>
            ))}
          </div>
        )}
        
        {activeTab === 'features' && (
          <div className="space-y-3">
            <h4 className="font-medium">功能开关</h4>
            
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">性能优化</div>
              <label className="flex items-center justify-between text-sm">
                <span>智能预加载</span>
                <input
                  type="checkbox"
                  checked={config.enableSmartPreload}
                  onChange={(e) => onConfigChange({ enableSmartPreload: e.target.checked })}
                  className="w-4 h-4"
                />
              </label>
              <label className="flex items-center justify-between text-sm">
                <span>乐观更新</span>
                <input
                  type="checkbox"
                  checked={config.enableOptimisticUpdates}
                  onChange={(e) => onConfigChange({ enableOptimisticUpdates: e.target.checked })}
                  className="w-4 h-4"
                />
              </label>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">可访问性</div>
              <label className="flex items-center justify-between text-sm">
                <span>WCAG合规</span>
                <input
                  type="checkbox"
                  checked={config.enableWCAGCompliance}
                  onChange={(e) => onConfigChange({ enableWCAGCompliance: e.target.checked })}
                  className="w-4 h-4"
                />
              </label>
              <label className="flex items-center justify-between text-sm">
                <span>屏幕阅读器</span>
                <input
                  type="checkbox"
                  checked={config.enableScreenReaderSupport}
                  onChange={(e) => onConfigChange({ enableScreenReaderSupport: e.target.checked })}
                  className="w-4 h-4"
                />
              </label>
            </div>
          </div>
        )}
        
        {activeTab === 'advanced' && (
          <div className="space-y-3">
            <h4 className="font-medium">高级设置</h4>
            
            <div>
              <label className="block text-sm font-medium mb-2">部署阶段</label>
              <select
                value={config.phase}
                onChange={(e) => onConfigChange({ phase: e.target.value as any })}
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="development">开发环境</option>
                <option value="testing">测试环境</option>
                <option value="production">生产环境</option>
              </select>
            </div>
            
            <label className="flex items-center justify-between text-sm">
              <span>显示UX控制面板</span>
              <input
                type="checkbox"
                checked={config.showUXControls}
                onChange={(e) => onConfigChange({ showUXControls: e.target.checked })}
                className="w-4 h-4"
              />
            </label>
            
            <button
              onClick={() => onConfigChange(DEFAULT_CONFIG)}
              className="w-full px-3 py-2 text-sm bg-muted rounded hover:bg-muted/80"
            >
              重置为默认配置
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
