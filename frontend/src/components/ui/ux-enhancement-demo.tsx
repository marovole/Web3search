import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Accessibility, 
  Zap, 
  Smartphone, 
  MousePointer, 
  TestTube,
  Eye,
  EyeOff,
  Volume2,
  VolumeX,
  Settings,
  RefreshCw,
  Download,
  Upload,
  Info,
  CheckCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react'
import { 
  AccessibilityProvider, 
  AccessibilityPanel,
  AccessibilityToolbar 
} from './accessibility-wcag'
import { 
  AccessibilityNavigationProvider,
  KeyboardNavigationGuide,
  ScreenReaderControls 
} from './accessibility-navigation'
import { 
  MicroInteractionProvider,
  Animated,
  InteractiveFeedback,
  LoadingAnimation,
  MicroInteractionPanel
} from './micro-interactions'
import { 
  TouchOptimized,
  GestureDemo,
  MobileOptimizationPanel 
} from './mobile-touch'
import { 
  UXTestProvider,
  UXTestPanel 
} from './ux-testing'
import { 
  ErrorBoundary,
  ErrorFeedback 
} from './error-feedback'
import { 
  Onboarding,
  OnboardingProvider 
} from './onboarding'
import { 
  InteractiveHelp,
  HelpTooltip 
} from './interactive-help'
import { 
  FeatureDiscovery,
  FeatureTour 
} from './feature-discovery'
import { 
  HelpDocuments,
  HelpCenter 
} from './help-documents'
import { 
  UserFeedback,
  QuickFeedbackButton,
  FeedbackForm 
} from './user-feedback'

/**
 * UX增强演示页面
 */
