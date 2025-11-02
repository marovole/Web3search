import React, { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { 
  ArrowRight, 
  ArrowLeft, 
  Check, 
  X, 
  Play, 
  Skip,
  Sparkles,
  Target,
  Zap,
  Star,
  Users,
  Settings,
  HelpCircle
} from 'lucide-react'

/**
 * 引导步骤接口
 */
export interface OnboardingStep {
  id: string
  title: string
  description: string
  content: React.ReactNode
  target?: string // CSS选择器，用于高亮特定元素
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center'
  canSkip?: boolean
  required?: boolean
  action?: {
    label: string
    action: () => void | Promise<void>
  }
}

/**
 * 引导配置
 */
export interface OnboardingConfig {
  steps: OnboardingStep[]
  showProgress?: boolean
  showSkip?: boolean
  allowKeyboardNavigation?: boolean
  autoStart?: boolean
  onComplete?: () => void
  onSkip?: () => void
  onStepChange?: (stepIndex: number, step: OnboardingStep) => void
  storageKey?: string // 用于持久化引导状态
}

/**
 * 引导上下文Hook
 */
export const useOnboarding = (config: OnboardingConfig) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [isActive, setIsActive] = useState(config.autoStart || false)
  const [isCompleted, setIsCompleted] = useState(false)
  const [skippedSteps, setSkippedSteps] = useState<Set<string>>(new Set())

  // 从存储中恢复状态
  useEffect(() => {
    if (config.storageKey) {
      try {
        const saved = localStorage.getItem(config.storageKey)
        if (saved) {
          const data = JSON.parse(saved)
          setIsCompleted(data.completed || false)
          setSkippedSteps(new Set(data.skippedSteps || []))
          if (!data.completed && data.currentStep !== undefined) {
            setCurrentStep(data.currentStep)
            setIsActive(true)
          }
        }
      } catch (error) {
        console.warn('Failed to restore onboarding state:', error)
      }
    }
  }, [config.storageKey])

  // 保存状态到存储
  const saveState = useCallback((state: any) => {
    if (config.storageKey) {
      try {
        localStorage.setItem(config.storageKey, JSON.stringify(state))
      } catch (error) {
        console.warn('Failed to save onboarding state:', error)
      }
    }
  }, [config.storageKey])

  const start = useCallback(() => {
    setIsActive(true)
    setCurrentStep(0)
    saveState({ completed: false, currentStep: 0, skippedSteps: Array.from(skippedSteps) })
  }, [saveState, skippedSteps])

  const next = useCallback(() => {
    if (currentStep < config.steps.length - 1) {
      const nextStep = currentStep + 1
      setCurrentStep(nextStep)
      config.onStepChange?.(nextStep, config.steps[nextStep])
      saveState({ 
        completed: false, 
        currentStep: nextStep, 
        skippedSteps: Array.from(skippedSteps) 
      })
    } else {
      complete()
    }
  }, [currentStep, config, saveState, skippedSteps])

  const previous = useCallback(() => {
    if (currentStep > 0) {
      const prevStep = currentStep - 1
      setCurrentStep(prevStep)
      config.onStepChange?.(prevStep, config.steps[prevStep])
      saveState({ 
        completed: false, 
        currentStep: prevStep, 
        skippedSteps: Array.from(skippedSteps) 
      })
    }
  }, [currentStep, config, saveState, skippedSteps])

  const skip = useCallback(() => {
    const currentStepData = config.steps[currentStep]
    if (currentStepData && !currentStepData.required) {
      setSkippedSteps(prev => new Set(prev).add(currentStepData.id))
    }
    
    if (currentStep < config.steps.length - 1) {
      next()
    } else {
      config.onSkip?.()
      setIsActive(false)
      saveState({ 
        completed: false, 
        currentStep: -1, 
        skippedSteps: Array.from(skippedSteps) 
      })
    }
  }, [currentStep, config, next, saveState, skippedSteps])

  const complete = useCallback(() => {
    setIsActive(false)
    setIsCompleted(true)
    config.onComplete?.()
    saveState({ completed: true, currentStep: -1, skippedSteps: [] })
  }, [config, saveState])

  const goToStep = useCallback((stepIndex: number) => {
    if (stepIndex >= 0 && stepIndex < config.steps.length) {
      setCurrentStep(stepIndex)
      config.onStepChange?.(stepIndex, config.steps[stepIndex])
      saveState({ 
        completed: false, 
        currentStep: stepIndex, 
        skippedSteps: Array.from(skippedSteps) 
      })
    }
  }, [config, saveState, skippedSteps])

  const reset = useCallback(() => {
    setCurrentStep(0)
    setIsActive(false)
    setIsCompleted(false)
    setSkippedSteps(new Set())
    saveState({ completed: false, currentStep: -1, skippedSteps: [] })
  }, [saveState])

  // 键盘导航
  useEffect(() => {
    if (!isActive || !config.allowKeyboardNavigation) return

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowRight':
        case ' ':
          e.preventDefault()
          next()
          break
        case 'ArrowLeft':
          e.preventDefault()
          previous()
          break
        case 'Escape':
          e.preventDefault()
          skip()
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isActive, config.allowKeyboardNavigation, next, previous, skip])

  return {
    currentStep,
    isActive,
    isCompleted,
    skippedSteps,
    start,
    next,
    previous,
    skip,
    complete,
    goToStep,
    reset,
    totalSteps: config.steps.length,
    progress: ((currentStep + 1) / config.steps.length) * 100
  }
}

