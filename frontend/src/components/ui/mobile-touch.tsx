import React, { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { 
  Touch, 
  Smartphone, 
  Tablet, 
  Monitor, 
  Hand, 
  SwipeLeft, 
  SwipeRight, 
  SwipeUp, 
  SwipeDown,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Move,
  Tap,
  Pinch,
  Pan
} from 'lucide-react'

/**
 * 触摸手势类型
 */
export type TouchGesture = 
  | 'tap'
  | 'double-tap'
  | 'long-press'
  | 'swipe-left'
  | 'swipe-right'
  | 'swipe-up'
  | 'swipe-down'
  | 'pinch-in'
  | 'pinch-out'
  | 'rotate'
  | 'pan'

/**
 * 设备类型
 */
export type DeviceType = 'mobile' | 'tablet' | 'desktop'

/**
 * 触摸配置
 */
export interface TouchConfig {
  // 基础设置
  enabled: boolean
  preventDefault: boolean
  stopPropagation: boolean
  
  // 手势识别
  tapThreshold: number // 点击阈值时间 (ms)
  doubleTapThreshold: number // 双击间隔 (ms)
  longPressThreshold: number // 长按阈值时间 (ms)
  swipeThreshold: number // 滑动阈值距离 (px)
  pinchThreshold: number // 缩放阈值距离 (px)
  rotateThreshold: number // 旋转阈值角度 (deg)
  
  // 反馈设置
  hapticFeedback: boolean
  visualFeedback: boolean
  soundFeedback: boolean
  
  // 性能设置
  throttleMs: number
  debounceMs: number
  
  // 可访问性
  reducedMotion: boolean
  largeTouchTargets: boolean
  highContrast: boolean
}

/**
 * 触摸点信息
 */
export interface TouchPoint {
  id: number
  x: number
  y: number
  startTime: number
  startX: number
  startY: number
}

/**
 * 手势事件数据
 */
export interface GestureEventData {
  type: TouchGesture
  touchPoints: TouchPoint[]
  center: { x: number; y: number }
  distance: number
  angle: number
  velocity: { x: number; y: number }
  duration: number
  target: HTMLElement
}

/**
 * 设备检测Hook
 */
export const useDeviceDetection = () => {
  const [deviceType, setDeviceType] = useState<DeviceType>('desktop')
  const [isTouchDevice, setIsTouchDevice] = useState(false)
  const [screenSize, setScreenSize] = useState({ width: 0, height: 0 })

  useEffect(() => {
    const updateDeviceInfo = () => {
      const width = window.innerWidth
      const height = window.innerHeight
      
      setScreenSize({ width, height })
      
      // 检测设备类型
      if (width <= 768) {
        setDeviceType('mobile')
      } else if (width <= 1024) {
        setDeviceType('tablet')
      } else {
        setDeviceType('desktop')
      }
      
      // 检测触摸支持
      setIsTouchDevice('ontouchstart' in window || navigator.maxTouchPoints > 0)
    }

    updateDeviceInfo()
    
    window.addEventListener('resize', updateDeviceInfo)
    window.addEventListener('orientationchange', updateDeviceInfo)
    
    return () => {
      window.removeEventListener('resize', updateDeviceInfo)
      window.removeEventListener('orientationchange', updateDeviceInfo)
    }
  }, [])

  return {
    deviceType,
    isTouchDevice,
    screenSize,
    isMobile: deviceType === 'mobile',
    isTablet: deviceType === 'tablet',
    isDesktop: deviceType === 'desktop'
  }
}

/**
 * 触摸手势识别Hook
 */
export const useTouchGestures = (
  elementRef: React.RefObject<HTMLElement>,
  config: TouchConfig,
  onGesture: (event: GestureEventData) => void
) => {
  const touchPointsRef = useRef<Map<number, TouchPoint>>(new Map())
  const gestureTimeoutRef = useRef<NodeJS.Timeout>()
  const lastTapRef = useRef<number>(0)

  const getTouchPoint = useCallback((touch: Touch): TouchPoint => {
    return {
      id: touch.identifier,
      x: touch.clientX,
      y: touch.clientY,
      startTime: Date.now(),
      startX: touch.clientX,
      startY: touch.clientY
    }
  }, [])

  const calculateGestureData = useCallback((): GestureEventData => {
    const touchPoints = Array.from(touchPointsRef.current.values())
    const center = touchPoints.reduce(
      (acc, point) => ({
        x: acc.x + point.x / touchPoints.length,
        y: acc.y + point.y / touchPoints.length
      }),
      { x: 0, y: 0 }
    )

    // 计算距离（用于缩放）
    let distance = 0
    if (touchPoints.length >= 2) {
      const p1 = touchPoints[0]
      const p2 = touchPoints[1]
      distance = Math.sqrt(
        Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2)
      )
    }

    // 计算角度（用于旋转）
    let angle = 0
    if (touchPoints.length >= 2) {
      const p1 = touchPoints[0]
      const p2 = touchPoints[1]
      angle = Math.atan2(p2.y - p1.y, p2.x - p1.x) * (180 / Math.PI)
    }

    // 计算速度
    const velocity = touchPoints.reduce(
      (acc, point) => ({
        x: acc.x + (point.x - point.startX) / (Date.now() - point.startTime),
        y: acc.y + (point.y - point.startY) / (Date.now() - point.startTime)
      }),
      { x: 0, y: 0 }
    )

    const duration = Date.now() - (touchPoints[0]?.startTime || 0)

    return {
      type: 'tap' as TouchGesture, // 将根据具体手势更新
      touchPoints,
      center,
      distance,
      angle,
      velocity,
      duration,
      target: elementRef.current!
    }
  }, [elementRef])

  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (!config.enabled) return

    for (let i = 0; i < e.changedTouches.length; i++) {
      const touch = e.changedTouches[i]
      touchPointsRef.current.set(touch.identifier, getTouchPoint(touch))
    }

    if (config.preventDefault) e.preventDefault()
    if (config.stopPropagation) e.stopPropagation()
  }, [config.enabled, config.preventDefault, config.stopPropagation, getTouchPoint])

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!config.enabled) return

    for (let i = 0; i < e.changedTouches.length; i++) {
      const touch = e.changedTouches[i]
      const point = touchPointsRef.current.get(touch.identifier)
      if (point) {
        point.x = touch.clientX
        point.y = touch.clientY
      }
    }

    if (config.preventDefault) e.preventDefault()
    if (config.stopPropagation) e.stopPropagation()
  }, [config.enabled, config.preventDefault, config.stopPropagation])

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    if (!config.enabled) return

    const gestureData = calculateGestureData()
    const currentTime = Date.now()
    
    // 检测点击
    if (gestureData.touchPoints.length === 1 && gestureData.duration < config.tapThreshold) {
      const deltaX = Math.abs(gestureData.touchPoints[0].x - gestureData.touchPoints[0].startX)
      const deltaY = Math.abs(gestureData.touchPoints[0].y - gestureData.touchPoints[0].startY)
      
      if (deltaX < 10 && deltaY < 10) {
        // 检测双击
        if (currentTime - lastTapRef.current < config.doubleTapThreshold) {
          gestureData.type = 'double-tap'
          lastTapRef.current = 0
        } else {
          gestureData.type = 'tap'
          lastTapRef.current = currentTime
        }
        
        onGesture(gestureData)
      }
    }

    // 检测长按
    if (gestureData.duration >= config.longPressThreshold) {
      gestureData.type = 'long-press'
      onGesture(gestureData)
    }

    // 检测滑动
    if (gestureData.touchPoints.length === 1 && gestureData.duration < 500) {
      const deltaX = gestureData.touchPoints[0].x - gestureData.touchPoints[0].startX
      const deltaY = gestureData.touchPoints[0].y - gestureData.touchPoints[0].startY
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
      
      if (distance >= config.swipeThreshold) {
        const angle = Math.atan2(deltaY, deltaX) * (180 / Math.PI)
        
        if (angle >= -45 && angle <= 45) {
          gestureData.type = 'swipe-right'
        } else if (angle > 45 && angle <= 135) {
          gestureData.type = 'swipe-down'
        } else if (angle > 135 || angle <= -135) {
          gestureData.type = 'swipe-left'
        } else {
          gestureData.type = 'swipe-up'
        }
        
        onGesture(gestureData)
      }
    }

    // 检测缩放
    if (gestureData.touchPoints.length >= 2) {
      const initialDistance = Math.sqrt(
        Math.pow(gestureData.touchPoints[1].startX - gestureData.touchPoints[0].startX, 2) +
        Math.pow(gestureData.touchPoints[1].startY - gestureData.touchPoints[0].startY, 2)
      )
      
      if (Math.abs(gestureData.distance - initialDistance) >= config.pinchThreshold) {
        gestureData.type = gestureData.distance > initialDistance ? 'pinch-out' : 'pinch-in'
        onGesture(gestureData)
      }
    }

    for (let i = 0; i < e.changedTouches.length; i++) {
      touchPointsRef.current.delete(e.changedTouches[i].identifier)
    }

    if (config.preventDefault) e.preventDefault()
    if (config.stopPropagation) e.stopPropagation()
  }, [config, calculateGestureData, onGesture])

  useEffect(() => {
    const element = elementRef.current
    if (!element || !config.enabled) return

    element.addEventListener('touchstart', handleTouchStart, { passive: false })
    element.addEventListener('touchmove', handleTouchMove, { passive: false })
    element.addEventListener('touchend', handleTouchEnd, { passive: false })

    return () => {
      element.removeEventListener('touchstart', handleTouchStart)
      element.removeEventListener('touchmove', handleTouchMove)
      element.removeEventListener('touchend', handleTouchEnd)
    }
  }, [elementRef, config.enabled, handleTouchStart, handleTouchMove, handleTouchEnd])

  return {
    touchPoints: Array.from(touchPointsRef.current.values())
  }
}