export const UXEnhancementDemo: React.FC = () => {
  const [activeDemo, setActiveDemo] = useState<string>('overview')
  const [showControls, setShowControls] = useState(true)

  const demos = [
    {
      id: 'overview',
      name: '概览',
      icon: <Info className="w-4 h-4" />,
      description: '所有UX增强功能概览'
    },
    {
      id: 'accessibility',
      name: '可访问性',
      icon: <Accessibility className="w-4 h-4" />,
      description: 'WCAG合规、屏幕阅读器、键盘导航'
    },
    {
      id: 'interactions',
      name: '微交互',
      icon: <MousePointer className="w-4 h-4" />,
      description: '动画、过渡、交互反馈'
    },
    {
      id: 'mobile',
      name: '移动端',
      icon: <Smartphone className="w-4 h-4" />,
      description: '触摸优化、手势支持'
    },
    {
      id: 'testing',
      name: 'UX测试',
      icon: <TestTube className="w-4 h-4" />,
      description: '自动化测试、性能监控'
    },
    {
      id: 'error',
      name: '错误处理',
      icon: <AlertTriangle className="w-4 h-4" />,
      description: '错误边界、用户反馈'
    },
    {
      id: 'onboarding',
      name: '用户引导',
      icon: <Eye className="w-4 h-4" />,
      description: '新手引导、功能发现'
    },
    {
      id: 'help',
      name: '帮助系统',
      icon: <Settings className="w-4 h-4" />,
      description: '帮助文档、交互式帮助'
    }
  ]

  const renderDemoContent = () => {
    switch (activeDemo) {
      case 'overview':
        return <OverviewDemo />
      case 'accessibility':
        return <AccessibilityDemo />
      case 'interactions':
        return <InteractionDemo />
      case 'mobile':
        return <MobileDemo />
      case 'testing':
        return <TestingDemo />
      case 'error':
        return <ErrorDemo />
      case 'onboarding':
        return <OnboardingDemo />
      case 'help':
        return <HelpDemo />
      default:
        return <OverviewDemo />
    }
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 头部 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">UX增强功能演示</h1>
            <p className="text-muted-foreground mt-2">
              体验现代化的用户界面增强功能
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setShowControls(!showControls)}
            >
              {showControls ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
              {showControls ? '隐藏控制面板' : '显示控制面板'}
            </Button>
          </div>
        </div>

        {/* 导航标签 */}
        <div className="border-b border-border">
          <nav className="flex space-x-1 overflow-x-auto">
            {demos.map((demo) => (
              <button
                key={demo.id}
                onClick={() => setActiveDemo(demo.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                  activeDemo === demo.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                {demo.icon}
                {demo.name}
              </button>
            ))}
          </nav>
        </div>

        {/* 演示内容 */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            {renderDemoContent()}
          </div>
          
          {/* 控制面板 */}
          {showControls && (
            <div className="lg:col-span-1">
              <div className="sticky top-6 space-y-4">
                <MicroInteractionPanel
                  config={{
                    enabled: true,
                    reducedMotion: false,
                    respectPreferences: true,
                    defaultDuration: 300,
                    defaultEasing: 'ease-out',
                    staggerDelay: 100,
                    hoverEffects: true,
                    clickEffects: true,
                    focusEffects: true,
                    loadingEffects: true,
                    enableGPU: true,
                    throttleAnimations: false,
                    maxConcurrentAnimations: 10,
                    pauseOnHover: false,
                    showControls: true,
                    announceAnimations: false
                  }}
                  onConfigChange={() => {}}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * 概览演示
 */
const OverviewDemo: React.FC = () => {
  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">UX增强功能概览</h2>
        <p className="text-muted-foreground mb-6">
          这个演示展示了所有可用的UX增强功能，包括性能优化、可访问性、微交互等。
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Animated
            animation={{
              type: 'fade',
              duration: 500,
              delay: 0
            }}
          >
            <Card className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Zap className="w-5 h-5 text-blue-500" />
                <h3 className="font-semibold">性能优化</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                智能预加载、骨架屏、离线支持等功能，显著提升应用性能。
              </p>
            </Card>
          </Animated>
          
          <Animated
            animation={{
              type: 'fade',
              duration: 500,
              delay: 100
            }}
          >
            <Card className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Accessibility className="w-5 h-5 text-green-500" />
                <h3 className="font-semibold">可访问性</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                WCAG 2.1 AA合规、屏幕阅读器支持、键盘导航等。
              </p>
            </Card>
          </Animated>
          
          <Animated
            animation={{
              type: 'fade',
              duration: 500,
              delay: 200
            }}
          >
            <Card className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <MousePointer className="w-5 h-5 text-purple-500" />
                <h3 className="font-semibold">微交互</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                丰富的动画效果、交互反馈、加载动画等。
              </p>
            </Card>
          </Animated>
          
          <Animated
            animation={{
              type: 'fade',
              duration: 500,
              delay: 300
            }}
          >
            <Card className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Smartphone className="w-5 h-5 text-orange-500" />
                <h3 className="font-semibold">移动端优化</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                触摸手势、大触摸目标、响应式设计等。
              </p>
            </Card>
          </Animated>
        </div>
      </Card>
    </div>
  )
}

/**
 * 可访问性演示
 */
const AccessibilityDemo: React.FC = () => {
  return (
    <AccessibilityProvider>
      <AccessibilityNavigationProvider>
        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">可访问性功能演示</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">可访问性工具栏</h3>
                <AccessibilityToolbar />
              </div>
              
              <div>
                <h3 className="font-medium mb-2">键盘导航指南</h3>
                <KeyboardNavigationGuide />
              </div>
              
              <div>
                <h3 className="font-medium mb-2">屏幕阅读器控制</h3>
                <ScreenReaderControls />
              </div>
            </div>
          </Card>
        </div>
      </AccessibilityNavigationProvider>
    </AccessibilityProvider>
  )
}

/**
 * 微交互演示
 */
const InteractionDemo: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false)
  
  return (
    <MicroInteractionProvider>
      <div className="space-y-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">微交互功能演示</h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="font-medium mb-3">动画效果</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Animated
                  animation={{
                    type: 'bounce',
                    duration: 1000,
                    repeat: 'infinite'
                  }}
                >
                  <Button className="w-full">弹跳动画</Button>
                </Animated>
                
                <Animated
                  animation={{
                    type: 'pulse',
                    duration: 1500,
                    repeat: 'infinite'
                  }}
                >
                  <Button variant="outline" className="w-full">脉冲动画</Button>
                </Animated>
                
                <Animated
                  animation={{
                    type: 'shake',
                    duration: 500,
                    trigger: 'hover'
                  }}
                >
                  <Button variant="secondary" className="w-full">悬停震动</Button>
                </Animated>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-3">交互反馈</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <InteractiveFeedback feedback="hover">
                  <Card className="p-4 text-center cursor-pointer">
                    悬停效果
                  </Card>
                </InteractiveFeedback>
                
                <InteractiveFeedback feedback="click">
                  <Card className="p-4 text-center cursor-pointer">
                    点击效果
                  </Card>
                </InteractiveFeedback>
                
                <InteractiveFeedback feedback="all">
                  <Card className="p-4 text-center cursor-pointer">
                    全部效果
                  </Card>
                </InteractiveFeedback>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-3">加载动画</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <LoadingAnimation type="spinner" size="md" />
                  <p className="text-sm mt-2">旋转器</p>
                </div>
                <div className="text-center">
                  <LoadingAnimation type="dots" size="md" />
                  <p className="text-sm mt-2">点状</p>
                </div>
                <div className="text-center">
                  <LoadingAnimation type="pulse" size="md" />
                  <p className="text-sm mt-2">脉冲</p>
                </div>
                <div className="text-center">
                  <LoadingAnimation type="skeleton" size="md" />
                  <p className="text-sm mt-2">骨架</p>
                </div>
              </div>
            </div>
            
            <div>
              <Button 
                onClick={() => {
                  setIsLoading(true)
                  setTimeout(() => setIsLoading(false), 2000)
                }}
                disabled={isLoading}
              >
                {isLoading ? <LoadingAnimation type="spinner" size="sm" /> : null}
                {isLoading ? '加载中...' : '模拟加载'}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </MicroInteractionProvider>
  )
}

/**
 * 移动端演示
 */
const MobileDemo: React.FC = () => {
  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">移动端触摸优化演示</h2>
        
        <div className="space-y-6">
          <div>
            <h3 className="font-medium mb-3">手势演示</h3>
            <GestureDemo onGesture={(gesture) => console.log('Gesture:', gesture)} />
          </div>
          
          <div>
            <h3 className="font-medium mb-3">移动端优化面板</h3>
            <MobileOptimizationPanel
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
                hapticFeedback: true,
                visualFeedback: true,
                soundFeedback: false,
                throttleMs: 16,
                debounceMs: 100,
                reducedMotion: false,
                largeTouchTargets: true,
                highContrast: false
              }}
              onConfigChange={() => {}}
              device={{
                deviceType: 'mobile',
                isTouchDevice: true,
                screenSize: { width: 375, height: 667 },
                isMobile: true,
                isTablet: false,
                isDesktop: false
              }}
            />
          </div>
        </div>
      </Card>
    </div>
  )
}

/**
 * UX测试演示
 */
const TestingDemo: React.FC = () => {
  return (
    <UXTestProvider showPanel={true}>
      <div className="space-y-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">UX测试工具演示</h2>
          <p className="text-muted-foreground">
            右下角显示UX测试控制面板，可以运行各种用户体验测试。
          </p>
        </Card>
      </div>
    </UXTestProvider>
  )
}

/**
 * 错误处理演示
 */
const ErrorDemo: React.FC = () => {
  const [shouldError, setShouldError] = useState(false)
  
  if (shouldError) {
    throw new Error('这是一个演示错误！')
  }
  
  return (
    <ErrorBoundary>
      <div className="space-y-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">错误处理演示</h2>
          
          <div className="space-y-4">
            <p className="text-muted-foreground">
              点击下面的按钮触发错误，体验错误边界和错误反馈功能。
            </p>
            
            <Button 
              variant="destructive"
              onClick={() => setShouldError(true)}
            >
              触发演示错误
            </Button>
            
            <ErrorFeedback />
          </div>
        </Card>
      </div>
    </ErrorBoundary>
  )
}

/**
 * 用户引导演示
 */
const OnboardingDemo: React.FC = () => {
  return (
    <OnboardingProvider>
      <div className="space-y-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">用户引导演示</h2>
          
          <div className="space-y-4">
            <Onboarding
              steps={[
                {
                  id: 'welcome',
                  title: '欢迎使用UX增强功能',
                  content: '这是一个现代化的用户界面增强系统。',
                  target: '.demo-target-1'
                },
                {
                  id: 'features',
                  title: '丰富的功能',
                  content: '包括性能优化、可访问性、微交互等。',
                  target: '.demo-target-2'
                },
                {
                  id: 'customization',
                  title: '个性化定制',
                  content: '您可以根据需要调整各种设置。',
                  target: '.demo-target-3'
                }
              ]}
            />
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="p-4 demo-target-1">
                <h3 className="font-medium">目标1</h3>
                <p className="text-sm text-muted-foreground">引导目标</p>
              </Card>
              <Card className="p-4 demo-target-2">
                <h3 className="font-medium">目标2</h3>
                <p className="text-sm text-muted-foreground">引导目标</p>
              </Card>
              <Card className="p-4 demo-target-3">
                <h3 className="font-medium">目标3</h3>
                <p className="text-sm text-muted-foreground">引导目标</p>
              </Card>
            </div>
          </div>
        </Card>
      </div>
    </OnboardingProvider>
  )
}

/**
 * 帮助系统演示
 */
const HelpDemo: React.FC = () => {
  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">帮助系统演示</h2>
        
        <div className="space-y-6">
          <div>
            <h3 className="font-medium mb-3">交互式帮助</h3>
            <div className="space-y-4">
              <InteractiveHelp
                content="这是一个帮助提示，您可以点击了解更多信息。"
                position="top"
              >
                <Button variant="outline">悬停查看帮助</Button>
              </InteractiveHelp>
              
              <HelpTooltip content="工具提示帮助信息">
                <Button variant="outline">工具提示</Button>
              </HelpTooltip>
            </div>
          </div>
          
          <div>
            <h3 className="font-medium mb-3">快速反馈</h3>
            <QuickFeedbackButton 
              type="suggestion"
              position="bottom-right"
            />
          </div>
          
          <div>
            <h3 className="font-medium mb-3">反馈表单</h3>
            <FeedbackForm />
          </div>
        </div>
      </Card>
    </div>
  )
}