/**
 * 引导遮罩层组件
 */
export const OnboardingOverlay: React.FC<{
  target?: string
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center'
  children: React.ReactNode
  className?: string
}> = ({ target, position = 'bottom', children, className }) => {
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null)
  const [highlightRect, setHighlightRect] = useState<DOMRect | null>(null)

  useEffect(() => {
    if (target) {
      const element = document.querySelector(target) as HTMLElement
      setTargetElement(element)
      
      if (element) {
        const rect = element.getBoundingClientRect()
        setHighlightRect(rect)
        
        // 滚动到目标元素
        element.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center', 
          inline: 'center' 
        })
      }
    }
  }, [target])

  if (!target || !targetElement || !highlightRect) {
    return (
      <div className={cn(
        "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
        className
      )}>
        {children}
      </div>
    )
  }

  const overlayStyle = {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 50,
    pointerEvents: 'none' as const
  }

  const highlightStyle = {
    position: 'absolute' as const,
    top: highlightRect.top - 8,
    left: highlightRect.left - 8,
    width: highlightRect.width + 16,
    height: highlightRect.height + 16,
    borderRadius: '8px',
    boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.5)',
    pointerEvents: 'auto' as const
  }

  const getContentPosition = () => {
    const tooltipWidth = 400
    const tooltipHeight = 200
    const margin = 20

    let top = highlightRect.top
    let left = highlightRect.left

    switch (position) {
      case 'top':
        top = highlightRect.top - tooltipHeight - margin
        left = highlightRect.left + (highlightRect.width - tooltipWidth) / 2
        break
      case 'bottom':
        top = highlightRect.bottom + margin
        left = highlightRect.left + (highlightRect.width - tooltipWidth) / 2
        break
      case 'left':
        top = highlightRect.top + (highlightRect.height - tooltipHeight) / 2
        left = highlightRect.left - tooltipWidth - margin
        break
      case 'right':
        top = highlightRect.top + (highlightRect.height - tooltipHeight) / 2
        left = highlightRect.right + margin
        break
      case 'center':
        top = '50%'
        left = '50%'
        break
    }

    // 确保不超出视窗边界
    if (left < margin) left = margin
    if (left + tooltipWidth > window.innerWidth - margin) {
      left = window.innerWidth - tooltipWidth - margin
    }
    if (top < margin) top = margin
    if (top + tooltipHeight > window.innerHeight - margin) {
      top = window.innerHeight - tooltipHeight - margin
    }

    return { top, left, position: position === 'center' ? 'fixed' : 'absolute' }
  }

  const contentPosition = getContentPosition()

  return (
    <>
      <div style={overlayStyle} />
      <div style={highlightStyle} />
      <div
        style={{
          ...contentPosition,
          transform: position === 'center' ? 'translate(-50%, -50%)' : undefined,
          zIndex: 51,
          pointerEvents: 'auto'
        }}
      >
        {children}
      </div>
    </>
  )
}

