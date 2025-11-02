import React, { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { 
  Sparkles, 
  Zap, 
  Heart, 
  Star, 
  ThumbsUp, 
  Check, 
  X,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  RotateCcw,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Eye,
  EyeOff,
  Settings,
  RefreshCw
} from 'lucide-react'

/**
 * 动画类型
 */
export type AnimationType = 
  | 'fade'
  | 'slide'
  | 'scale'
  | 'rotate'
  | 'bounce'
  | 'elastic'
  | 'shake'
  | 'pulse'
  | 'flip'
  | 'glow'
  | 'ripple'
  | 'morph'

/**
 * 动画方向
 */
export type AnimationDirection = 'up' | 'down' | 'left' | 'right' | 'in' | 'out'

/**
 * 动画配置
 */
export interface AnimationConfig {
  type: AnimationType
  direction?: AnimationDirection
  duration: number // ms
  delay?: number // ms
  easing?: string
  repeat?: number | 'infinite'
  autoPlay?: boolean
  trigger?: 'hover' | 'click' | 'scroll' | 'manual'
  reducedMotion?: boolean
}

/**
 * 微交互配置
 */
export interface MicroInteractionConfig {
  // 基础设置
  enabled: boolean
  reducedMotion: boolean
  respectPreferences: boolean
  
  // 动画设置
  defaultDuration: number
  defaultEasing: string
  staggerDelay: number
  
  // 反馈设置
  hoverEffects: boolean
  clickEffects: boolean
  focusEffects: boolean
  loadingEffects: boolean
  
  // 性能设置
  enableGPU: boolean
  throttleAnimations: boolean
  maxConcurrentAnimations: number
  
  // 可访问性
  pauseOnHover: boolean
  showControls: boolean
  announceAnimations: boolean
}

/**
 * 动画状态
 */
export interface AnimationState {
  isPlaying: boolean
  isPaused: boolean
  isCompleted: boolean
  currentIteration: number
  progress: number
}

/**
 * 微交互Hook
 */
export const useMicroInteractions = (config: MicroInteractionConfig) => {
  const [isInitialized, setIsInitialized] = useState(false)
  const [animationCount, setAnimationCount] = useState(0)
  const [isReducedMotion, setIsReducedMotion] = useState(false)

  useEffect(() => {
    // 检测用户的动画偏好
    if (config.respectPreferences) {
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      setIsReducedMotion(prefersReducedMotion)
    }

    // 设置CSS变量
    const root = document.documentElement
    root.style.setProperty('--animation-duration', `${config.defaultDuration}ms`)
    root.style.setProperty('--animation-easing', config.defaultEasing)
    root.style.setProperty('--stagger-delay', `${config.staggerDelay}ms`)

    // 添加全局样式
    if (config.enableGPU) {
      root.style.setProperty('--transform-gpu', 'translate3d(0, 0, 0)')
    }

    setIsInitialized(true)
  }, [config])

  const shouldAnimate = useCallback(() => {
    return config.enabled && !isReducedMotion && !config.reducedMotion
  }, [config, isReducedMotion])

  const createAnimation = useCallback((
    element: HTMLElement,
    animationConfig: AnimationConfig
  ): Animation => {
    if (!shouldAnimate()) {
      return new Animation([], {})
    }

    const keyframes = generateKeyframes(animationConfig)
    const options: KeyframeAnimationOptions = {
      duration: animationConfig.duration,
      delay: animationConfig.delay || 0,
      easing: animationConfig.easing || config.defaultEasing,
      iterations: animationConfig.repeat === 'infinite' ? Infinity : animationConfig.repeat || 1,
      fill: 'both'
    }

    return element.animate(keyframes, options)
  }, [shouldAnimate, config.defaultEasing])

  const triggerHoverEffect = useCallback((element: HTMLElement) => {
    if (!config.hoverEffects || !shouldAnimate()) return

    element.style.transform = 'scale(1.05)'
    element.style.transition = `transform ${config.defaultDuration}ms ${config.defaultEasing}`
    
    const handleMouseLeave = () => {
      element.style.transform = 'scale(1)'
      element.removeEventListener('mouseleave', handleMouseLeave)
    }
    
    element.addEventListener('mouseleave', handleMouseLeave)
  }, [config, shouldAnimate])

  const triggerClickEffect = useCallback((element: HTMLElement) => {
    if (!config.clickEffects || !shouldAnimate()) return

    const ripple = document.createElement('div')
    ripple.className = 'ripple-effect'
    ripple.style.position = 'absolute'
    ripple.style.borderRadius = '50%'
    ripple.style.background = 'rgba(255, 255, 255, 0.6)'
    ripple.style.transform = 'scale(0)'
    ripple.style.animation = 'ripple 0.6s ease-out'
    ripple.style.pointerEvents = 'none'

    const rect = element.getBoundingClientRect()
    const size = Math.max(rect.width, rect.height)
    ripple.style.width = ripple.style.height = size + 'px'
    ripple.style.left = '50%'
    ripple.style.top = '50%'
    ripple.style.marginLeft = -size / 2 + 'px'
    ripple.style.marginTop = -size / 2 + 'px'

    element.style.position = 'relative'
    element.style.overflow = 'hidden'
    element.appendChild(ripple)

    setTimeout(() => ripple.remove(), 600)
  }, [config, shouldAnimate])

  return {
    isInitialized,
    animationCount,
    isReducedMotion,
    shouldAnimate,
    createAnimation,
    triggerHoverEffect,
    triggerClickEffect
  }
}

/**
 * 生成关键帧
 */
const generateKeyframes = (config: AnimationConfig): Keyframe[] => {
  const { type, direction = 'in' } = config

  switch (type) {
    case 'fade':
      return direction === 'in' ? [
        { opacity: 0 },
        { opacity: 1 }
      ] : [
        { opacity: 1 },
        { opacity: 0 }
      ]

    case 'slide':
      const slideOffset = direction === 'up' ? '20px' : 
                         direction === 'down' ? '-20px' :
                         direction === 'left' ? '20px' : '-20px'
      const slideProperty = direction === 'up' || direction === 'down' ? 'translateY' : 'translateX'
      
      return direction === 'in' ? [
        { transform: `${slideProperty}(${slideOffset})`, opacity: 0 },
        { transform: `${slideProperty}(0)`, opacity: 1 }
      ] : [
        { transform: `${slideProperty}(0)`, opacity: 1 },
        { transform: `${slideProperty}(${slideOffset})`, opacity: 0 }
      ]

    case 'scale':
      return direction === 'in' ? [
        { transform: 'scale(0.8)', opacity: 0 },
        { transform: 'scale(1)', opacity: 1 }
      ] : [
        { transform: 'scale(1)', opacity: 1 },
        { transform: 'scale(0.8)', opacity: 0 }
      ]

    case 'bounce':
      return [
        { transform: 'translateY(0)' },
        { transform: 'translateY(-10px)' },
        { transform: 'translateY(0)' }
      ]

    case 'pulse':
      return [
        { transform: 'scale(1)' },
        { transform: 'scale(1.05)' },
        { transform: 'scale(1)' }
      ]

    case 'shake':
      return [
        { transform: 'translateX(0)' },
        { transform: 'translateX(-5px)' },
        { transform: 'translateX(5px)' },
        { transform: 'translateX(-5px)' },
        { transform: 'translateX(5px)' },
        { transform: 'translateX(0)' }
      ]

    case 'rotate':
      return [
        { transform: 'rotate(0deg)' },
        { transform: 'rotate(360deg)' }
      ]

    case 'flip':
      return [
        { transform: 'rotateY(0deg)' },
        { transform: 'rotateY(180deg)' }
      ]

    case 'glow':
      return [
        { boxShadow: '0 0 0 0 rgba(59, 130, 246, 0.5)' },
        { boxShadow: '0 0 20px 10px rgba(59, 130, 246, 0)' }
      ]

    default:
      return []
  }
}

/**
 * 动画组件
 */
export const Animated: React.FC<{
  children: React.ReactNode
  animation: AnimationConfig
  className?: string
  onAnimationStart?: () => void
  onAnimationEnd?: () => void
}> = ({ children, animation, className, onAnimationStart, onAnimationEnd }) => {
  const elementRef = useRef<HTMLElement>(null)
  const [isAnimating, setIsAnimating] = useState(false)

  const playAnimation = useCallback(() => {
    if (!elementRef.current) return

    setIsAnimating(true)
    onAnimationStart?.()

    const keyframes = generateKeyframes(animation)
    const options: KeyframeAnimationOptions = {
      duration: animation.duration,
      delay: animation.delay || 0,
      easing: animation.easing || 'ease-out',
      iterations: animation.repeat === 'infinite' ? Infinity : animation.repeat || 1,
      fill: 'both'
    }

    const anim = elementRef.current.animate(keyframes, options)

    anim.onfinish = () => {
      setIsAnimating(false)
      onAnimationEnd?.()
    }
  }, [animation, onAnimationStart, onAnimationEnd])

  useEffect(() => {
    if (animation.autoPlay) {
      playAnimation()
    }
  }, [animation.autoPlay, playAnimation])

  useEffect(() => {
    const element = elementRef.current
    if (!element) return

    const handleTrigger = () => {
      switch (animation.trigger) {
        case 'hover':
          element.addEventListener('mouseenter', playAnimation)
          break
        case 'click':
          element.addEventListener('click', playAnimation)
          break
      }
    }

    handleTrigger()

    return () => {
      element.removeEventListener('mouseenter', playAnimation)
      element.removeEventListener('click', playAnimation)
    }
  }, [animation.trigger, playAnimation])

  return (
    <div
      ref={elementRef}
      className={cn(
        'animated-element',
        isAnimating && 'animating',
        className
      )}
    >
      {children}
    </div>
  )
}

/**
 * 交错动画组件
 */
export const StaggeredAnimation: React.FC<{
  children: React.ReactNode[]
  animation: AnimationConfig
  staggerDelay?: number
  className?: string
}> = ({ children, animation, staggerDelay = 100, className }) => {
  return (
    <div className={cn("staggered-container", className)}>
      {children.map((child, index) => (
        <Animated
          key={index}
          animation={{
            ...animation,
            delay: (animation.delay || 0) + (index * staggerDelay)
          }}
        >
          {child}
        </Animated>
      ))}
    </div>
  )
}

/**
 * 交互反馈组件
 */
export const InteractiveFeedback: React.FC<{
  children: React.ReactNode
  feedback?: 'hover' | 'click' | 'focus' | 'all'
  intensity?: 'subtle' | 'normal' | 'strong'
  className?: string
}> = ({ 
  children, 
  feedback = 'all', 
  intensity = 'normal', 
  className 
}) => {
  const elementRef = useRef<HTMLElement>(null)

  const getIntensityClass = () => {
    switch (intensity) {
      case 'subtle': return 'feedback-subtle'
      case 'strong': return 'feedback-strong'
      default: return 'feedback-normal'
    }
  }

  const getFeedbackClass = () => {
    switch (feedback) {
      case 'hover': return 'feedback-hover'
      case 'click': return 'feedback-click'
      case 'focus': return 'feedback-focus'
      default: return 'feedback-all'
    }
  }

  return (
    <div
      ref={elementRef}
      className={cn(
        'interactive-feedback',
        getIntensityClass(),
        getFeedbackClass(),
        className
      )}
    >
      {children}
    </div>
  )
}

/**
 * 加载动画组件
 */
export const LoadingAnimation: React.FC<{
  type?: 'spinner' | 'dots' | 'pulse' | 'skeleton'
  size?: 'sm' | 'md' | 'lg'
  color?: string
  className?: string
}> = ({ 
  type = 'spinner', 
  size = 'md', 
  color = 'primary', 
  className 
}) => {
  const getSizeClass = () => {
    switch (size) {
      case 'sm': return 'w-4 h-4'
      case 'lg': return 'w-8 h-8'
      default: return 'w-6 h-6'
    }
  }

  const getColorClass = () => {
    return `text-${color}`
  }

  switch (type) {
    case 'spinner':
      return (
        <div className={cn(
          "animate-spin rounded-full border-2 border-current border-t-transparent",
          getSizeClass(),
          getColorClass(),
          className
        )} />
      )

    case 'dots':
      return (
        <div className={cn("flex gap-1", className)}>
          {[0, 1, 2].map(index => (
            <div
              key={index}
              className={cn(
                "w-2 h-2 bg-current rounded-full animate-bounce",
                getColorClass()
              )}
              style={{ animationDelay: `${index * 0.1}s` }}
            />
          ))}
        </div>
      )

    case 'pulse':
      return (
        <div className={cn(
          "w-6 h-6 bg-current rounded-full animate-pulse",
          getColorClass(),
          className
        )} />
      )

    case 'skeleton':
      return (
        <div className={cn(
          "animate-pulse bg-muted rounded",
          size === 'sm' ? 'h-4 w-16' : size === 'lg' ? 'h-8 w-32' : 'h-6 w-24',
          className
        )} />
      )

    default:
      return null
  }
}

/**
 * 微交互控制面板
 */
export const MicroInteractionPanel: React.FC<{
  config: MicroInteractionConfig
  onConfigChange: (updates: Partial<MicroInteractionConfig>) => void
  className?: string
}> = ({ config, onConfigChange, className }) => {
  const [testAnimation, setTestAnimation] = useState<AnimationType>('fade')
  const [isPlaying, setIsPlaying] = useState(false)

  const animationTypes: AnimationType[] = [
    'fade', 'slide', 'scale', 'bounce', 'elastic', 
    'shake', 'pulse', 'flip', 'glow', 'ripple'
  ]

  const runTestAnimation = () => {
    setIsPlaying(true)
    setTimeout(() => setIsPlaying(false), 1000)
  }

  return (
    <Card className={cn("p-6 space-y-6", className)}>
      {/* 头部 */}
      <div className="flex items-center gap-3">
        <Sparkles className="w-6 h-6 text-primary" />
        <h2 className="text-xl font-semibold">微交互设置</h2>
      </div>

      {/* 基础设置 */}
      <div className="space-y-3">
        <h3 className="font-semibold">基础设置</h3>
        
        <label className="flex items-center justify-between">
          <span>启用微交互</span>
          <input
            type="checkbox"
            checked={config.enabled}
            onChange={(e) => onConfigChange({ enabled: e.target.checked })}
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
          <span>尊重用户偏好</span>
          <input
            type="checkbox"
            checked={config.respectPreferences}
            onChange={(e) => onConfigChange({ respectPreferences: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
      </div>

      {/* 动画设置 */}
      <div className="space-y-3">
        <h3 className="font-semibold">动画设置</h3>
        
        <div>
          <label className="block text-sm font-medium mb-1">
            默认时长: {config.defaultDuration}ms
          </label>
          <input
            type="range"
            min="100"
            max="2000"
            step="100"
            value={config.defaultDuration}
            onChange={(e) => onConfigChange({ defaultDuration: parseInt(e.target.value) })}
            className="w-full"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-1">
            交错延迟: {config.staggerDelay}ms
          </label>
          <input
            type="range"
            min="0"
            max="500"
            step="50"
            value={config.staggerDelay}
            onChange={(e) => onConfigChange({ staggerDelay: parseInt(e.target.value) })}
            className="w-full"
          />
        </div>
      </div>

      {/* 反馈设置 */}
      <div className="space-y-3">
        <h3 className="font-semibold">交互反馈</h3>
        
        <label className="flex items-center justify-between">
          <span>悬停效果</span>
          <input
            type="checkbox"
            checked={config.hoverEffects}
            onChange={(e) => onConfigChange({ hoverEffects: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>点击效果</span>
          <input
            type="checkbox"
            checked={config.clickEffects}
            onChange={(e) => onConfigChange({ clickEffects: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>焦点效果</span>
          <input
            type="checkbox"
            checked={config.focusEffects}
            onChange={(e) => onConfigChange({ focusEffects: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>加载效果</span>
          <input
            type="checkbox"
            checked={config.loadingEffects}
            onChange={(e) => onConfigChange({ loadingEffects: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
      </div>

      {/* 性能设置 */}
      <div className="space-y-3">
        <h3 className="font-semibold">性能优化</h3>
        
        <label className="flex items-center justify-between">
          <span>GPU加速</span>
          <input
            type="checkbox"
            checked={config.enableGPU}
            onChange={(e) => onConfigChange({ enableGPU: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
        
        <label className="flex items-center justify-between">
          <span>限制并发动画</span>
          <input
            type="checkbox"
            checked={config.throttleAnimations}
            onChange={(e) => onConfigChange({ throttleAnimations: e.target.checked })}
            className="w-4 h-4"
          />
        </label>
      </div>

      {/* 测试区域 */}
      <div className="space-y-4">
        <h3 className="font-semibold">测试动画</h3>
        
        <div className="grid gap-2">
          <select
            value={testAnimation}
            onChange={(e) => setTestAnimation(e.target.value as AnimationType)}
            className="border rounded px-3 py-2"
          >
            {animationTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          
          <Button onClick={runTestAnimation} disabled={isPlaying}>
            {isPlaying ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                播放中...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                测试动画
              </>
            )}
          </Button>
        </div>
        
        {/* 测试元素 */}
        <div className="flex justify-center p-8 bg-muted rounded-lg">
          <Animated
            animation={{
              type: testAnimation,
              duration: config.defaultDuration,
              autoPlay: false
            }}
          >
            <div className="w-16 h-16 bg-primary rounded-lg flex items-center justify-center text-white font-bold">
              测试
            </div>
          </Animated>
        </div>
      </div>

      {/* 预设模板 */}
      <div className="space-y-3">
        <h3 className="font-semibold">预设模板</h3>
        
        <div className="grid gap-2">
          <Button
            variant="outline"
            onClick={() => onConfigChange({
              enabled: true,
              reducedMotion: false,
              defaultDuration: 300,
              hoverEffects: true,
              clickEffects: true,
              focusEffects: true
            })}
          >
            标准
          </Button>
          
          <Button
            variant="outline"
            onClick={() => onConfigChange({
              enabled: true,
              reducedMotion: true,
              defaultDuration: 200,
              hoverEffects: true,
              clickEffects: false,
              focusEffects: true
            })}
          >
            简约
          </Button>
          
          <Button
            variant="outline"
            onClick={() => onConfigChange({
              enabled: true,
              reducedMotion: false,
              defaultDuration: 500,
              hoverEffects: true,
              clickEffects: true,
              focusEffects: true,
              enableGPU: true
            })}
          >
            丰富
          </Button>
        </div>
      </div>
    </Card>
  )
}

/**
 * 微交互提供者组件
 */
export const MicroInteractionProvider: React.FC<{
  children: React.ReactNode
  config?: Partial<MicroInteractionConfig>
}> = ({ children, config = {} }) => {
  const [microConfig, setMicroConfig] = useState<MicroInteractionConfig>({
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
    showControls: false,
    announceAnimations: false,
    ...config
  })

  const microInteractions = useMicroInteractions(microConfig)

  // 添加全局样式
  useEffect(() => {
    const style = document.createElement('style')
    style.textContent = `
      .interactive-feedback {
        transition: all var(--animation-duration, 300ms) var(--animation-easing, ease-out);
      }
      
      .feedback-hover:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }
      
      .feedback-click:active {
        transform: scale(0.98);
      }
      
      .feedback-focus:focus {
        outline: none;
        box-shadow: 0 0 0 2px var(--primary);
      }
      
      .feedback-subtle {
        transition-duration: 200ms;
      }
      
      .feedback-strong {
        transition-duration: 500ms;
      }
      
      @keyframes ripple {
        to {
          transform: scale(4);
          opacity: 0;
        }
      }
      
      .ripple-effect {
        animation: ripple 0.6s ease-out;
      }
      
      ${microConfig.reducedMotion ? `
        *, *::before, *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
        }
      ` : ''}
    `
    
    document.head.appendChild(style)
    
    return () => {
      document.head.removeChild(style)
    }
  }, [microConfig.reducedMotion])

  return (
    <div className={cn(
      "micro-interaction-provider",
      !microConfig.enabled && "animations-disabled",
      microConfig.reducedMotion && "reduced-motion"
    )}>
      {children}
    </div>
  )
}
