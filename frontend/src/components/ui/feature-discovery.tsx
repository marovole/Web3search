import React, { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { 
  Compass, 
  Target, 
  Zap, 
  Star, 
  Award,
  TrendingUp,
  Eye,
  Play,
  Check,
  Lock,
  Unlock,
  ArrowRight,
  Lightbulb,
  BookOpen,
  Video
} from 'lucide-react'

/**
 * 功能发现状态
 */
export interface FeatureDiscoveryState {
  discovered: Set<string>
  inProgress: Set<string>
  completed: Set<string>
  favorites: Set<string>
  lastVisited: Record<string, number>
}

/**
 * 功能项接口
 */
export interface FeatureItem {
  id: string
  name: string
  description: string
  category: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  estimatedTime: number // 分钟
  prerequisites?: string[]
  rewards?: {
    points: number
    badge?: string
  }
  content: {
    steps: Array<{
      title: string
      description: string
      action?: () => void
      target?: string // CSS选择器
    }>
    resources?: Array<{
      type: 'article' | 'video' | 'tutorial'
      title: string
      url: string
    }>
  }
  metadata?: {
    tags: string[]
    popularity: number
    rating: number
  }
}

/**
 * 功能发现Hook
 */
export const useFeatureDiscovery = (features: FeatureItem[]) => {
  const [state, setState] = useState<FeatureDiscoveryState>({
    discovered: new Set(),
    inProgress: new Set(),
    completed: new Set(),
    favorites: new Set(),
    lastVisited: {}
  })
  const [currentFeature, setCurrentFeature] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState(0)

  // 从存储中恢复状态
  useEffect(() => {
    try {
      const saved = localStorage.getItem('feature_discovery_state')
      if (saved) {
        const data = JSON.parse(saved)
        setState({
          discovered: new Set(data.discovered || []),
          inProgress: new Set(data.inProgress || []),
          completed: new Set(data.completed || []),
          favorites: new Set(data.favorites || []),
          lastVisited: data.lastVisited || {}
        })
      }
    } catch (error) {
      console.warn('Failed to restore feature discovery state:', error)
    }
  }, [])

  // 保存状态到存储
  const saveState = useCallback((newState: FeatureDiscoveryState) => {
    try {
      localStorage.setItem('feature_discovery_state', JSON.stringify({
        discovered: Array.from(newState.discovered),
        inProgress: Array.from(newState.inProgress),
        completed: Array.from(newState.completed),
        favorites: Array.from(newState.favorites),
        lastVisited: newState.lastVisited
      }))
    } catch (error) {
      console.warn('Failed to save feature discovery state:', error)
    }
  }, [])

  const startDiscovery = useCallback((featureId: string) => {
    setState(prev => {
      const newState = {
        ...prev,
        discovered: new Set(prev.discovered).add(featureId),
        inProgress: new Set(prev.inProgress).add(featureId),
        lastVisited: {
          ...prev.lastVisited,
          [featureId]: Date.now()
        }
      }
      saveState(newState)
      return newState
    })
    setCurrentFeature(featureId)
    setCurrentStep(0)
  }, [saveState])

  const completeStep = useCallback((featureId: string, stepIndex: number) => {
    const feature = features.find(f => f.id === featureId)
    if (!feature) return

    if (stepIndex >= feature.content.steps.length - 1) {
      // 完成整个功能
      setState(prev => {
        const newState = {
          ...prev,
          inProgress: new Set(prev.inProgress).delete(featureId) && prev.inProgress,
          completed: new Set(prev.completed).add(featureId)
        }
        saveState(newState)
        return newState
      })
      setCurrentFeature(null)
      setCurrentStep(0)
    } else {
      // 进入下一步
      setCurrentStep(stepIndex + 1)
    }
  }, [features, saveState])

  const skipDiscovery = useCallback((featureId: string) => {
    setState(prev => {
      const newState = {
        ...prev,
        inProgress: new Set(prev.inProgress).delete(featureId) && prev.inProgress
      }
      saveState(newState)
      return newState
    })
    setCurrentFeature(null)
    setCurrentStep(0)
  }, [saveState])

  const toggleFavorite = useCallback((featureId: string) => {
    setState(prev => {
      const favorites = new Set(prev.favorites)
      if (favorites.has(featureId)) {
        favorites.delete(featureId)
      } else {
        favorites.add(featureId)
      }
      const newState = { ...prev, favorites }
      saveState(newState)
      return newState
    })
  }, [saveState])

  const getProgress = useCallback(() => {
    const totalFeatures = features.length
    const completedCount = state.completed.size
    return totalFeatures > 0 ? (completedCount / totalFeatures) * 100 : 0
  }, [features.length, state.completed.size])

  const getRecommendedFeatures = useCallback((limit: number = 3) => {
    // 基于用户进度和功能受欢迎程度推荐
    const undiscovered = features.filter(f => !state.discovered.has(f.id))
    const inProgress = features.filter(f => state.inProgress.has(f.id))
    
    // 优先推荐进行中的功能
    const recommended = [
      ...inProgress.sort((a, b) => (b.metadata?.popularity || 0) - (a.metadata?.popularity || 0)),
      ...undiscovered.filter(f => 
        f.difficulty === 'beginner' && 
        (!f.prerequisites || f.prerequisites.every(p => state.completed.has(p)))
      ).sort((a, b) => (b.metadata?.popularity || 0) - (a.metadata?.popularity || 0))
    ]
    
    return recommended.slice(0, limit)
  }, [features, state])

  return {
    state,
    currentFeature,
    currentStep,
    startDiscovery,
    completeStep,
    skipDiscovery,
    toggleFavorite,
    getProgress,
    getRecommendedFeatures
  }
}

/**
 * 功能卡片组件
 */
export const FeatureCard: React.FC<{
  feature: FeatureItem
  state: FeatureDiscoveryState
  onStart: (featureId: string) => void
  onToggleFavorite: (featureId: string) => void
  className?: string
}> = ({ feature, state, onStart, onToggleFavorite, className }) => {
  const isDiscovered = state.discovered.has(feature.id)
  const isInProgress = state.inProgress.has(feature.id)
  const isCompleted = state.completed.has(feature.id)
  const isFavorite = state.favorites.has(feature.id)

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-700 border-green-200'
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'advanced':
        return 'bg-red-100 text-red-700 border-red-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getStatusIcon = () => {
    if (isCompleted) return <Check className="w-4 h-4 text-green-500" />
    if (isInProgress) return <Play className="w-4 h-4 text-blue-500" />
    if (isDiscovered) return <Eye className="w-4 h-4 text-gray-500" />
    return <Lock className="w-4 h-4 text-gray-400" />
  }

  return (
    <Card className={cn(
      "p-4 space-y-3 hover:shadow-md transition-shadow cursor-pointer",
      isCompleted && "border-green-200 bg-green-50/50",
      isInProgress && "border-blue-200 bg-blue-50/50",
      className
    )}>
      {/* 头部 */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <h3 className="font-semibold text-foreground">{feature.name}</h3>
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onToggleFavorite(feature.id)
          }}
          className="h-8 w-8 p-0"
        >
          <Star className={cn(
            "w-4 h-4",
            isFavorite ? "fill-yellow-400 text-yellow-400" : "text-gray-400"
          )} />
        </Button>
      </div>

      {/* 描述 */}
      <p className="text-sm text-muted-foreground line-clamp-2">
        {feature.description}
      </p>

      {/* 元数据 */}
      <div className="flex items-center gap-2 text-xs">
        <span className={cn(
          "px-2 py-1 rounded border",
          getDifficultyColor(feature.difficulty)
        )}>
          {feature.difficulty === 'beginner' && '入门'}
          {feature.difficulty === 'intermediate' && '进阶'}
          {feature.difficulty === 'advanced' && '高级'}
        </span>
        
        <span className="text-muted-foreground">
          {feature.estimatedTime} 分钟
        </span>
        
        {feature.rewards && (
          <span className="flex items-center gap-1 text-yellow-600">
            <Award className="w-3 h-3" />
            {feature.rewards.points} 积分
          </span>
        )}
      </div>

      {/* 标签 */}
      {feature.metadata?.tags && feature.metadata.tags.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {feature.metadata.tags.slice(0, 3).map(tag => (
            <span
              key={tag}
              className="text-xs px-2 py-1 bg-primary/10 text-primary rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex gap-2">
        {isCompleted ? (
          <Button variant="outline" size="sm" className="flex-1">
            <Check className="w-4 h-4 mr-2" />
            已完成
          </Button>
        ) : isInProgress ? (
          <Button size="sm" className="flex-1">
            <Play className="w-4 h-4 mr-2" />
            继续学习
          </Button>
        ) : (
          <Button 
            size="sm" 
            className="flex-1"
            onClick={() => onStart(feature.id)}
          >
            <Unlock className="w-4 h-4 mr-2" />
            开始学习
          </Button>
        )}
      </div>
    </Card>
  )
}

/**
 * 功能发现向导组件
 */
export const FeatureDiscoveryWizard: React.FC<{
  feature: FeatureItem
  currentStep: number
  onComplete: (stepIndex: number) => void
  onSkip: () => void
  className?: string
}> = ({ feature, currentStep, onComplete, onSkip, className }) => {
  const step = feature.content.steps[currentStep]
  const isLastStep = currentStep === feature.content.steps.length - 1

  useEffect(() => {
    // 高亮目标元素
    if (step.target) {
      const element = document.querySelector(step.target) as HTMLElement
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        element.classList.add('ring-2', 'ring-primary', 'ring-offset-2')
        
        return () => {
          element.classList.remove('ring-2', 'ring-primary', 'ring-offset-2')
        }
      }
    }
  }, [step.target])

  return (
    <Card className={cn(
      "fixed bottom-4 right-4 z-50 w-96 p-6 shadow-xl",
      className
    )}>
      {/* 进度 */}
      <div className="mb-4">
        <div className="flex justify-between items-center text-sm text-muted-foreground mb-2">
          <span>步骤 {currentStep + 1} / {feature.content.steps.length}</span>
          <span>{feature.name}</span>
        </div>
        <Progress value={((currentStep + 1) / feature.content.steps.length) * 100} />
      </div>

      {/* 内容 */}
      <div className="space-y-4">
        <div>
          <h3 className="font-semibold text-foreground mb-2">
            {step.title}
          </h3>
          <p className="text-sm text-muted-foreground">
            {step.description}
          </p>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2">
          <Button variant="outline" onClick={onSkip}>
            跳过
          </Button>
          
          {step.action ? (
            <Button onClick={step.action} className="flex-1">
              执行操作
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={() => onComplete(currentStep)} className="flex-1">
              {isLastStep ? '完成' : '下一步'}
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>

        {/* 资源链接 */}
        {feature.content.resources && feature.content.resources.length > 0 && (
          <div className="border-t pt-4">
            <p className="text-sm font-medium text-foreground mb-2">相关资源</p>
            <div className="space-y-2">
              {feature.content.resources.map((resource, index) => (
                <a
                  key={index}
                  href={resource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-primary hover:underline"
                >
                  {resource.type === 'video' && <Video className="w-4 h-4" />}
                  {resource.type === 'article' && <BookOpen className="w-4 h-4" />}
                  {resource.type === 'tutorial' && <Lightbulb className="w-4 h-4" />}
                  {resource.title}
                  <ExternalLink className="w-3 h-3" />
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

/**
 * 功能发现中心组件
 */
export const FeatureDiscoveryCenter: React.FC<{
  features: FeatureItem[]
  className?: string
}> = ({ features, className }) => {
  const discovery = useFeatureDiscovery(features)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  const categories = Array.from(new Set(features.map(f => f.category)))
  
  const filteredFeatures = features.filter(feature => {
    if (selectedCategory === 'all') return true
    return feature.category === selectedCategory
  })

  const stats = {
    total: features.length,
    discovered: discovery.state.discovered.size,
    inProgress: discovery.state.inProgress.size,
    completed: discovery.state.completed.size,
    points: features
      .filter(f => discovery.state.completed.has(f.id))
      .reduce((sum, f) => sum + (f.rewards?.points || 0), 0)
  }

  return (
    <div className={cn("w-full max-w-6xl mx-auto space-y-6", className)}>
      {/* 统计概览 */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <Compass className="w-6 h-6 text-primary" />
          <h2 className="text-xl font-semibold">功能发现中心</h2>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary">{stats.total}</div>
            <div className="text-sm text-muted-foreground">总功能数</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.discovered}</div>
            <div className="text-sm text-muted-foreground">已发现</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
            <div className="text-sm text-muted-foreground">已完成</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{stats.points}</div>
            <div className="text-sm text-muted-foreground">获得积分</div>
          </div>
        </div>

        {/* 总进度 */}
        <div className="mt-4">
          <div className="flex justify-between items-center text-sm mb-2">
            <span>学习进度</span>
            <span>{Math.round(discovery.getProgress())}%</span>
          </div>
          <Progress value={discovery.getProgress()} />
        </div>
      </Card>

      {/* 推荐功能 */}
      {discovery.getRecommendedFeatures().length > 0 && (
        <Card className="p-6">
          <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            推荐学习
          </h3>
          <div className="grid gap-4 md:grid-cols-3">
            {discovery.getRecommendedFeatures().map(feature => (
              <FeatureCard
                key={feature.id}
                feature={feature}
                state={discovery.state}
                onStart={discovery.startDiscovery}
                onToggleFavorite={discovery.toggleFavorite}
              />
            ))}
          </div>
        </Card>
      )}

      {/* 筛选和视图 */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex gap-2">
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

        <div className="flex gap-2">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('grid')}
          >
            网格
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('list')}
          >
            列表
          </Button>
        </div>
      </div>

      {/* 功能列表 */}
      <div className={cn(
        viewMode === 'grid' ? "grid gap-4 md:grid-cols-2 lg:grid-cols-3" : "space-y-4"
      )}>
        {filteredFeatures.map(feature => (
          <FeatureCard
            key={feature.id}
            feature={feature}
            state={discovery.state}
            onStart={discovery.startDiscovery}
            onToggleFavorite={discovery.toggleFavorite}
          />
        ))}
      </div>

      {/* 当前进行中的功能向导 */}
      {discovery.currentFeature && (
        <FeatureDiscoveryWizard
          feature={features.find(f => f.id === discovery.currentFeature)!}
          currentStep={discovery.currentStep}
          onComplete={discovery.completeStep}
          onSkip={() => discovery.skipDiscovery(discovery.currentFeature!)}
        />
      )}
    </div>
  )
}

/**
 * 功能发现提示组件
 */
export const FeatureDiscoveryTip: React.FC<{
  feature: FeatureItem
  onAccept: () => void
  onDismiss: () => void
  className?: string
}> = ({ feature, onAccept, onDismiss, className }) => {
  return (
    <Card className={cn(
      "fixed top-4 right-4 z-40 w-80 p-4 shadow-lg animate-slide-in",
      className
    )}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 text-blue-500">
          <Target className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-foreground text-sm mb-1">
            发现新功能
          </h4>
          <p className="text-xs text-muted-foreground mb-2">
            {feature.name} - {feature.description}
          </p>
          <div className="flex gap-2">
            <Button size="sm" onClick={onAccept}>
              立即学习
            </Button>
            <Button variant="ghost" size="sm" onClick={onDismiss}>
              稍后
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