/**
 * 引导步骤组件
 */
export const OnboardingStep: React.FC<{
  step: OnboardingStep
  stepNumber: number
  totalSteps: number
  onNext: () => void
  onPrevious: () => void
  onSkip: () => void
  onComplete?: () => void
  showProgress?: boolean
  showSkip?: boolean
}> = ({ 
  step, 
  stepNumber, 
  totalSteps, 
  onNext, 
  onPrevious, 
  onSkip, 
  onComplete,
  showProgress = true,
  showSkip = true 
}) => {
  const isLastStep = stepNumber === totalSteps - 1
  const isFirstStep = stepNumber === 0

  return (
    <Card className="w-full max-w-md p-6 space-y-4 bg-white shadow-xl">
      {/* 进度指示器 */}
      {showProgress && (
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm text-muted-foreground">
            <span>步骤 {stepNumber + 1} / {totalSteps}</span>
            <span>{Math.round(((stepNumber + 1) / totalSteps) * 100)}%</span>
          </div>
          <Progress value={((stepNumber + 1) / totalSteps) * 100} />
        </div>
      )}

      {/* 步骤内容 */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white text-sm font-medium">
            {stepNumber + 1}
          </div>
          <h3 className="text-lg font-semibold text-foreground">
            {step.title}
          </h3>
        </div>
        
        <p className="text-sm text-muted-foreground leading-relaxed">
          {step.description}
        </p>
        
        {step.content && (
          <div className="py-2">
            {step.content}
          </div>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2">
        {!isFirstStep && (
          <Button variant="outline" onClick={onPrevious} className="flex-1">
            <ArrowLeft className="w-4 h-4 mr-2" />
            上一步
          </Button>
        )}
        
        <div className="flex-1 flex gap-2">
          {showSkip && step.canSkip && !isLastStep && (
            <Button variant="ghost" onClick={onSkip}>
              <Skip className="w-4 h-4 mr-2" />
              跳过
            </Button>
          )}
          
          {step.action ? (
            <Button onClick={step.action.action} className="flex-1">
              {step.action.label}
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : isLastStep ? (
            <Button onClick={onComplete} className="flex-1">
              <Check className="w-4 h-4 mr-2" />
              完成
            </Button>
          ) : (
            <Button onClick={onNext} className="flex-1">
              下一步
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}

/**
 * 主引导组件
 */
export const OnboardingFlow: React.FC<{
  config: OnboardingConfig
  trigger?: React.ReactNode
  className?: string
}> = ({ config, trigger, className }) => {
  const onboarding = useOnboarding(config)

  if (!onboarding.isActive) {
    return (
      <>
        {trigger && (
          <div onClick={onboarding.start} className={cn("cursor-pointer", className)}>
            {trigger}
          </div>
        )}
      </>
    )
  }

  const currentStepData = config.steps[onboarding.currentStep]

  return (
    <OnboardingOverlay
      target={currentStepData?.target}
      position={currentStepData?.position}
    >
      <OnboardingStep
        step={currentStepData}
        stepNumber={onboarding.currentStep}
        totalSteps={onboarding.totalSteps}
        onNext={onboarding.next}
        onPrevious={onboarding.previous}
        onSkip={onboarding.skip}
        onComplete={onboarding.complete}
        showProgress={config.showProgress}
        showSkip={config.showSkip}
      />
    </OnboardingOverlay>
  )
}

/**
 * 欢迎页面组件
 */
export const WelcomePage: React.FC<{
  onStart: () => void
  onSkip: () => void
  title?: string
  description?: string
  features?: Array<{
    icon: React.ReactNode
    title: string
    description: string
  }>
  className?: string
}> = ({ 
  onStart, 
  onSkip, 
  title = "欢迎使用我们的产品",
  description = "让我们用几分钟时间了解主要功能",
  features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: "快速上手",
      description: "简洁直观的界面设计"
    },
    {
      icon: <Target className="w-6 h-6" />,
      title: "精准搜索",
      description: "强大的搜索和分析功能"
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "团队协作",
      description: "实时协作和共享功能"
    }
  ],
  className 
}) => {
  return (
    <div className={cn(
      "fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/20 p-8",
      className
    )}>
      <Card className="w-full max-w-2xl p-8 space-y-6 bg-white/95 backdrop-blur">
        {/* 头部 */}
        <div className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">
              {title}
            </h1>
            <p className="text-lg text-muted-foreground">
              {description}
            </p>
          </div>
        </div>

        {/* 功能介绍 */}
        <div className="grid gap-4 md:grid-cols-3">
          {features.map((feature, index) => (
            <div key={index} className="text-center space-y-2">
              <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center text-primary">
                {feature.icon}
              </div>
              <h3 className="font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="text-sm text-muted-foreground">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-4">
          <Button onClick={onSkip} variant="outline" className="flex-1">
            跳过引导
          </Button>
          <Button onClick={onStart} className="flex-1">
            <Play className="w-4 h-4 mr-2" />
            开始引导
          </Button>
        </div>

        {/* 提示 */}
        <div className="text-center text-sm text-muted-foreground">
          <p>您可以随时在设置中重新开始引导</p>
        </div>
      </Card>
    </div>
  )
}

/**
 * 快速提示组件
 */
export const QuickTip: React.FC<{
  title: string
  description: string
  icon?: React.ReactNode
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
  onClose: () => void
  autoClose?: boolean
  duration?: number
  className?: string
}> = ({ 
  title, 
  description, 
  icon = <HelpCircle className="w-5 h-5" />,
  position = 'bottom-right',
  onClose,
  autoClose = true,
  duration = 5000,
  className 
}) => {
  useEffect(() => {
    if (autoClose) {
      const timer = setTimeout(onClose, duration)
      return () => clearTimeout(timer)
    }
  }, [autoClose, duration, onClose])

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4'
  }

  return (
    <Card className={cn(
      "fixed z-40 w-80 p-4 space-y-3 shadow-lg animate-slide-in",
      positionClasses[position],
      className
    )}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 text-primary">
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-foreground text-sm">
            {title}
          </h4>
          <p className="text-xs text-muted-foreground mt-1">
            {description}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="flex-shrink-0 h-6 w-6 p-0"
        >
          <X className="w-3 h-3" />
        </Button>
      </div>
    </Card>
  )
}

/**
 * 引导管理器Hook
 */
export const useOnboardingManager = () => {
  const [showWelcome, setShowWelcome] = useState(false)
  const [showQuickTip, setShowQuickTip] = useState(false)
  const [currentTip, setCurrentTip] = useState<any>(null)

  const showWelcomePage = useCallback(() => {
    setShowWelcome(true)
  }, [])

  const hideWelcomePage = useCallback(() => {
    setShowWelcome(false)
  }, [])

  const showTip = useCallback((tip: any) => {
    setCurrentTip(tip)
    setShowQuickTip(true)
  }, [])

  const hideTip = useCallback(() => {
    setShowQuickTip(false)
    setCurrentTip(null)
  }, [])

  return {
    showWelcomePage,
    hideWelcomePage,
    showTip,
    hideTip,
    isWelcomeVisible: showWelcome,
    isTipVisible: showQuickTip,
    currentTip
  }
}
