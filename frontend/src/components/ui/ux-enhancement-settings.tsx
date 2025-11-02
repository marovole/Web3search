import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Settings, 
  Zap, 
  Shield, 
  BookOpen, 
  Accessibility,
  Smartphone,
  MousePointer,
  TestTube,
  Save,
  RotateCcw,
  Info,
  CheckCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react'
import { UXEnhancementProvider, UXEnhancementControlPanel, useUXEnhancement, UXEnhancementConfig } from './ux-enhancement-provider'

/**
 * UX增强设置页面组件
 */
export const UXEnhancementSettings: React.FC = () => {
  const { config, updateConfig, resetConfig } = useUXEnhancement()
  const [hasChanges, setHasChanges] = useState(false)
  const [savedMessage, setSavedMessage] = useState(false)

  const handleConfigChange = (updates: Partial<UXEnhancementConfig>) => {
    updateConfig(updates)
    setHasChanges(true)
  }

  const handleSave = () => {
    setSavedMessage(true)
    setHasChanges(false)
    setTimeout(() => setSavedMessage(false), 3000)
  }

  const handleReset = () => {
    resetConfig()
    setHasChanges(false)
    setSavedMessage(true)
    setTimeout(() => setSavedMessage(false), 3000)
  }

  const getPhaseStatus = (phase: keyof UXEnhancementConfig['features']) => {
    if (!config.features[phase]) return 'disabled'
    
    // 检查该阶段的关键功能是否启用
    switch (phase) {
      case 'phase1':
        return config.enableSmartPreload && config.enableSkeletonScreens ? 'enabled' : 'partial'
      case 'phase2':
        return config.enableErrorBoundaries && config.enableErrorRecovery ? 'enabled' : 'partial'
      case 'phase3':
        return config.enableOnboarding && config.enableHelpDocumentation ? 'enabled' : 'partial'
      case 'phase4':
        return config.enableWCAGCompliance && config.enableKeyboardNavigation ? 'enabled' : 'partial'
      default:
        return 'partial'
    }
  }

  const getStatusIcon = (status: 'enabled' | 'partial' | 'disabled') => {
    switch (status) {
      case 'enabled': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'partial': return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'disabled': return <XCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusText = (status: 'enabled' | 'partial' | 'disabled') => {
    switch (status) {
      case 'enabled': return '已启用'
      case 'partial': return '部分启用'
      case 'disabled': return '已禁用'
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="w-6 h-6 text-primary" />
          <h1 className="text-2xl font-bold">UX增强设置</h1>
        </div>
        
        <div className="flex gap-2">
          {hasChanges && (
            <Button onClick={handleSave} className="flex items-center gap-2">
              <Save className="w-4 h-4" />
              保存更改
            </Button>
          )}
          
          <Button variant="outline" onClick={handleReset} className="flex items-center gap-2">
            <RotateCcw className="w-4 h-4" />
            重置默认
          </Button>
        </div>
      </div>

      {savedMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-green-800 text-sm">
          ✓ 设置已保存
        </div>
      )}

      {/* 功能阶段概览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3 mb-3">
            <Zap className="w-5 h-5 text-blue-500" />
            <h3 className="font-semibold">Phase 1</h3>
            {getStatusIcon(getPhaseStatus('phase1'))}
          </div>
          <p className="text-sm text-muted-foreground mb-2">性能和加载优化</p>
          <p className="text-xs text-muted-foreground">
            骨架屏、智能预加载、离线支持
          </p>
          <div className="mt-3 text-xs">
            状态: {getStatusText(getPhaseStatus('phase1'))}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3 mb-3">
            <Shield className="w-5 h-5 text-green-500" />
            <h3 className="font-semibold">Phase 2</h3>
            {getStatusIcon(getPhaseStatus('phase2'))}
          </div>
          <p className="text-sm text-muted-foreground mb-2">错误处理和用户支持</p>
          <p className="text-xs text-muted-foreground">
            错误边界、自动重试、反馈系统
          </p>
          <div className="mt-3 text-xs">
            状态: {getStatusText(getPhaseStatus('phase2'))}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3 mb-3">
            <BookOpen className="w-5 h-5 text-purple-500" />
            <h3 className="font-semibold">Phase 3</h3>
            {getStatusIcon(getPhaseStatus('phase3'))}
          </div>
          <p className="text-sm text-muted-foreground mb-2">用户引导和帮助系统</p>
          <p className="text-xs text-muted-foreground">
            新手引导、帮助文档、用户反馈
          </p>
          <div className="mt-3 text-xs">
            状态: {getStatusText(getPhaseStatus('phase3'))}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3 mb-3">
            <Accessibility className="w-5 h-5 text-orange-500" />
            <h3 className="font-semibold">Phase 4</h3>
            {getStatusIcon(getPhaseStatus('phase4'))}
          </div>
          <p className="text-sm text-muted-foreground mb-2">可访问性和交互优化</p>
          <p className="text-xs text-muted-foreground">
            WCAG合规、屏幕阅读器、触摸优化
          </p>
          <div className="mt-3 text-xs">
            状态: {getStatusText(getPhaseStatus('phase4'))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 控制面板 */}
        <div className="lg:col-span-1">
          <UXEnhancementControlPanel
            config={config}
            onConfigChange={handleConfigChange}
          />
        </div>

        {/* 详细设置 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 性能优化设置 */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <Zap className="w-5 h-5 text-blue-500" />
              <h2 className="text-lg font-semibold">性能优化</h2>
            </div>
            
            <div className="grid gap-4">
              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">智能预加载</div>
                  <div className="text-sm text-muted-foreground">
                    根据用户行为预加载可能需要的资源
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableSmartPreload}
                  onChange={(e) => handleConfigChange({ enableSmartPreload: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">乐观更新</div>
                  <div className="text-sm text-muted-foreground">
                    在服务器响应前更新UI，提供即时反馈
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableOptimisticUpdates}
                  onChange={(e) => handleConfigChange({ enableOptimisticUpdates: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">骨架屏</div>
                  <div className="text-sm text-muted-foreground">
                    显示内容占位符，改善加载体验
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableSkeletonScreens}
                  onChange={(e) => handleConfigChange({ enableSkeletonScreens: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">离线支持</div>
                  <div className="text-sm text-muted-foreground">
                    缓存关键资源，支持离线访问
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableOfflineSupport}
                  onChange={(e) => handleConfigChange({ enableOfflineSupport: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>
            </div>
          </Card>

          {/* 可访问性设置 */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <Accessibility className="w-5 h-5 text-orange-500" />
              <h2 className="text-lg font-semibold">可访问性</h2>
            </div>
            
            <div className="grid gap-4">
              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">WCAG 2.1 AA 合规</div>
                  <div className="text-sm text-muted-foreground">
                    遵循Web内容可访问性指南
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableWCAGCompliance}
                  onChange={(e) => handleConfigChange({ enableWCAGCompliance: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">屏幕阅读器支持</div>
                  <div className="text-sm text-muted-foreground">
                    为视觉障碍用户提供语音导航
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableScreenReaderSupport}
                  onChange={(e) => handleConfigChange({ enableScreenReaderSupport: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">键盘导航</div>
                  <div className="text-sm text-muted-foreground">
                    完整的键盘操作支持
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableKeyboardNavigation}
                  onChange={(e) => handleConfigChange({ enableKeyboardNavigation: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">触摸优化</div>
                  <div className="text-sm text-muted-foreground">
                    针对移动设备的触摸交互优化
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableTouchOptimization}
                  onChange={(e) => handleConfigChange({ enableTouchOptimization: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>
            </div>
          </Card>

          {/* 交互设置 */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <MousePointer className="w-5 h-5 text-purple-500" />
              <h2 className="text-lg font-semibold">交互体验</h2>
            </div>
            
            <div className="grid gap-4">
              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">微交互</div>
                  <div className="text-sm text-muted-foreground">
                    悬停、点击等细节动画效果
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableMicroInteractions}
                  onChange={(e) => handleConfigChange({ enableMicroInteractions: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">动画效果</div>
                  <div className="text-sm text-muted-foreground">
                    页面过渡和元素动画
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableAnimations}
                  onChange={(e) => handleConfigChange({ enableAnimations: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">手势支持</div>
                  <div className="text-sm text-muted-foreground">
                    触摸手势识别和响应
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableGestureSupport}
                  onChange={(e) => handleConfigChange({ enableGestureSupport: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>
            </div>
          </Card>

          {/* 测试和监控 */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <TestTube className="w-5 h-5 text-green-500" />
              <h2 className="text-lg font-semibold">测试和监控</h2>
            </div>
            
            <div className="grid gap-4">
              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">UX测试工具</div>
                  <div className="text-sm text-muted-foreground">
                    自动化用户体验测试
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enableUXTesting}
                  onChange={(e) => handleConfigChange({ enableUXTesting: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">性能监控</div>
                  <div className="text-sm text-muted-foreground">
                    实时性能指标监控
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.enablePerformanceMonitoring}
                  onChange={(e) => handleConfigChange({ enablePerformanceMonitoring: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div>
                  <div className="font-medium">显示UX控制面板</div>
                  <div className="text-sm text-muted-foreground">
                    在界面中显示UX调试工具
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={config.showUXControls}
                  onChange={(e) => handleConfigChange({ showUXControls: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>
            </div>
          </Card>

          {/* 信息提示 */}
          <Card className="p-4 bg-blue-50 border-blue-200">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-800">
                <h3 className="font-semibold mb-1">关于UX增强功能</h3>
                <p className="mb-2">
                  这些功能基于现代Web最佳实践设计，旨在提供更好的用户体验。
                  所有设置都会自动保存到本地存储中。
                </p>
                <p>
                  在生产环境中，某些调试和测试功能可能会被自动禁用以优化性能。
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