/**
 * 触摸反馈Hook
 */
export const useTouchFeedback = (config: TouchConfig) => {
  const triggerFeedback = useCallback((type: 'tap' | 'long-press' | 'swipe') => {
    if (!config.enabled) return

    // 触觉反馈
    if (config.hapticFeedback && 'vibrate' in navigator) {
      switch (type) {
        case 'tap':
          navigator.vibrate(10)
          break
        case 'long-press':
          navigator.vibrate(50)
          break
        case 'swipe':
          navigator.vibrate(20)
          break
      }
    }

    // 视觉反馈
    if (config.visualFeedback) {
      document.body.classList.add('touch-feedback')
      setTimeout(() => {
        document.body.classList.remove('touch-feedback')
      }, 200)
    }

    // 声音反馈
    if (config.soundFeedback) {
      // 这里可以播放声音文件
      const audio = new Audio('/touch-sound.mp3')
      audio.volume = 0.3
      audio.play().catch(() => {
        // 忽略播放失败
      })
    }
  }, [config])

  return { triggerFeedback }
}

/**
 * 触摸优化组件
 */
export const TouchOptimized: React.FC<{
  children: React.ReactNode
  config?: Partial<TouchConfig>
  onGesture?: (event: GestureEventData) => void
  className?: string
}> = ({ 
  children, 
  config = {}, 
  onGesture = () => {},
  className 
}) => {
  const elementRef = useRef<HTMLDivElement>(null)
  const device = useDeviceDetection()
  
  const [touchConfig] = useState<TouchConfig>({
    enabled: device.isTouchDevice,
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
    reducedMotion: false,
    largeTouchTargets: device.isMobile,
    highContrast: false,
    ...config
  })

  const feedback = useTouchFeedback(touchConfig)
  
  useTouchGestures(elementRef, touchConfig, (event) => {
    feedback.triggerFeedback(event.type)
    onGesture(event)
  })

  return (
    <div
      ref={elementRef}
      className={cn(
        "touch-optimized",
        touchConfig.largeTouchTargets && "large-touch-targets",
        touchConfig.highContrast && "high-contrast",
        className
      )}
      style={{
        // 确保触摸目标足够大
        ...(touchConfig.largeTouchTargets && {
          '--touch-target-size': '44px',
          '--touch-target-spacing': '8px'
        } as React.CSSProperties)
      }}
    >
      {children}
    </div>
  )
}

/**
 * 手势演示组件
 */
export const GestureDemo: React.FC<{
  onGesture: (gesture: TouchGesture) => void
  className?: string
}> = ({ onGesture, className }) => {
  const [activeGesture, setActiveGesture] = useState<TouchGesture | null>(null)
  const [touchPoints, setTouchPoints] = useState<TouchPoint[]>([])

  const handleGesture = useCallback((event: GestureEventData) => {
    setActiveGesture(event.type)
    onGesture(event.type)
    
    // 重置状态
    setTimeout(() => setActiveGesture(null), 500)
  }, [onGesture])

  const config: TouchConfig = {
    enabled: true,
    preventDefault: true,
    stopPropagation: true,
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
  }

  const getGestureIcon = (gesture: TouchGesture) => {
    switch (gesture) {
      case 'tap': return <Tap className="w-6 h-6" />
      case 'double-tap': return <Tap className="w-6 h-6" />
      case 'long-press': return <Hand className="w-6 h-6" />
      case 'swipe-left': return <SwipeLeft className="w-6 h-6" />
      case 'swipe-right': return <SwipeRight className="w-6 h-6" />
      case 'swipe-up': return <SwipeUp className="w-6 h-6" />
      case 'swipe-down': return <SwipeDown className="w-6 h-6" />
      case 'pinch-in': return <ZoomOut className="w-6 h-6" />
      case 'pinch-out': return <ZoomIn className="w-6 h-6" />
      case 'rotate': return <RotateCw className="w-6 h-6" />
      case 'pan': return <Pan className="w-6 h-6" />
      default: return <Touch className="w-6 h-6" />
    }
  }

  return (
    <TouchOptimized config={config} onGesture={handleGesture}>
      <Card className={cn(
        "p-8 text-center cursor-pointer select-none transition-all duration-200",
        activeGesture && "scale-95 bg-primary/10",
        className
      )}>
        <div className="space-y-4">
          <div className="flex justify-center">
            {activeGesture ? getGestureIcon(activeGesture) : <Touch className="w-12 h-12 text-muted-foreground" />}
          </div>
          
          <div>
            <h3 className="text-lg font-semibold">
              {activeGesture ? `检测到: ${activeGesture}` : '触摸手势演示'}
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              尝试点击、双击、长按、滑动或缩放
            </p>
          </div>

          {/* 触摸点可视化 */}
          {touchPoints.length > 0 && (
            <div className="relative h-32 bg-muted rounded">
              {touchPoints.map((point, index) => (
                <div
                  key={point.id}
                  className="absolute w-4 h-4 bg-primary rounded-full transform -translate-x-1/2 -translate-y-1/2"
                  style={{
                    left: `${(point.x / window.innerWidth) * 100}%`,
                    top: `${(point.y / 200) * 100}%`
                  }}
                >
                  <div className="absolute inset-0 bg-primary rounded-full animate-ping" />
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </TouchOptimized>
  )
}

/**
 * 移动端优化面板
 */
export const MobileOptimizationPanel: React.FC<{
  config: TouchConfig
  onConfigChange: (updates: Partial<TouchConfig>) => void
  device: ReturnType<typeof useDeviceDetection>
  className?: string
}> = ({ config, onConfigChange, device, className }) => {
  const [testResults, setTestResults] = useState<string[]>([])

  const runTouchTests = useCallback(() => {
    const results: string[] = []
    
    // 测试触摸支持
    if (device.isTouchDevice) {
      results.push('✓ 触摸支持正常')
    } else {
      results.push('✗ 未检测到触摸支持')
    }
    
    // 测试触摸目标大小
    const buttons = document.querySelectorAll('button, a, input, [role="button"]')
    let smallTargets = 0
    
    buttons.forEach(button => {
      const rect = button.getBoundingClientRect()
      if (rect.width < 44 || rect.height < 44) {
        smallTargets++
      }
    })
    
    if (smallTargets === 0) {
      results.push('✓ 所有触摸目标大小符合标准')
    } else {
      results.push(`⚠ 发现 ${smallTargets} 个过小的触摸目标`)
    }
    
    // 测试间距
    let closeTargets = 0
    for (let i = 0; i < buttons.length - 1; i++) {
      const rect1 = buttons[i].getBoundingClientRect()
      const rect2 = buttons[i + 1].getBoundingClientRect()
      
      const distance = Math.sqrt(
        Math.pow(rect2.left - rect1.right, 2) + 
        Math.pow(rect2.top - rect1.top, 2)
      )
      
      if (distance < 8) {
        closeTargets++
      }
    }
    
    if (closeTargets === 0) {
      results.push('✓ 触摸目标间距符合标准')
    } else {
      results.push(`⚠ 发现 ${closeTargets} 个间距过小的触摸目标`)
    }
    
    setTestResults(results)
  }, [device])

  return (
    <Card className={cn("p-6 space-y-6", className)}>
      {/* 头部 */}
      <div className="flex items-center gap-3">
        <Smartphone className="w-6 h-6 text-primary" />
        <h2 className="text-xl font-semibold">移动端优化</h2>
      </div>

      {/* 设备信息 */}
      <div className="p-4 bg-muted rounded-lg">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">设备类型:</span>
            <div className="flex items-center gap-2 mt-1">
              {device.deviceType === 'mobile' && <Smartphone className="w-4 h-4" />}
              {device.deviceType === 'tablet' && <Tablet className="w-4 h-4" />}
              {device.deviceType === 'desktop' && <Monitor className="w-4 h-4" />}
              <span>{device.deviceType}</span>
            </div>
          </div>
          <div>
            <span className="font-medium">触摸支持:</span>
            <div className="mt-1">
              {device.isTouchDevice ? '✓ 支持' : '✗ 不支持'}
            </div>
          </div>
          <div>
            <span className="font-medium">屏幕尺寸:</span>
            <div className="mt-1">
              {device.screenSize.width} × {device.screenSize.height}
            </div>
          </div>
          <div>
            <span className="font-medium">像素密度:</span>
            <div className="mt-1">
              {window.devicePixelRatio || 1}x
            </div>
          </div>
        </div>
      </div>

      {/* 触摸配置 */}
      <div className="space-y-4">
        <h3 className="font-semibold">触摸配置</h3>
        
        <div className="grid gap-3">
          <label className="flex items-center justify-between">
            <span>启用触摸优化</span>
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => onConfigChange({ enabled: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>触觉反馈</span>
            <input
              type="checkbox"
              checked={config.hapticFeedback}
              onChange={(e) => onConfigChange({ hapticFeedback: e.target.checked })}
              className="w-4 h-4"
              disabled={!device.isMobile}
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>视觉反馈</span>
            <input
              type="checkbox"
              checked={config.visualFeedback}
              onChange={(e) => onConfigChange({ visualFeedback: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>大触摸目标</span>
            <input
              type="checkbox"
              checked={config.largeTouchTargets}
              onChange={(e) => onConfigChange({ largeTouchTargets: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>高对比度</span>
            <input
              type="checkbox"
              checked={config.highContrast}
              onChange={(e) => onConfigChange({ highContrast: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
        </div>
      </div>

      {/* 手势阈值设置 */}
      <div className="space-y-4">
        <h3 className="font-semibold">手势阈值</h3>
        
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">
              点击阈值: {config.tapThreshold}ms
            </label>
            <input
              type="range"
              min="100"
              max="500"
              value={config.tapThreshold}
              onChange={(e) => onConfigChange({ tapThreshold: parseInt(e.target.value) })}
              className="w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">
              长按阈值: {config.longPressThreshold}ms
            </label>
            <input
              type="range"
              min="300"
              max="1000"
              value={config.longPressThreshold}
              onChange={(e) => onConfigChange({ longPressThreshold: parseInt(e.target.value) })}
              className="w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">
              滑动阈值: {config.swipeThreshold}px
            </label>
            <input
              type="range"
              min="20"
              max="100"
              value={config.swipeThreshold}
              onChange={(e) => onConfigChange({ swipeThreshold: parseInt(e.target.value) })}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* 测试工具 */}
      <div className="space-y-4">
        <h3 className="font-semibold">测试工具</h3>
        
        <Button onClick={runTouchTests} className="w-full">
          运行触摸测试
        </Button>
        
        {testResults.length > 0 && (
          <div className="p-3 bg-muted rounded text-sm space-y-1">
            {testResults.map((result, index) => (
              <div key={index}>{result}</div>
            ))}
          </div>
        )}
      </div>

      {/* 手势演示 */}
      {device.isTouchDevice && (
        <div className="space-y-4">
          <h3 className="font-semibold">手势演示</h3>
          <GestureDemo onGesture={(gesture) => console.log('Gesture:', gesture)} />
        </div>
      )}
    </Card>
  )
}
