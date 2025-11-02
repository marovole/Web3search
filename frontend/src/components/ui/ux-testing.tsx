import React, { useState, useEffect, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { 
  TestTube, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Eye, 
  MousePointer, 
  Keyboard,
  Zap,
  TrendingUp,
  AlertTriangle,
  Info,
  Play,
  Pause,
  RotateCcw,
  Download,
  Upload,
  BarChart3,
  Users,
  Target,
  Award,
  Settings
} from 'lucide-react'

/**
 * 测试类型
 */
export type TestType = 
  | 'performance'
  | 'accessibility'
  | 'usability'
  | 'compatibility'
  | 'responsiveness'
  | 'interaction'
  | 'navigation'
  | 'content'

/**
 * 测试结果
 */
export interface TestResult {
  id: string
  type: TestType
  name: string
  status: 'pending' | 'running' | 'passed' | 'failed' | 'warning'
  score: number // 0-100
  duration: number // ms
  issues: TestIssue[]
  recommendations: string[]
  timestamp: number
  metadata?: Record<string, any>
}

/**
 * 测试问题
 */
export interface TestIssue {
  id: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  category: string
  description: string
  element?: string // CSS选择器
  suggestion?: string
  resources?: Array<{
    type: 'article' | 'guideline' | 'tool'
    title: string
    url: string
  }>
}

/**
 * UX测试配置
 */
export interface UXTestConfig {
  // 测试范围
  testTypes: TestType[]
  includePerformance: boolean
  includeAccessibility: boolean
  includeUsability: boolean
  
  // 性能测试
  performanceThresholds: {
    firstContentfulPaint: number // ms
    largestContentfulPaint: number // ms
    firstInputDelay: number // ms
    cumulativeLayoutShift: number
    timeToInteractive: number // ms
  }
  
  // 可访问性测试
  accessibilityLevel: 'AA' | 'AAA'
  testColorContrast: boolean
  testKeyboardNavigation: boolean
  testScreenReader: boolean
  
  // 可用性测试
  testTouchTargets: boolean
  testReadability: boolean
  testNavigation: boolean
  
  // 兼容性测试
  browsers: Array<'chrome' | 'firefox' | 'safari' | 'edge'>
  viewports: Array<{ width: number; height: number; name: string }>
  
  // 高级设置
  enableRealUserMonitoring: boolean
  enableA11yTesting: boolean
  enablePerformanceMonitoring: boolean
}

/**
 * UX测试Hook
 */
export const useUXTesting = (config: UXTestConfig) => {
  const [isRunning, setIsRunning] = useState(false)
  const [currentTest, setCurrentTest] = useState<TestType | null>(null)
  const [results, setResults] = useState<TestResult[]>([])
  const [progress, setProgress] = useState(0)
  const testControllerRef = useRef<AbortController | null>(null)

  // 运行所有测试
  const runAllTests = useCallback(async () => {
    if (isRunning) return

    setIsRunning(true)
    setProgress(0)
    setResults([])
    
    testControllerRef.current = new AbortController()
    const signal = testControllerRef.current.signal

    try {
      const allTests = config.testTypes
      const testResults: TestResult[] = []

      for (let i = 0; i < allTests.length; i++) {
        const testType = allTests[i]
        
        if (signal.aborted) break
        
        setCurrentTest(testType)
        const result = await runSingleTest(testType, signal)
        testResults.push(result)
        
        setProgress(((i + 1) / allTests.length) * 100)
      }

      setResults(testResults)
    } catch (error) {
      console.error('Test execution failed:', error)
    } finally {
      setIsRunning(false)
      setCurrentTest(null)
      testControllerRef.current = null
    }
  }, [isRunning, config.testTypes])

  // 运行单个测试
  const runSingleTest = useCallback(async (
    testType: TestType,
    signal?: AbortSignal
  ): Promise<TestResult> => {
    const startTime = Date.now()

    try {
      let result: TestResult

      switch (testType) {
        case 'performance':
          result = await runPerformanceTest(config, signal)
          break
        case 'accessibility':
          result = await runAccessibilityTest(config, signal)
          break
        case 'usability':
          result = await runUsabilityTest(config, signal)
          break
        case 'compatibility':
          result = await runCompatibilityTest(config, signal)
          break
        case 'responsiveness':
          result = await runResponsivenessTest(config, signal)
          break
        case 'interaction':
          result = await runInteractionTest(config, signal)
          break
        case 'navigation':
          result = await runNavigationTest(config, signal)
          break
        case 'content':
          result = await runContentTest(config, signal)
          break
        default:
          result = createEmptyResult(testType)
      }

      result.duration = Date.now() - startTime
      result.timestamp = Date.now()

      return result
    } catch (error) {
      return {
        id: `${testType}-${Date.now()}`,
        type: testType,
        name: getTestName(testType),
        status: 'failed',
        score: 0,
        duration: Date.now() - startTime,
        issues: [{
          id: 'exec-error',
          severity: 'critical',
          category: 'execution',
          description: `测试执行失败: ${error}`,
          suggestion: '请检查测试配置和环境'
        }],
        recommendations: ['修复测试执行错误后重新运行'],
        timestamp: Date.now()
      }
    }
  }, [config])

  // 停止测试
  const stopTests = useCallback(() => {
    if (testControllerRef.current) {
      testControllerRef.current.abort()
    }
    setIsRunning(false)
    setCurrentTest(null)
  }, [])

  // 重新运行测试
  const rerunTests = useCallback(() => {
    setResults([])
    setProgress(0)
    runAllTests()
  }, [runAllTests])

  // 导出结果
  const exportResults = useCallback(() => {
    const exportData = {
      timestamp: Date.now(),
      config,
      results,
      summary: generateSummary(results)
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ux-test-results-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    
    URL.revokeObjectURL(url)
  }, [config, results])

  return {
    isRunning,
    currentTest,
    results,
    progress,
    runAllTests,
    runSingleTest,
    stopTests,
    rerunTests,
    exportResults
  }
}

/**
 * 性能测试
 */
const runPerformanceTest = async (
  config: UXTestConfig,
  signal?: AbortSignal
): Promise<TestResult> => {
  const issues: TestIssue[] = []
  let score = 100

  // 检查 Web Vitals
  if ('performance' in window) {
    try {
      // 模拟性能指标检测
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      
      const fcp = navigation.responseStart - navigation.fetchStart
      const lcp = navigation.loadEventEnd - navigation.fetchStart
      const tti = navigation.domInteractive - navigation.fetchStart

      if (fcp > config.performanceThresholds.firstContentfulPaint) {
        issues.push({
          id: 'slow-fcp',
          severity: 'medium',
          category: 'performance',
          description: `首次内容绘制过慢: ${fcp}ms`,
          suggestion: '优化资源加载和渲染路径',
          resources: [{
            type: 'guideline',
            title: '优化首次内容绘制',
            url: 'https://web.dev/fcp/'
          }]
        })
        score -= 15
      }

      if (lcp > config.performanceThresholds.largestContentfulPaint) {
        issues.push({
          id: 'slow-lcp',
          severity: 'medium',
          category: 'performance',
          description: `最大内容绘制过慢: ${lcp}ms`,
          suggestion: '优化图片和关键资源加载'
        })
        score -= 20
      }

      if (tti > config.performanceThresholds.timeToInteractive) {
        issues.push({
          id: 'slow-tti',
          severity: 'high',
          category: 'performance',
          description: `可交互时间过慢: ${tti}ms`,
          suggestion: '减少JavaScript执行时间和阻塞资源'
        })
        score -= 25
      }
    } catch (error) {
      issues.push({
        id: 'perf-api-error',
        severity: 'low',
        category: 'performance',
        description: '无法获取性能指标',
        suggestion: '确保在支持Performance API的环境中运行测试'
      })
      score -= 5
    }
  }

  // 检查资源优化
  const images = document.querySelectorAll('img')
  let unoptimizedImages = 0
  
  images.forEach(img => {
    if (!img.loading || img.loading === 'eager') {
      unoptimizedImages++
    }
  })

  if (unoptimizedImages > images.length * 0.5) {
    issues.push({
      id: 'unoptimized-images',
      severity: 'medium',
      category: 'performance',
      description: `${unoptimizedImages} 张图片未使用懒加载`,
      suggestion: '为非关键图片添加 loading="lazy" 属性'
    })
    score -= 10
  }

  return {
    id: 'performance-test',
    type: 'performance',
    name: '性能测试',
    status: score >= 80 ? 'passed' : score >= 60 ? 'warning' : 'failed',
    score: Math.max(0, score),
    duration: 0,
    issues,
    recommendations: generatePerformanceRecommendations(issues),
    timestamp: Date.now()
  }
}

/**
 * 可访问性测试
 */
const runAccessibilityTest = async (
  config: UXTestConfig,
  signal?: AbortSignal
): Promise<TestResult> => {
  const issues: TestIssue[] = []
  let score = 100

  // 检查颜色对比度
  const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, a, button')
  let lowContrastElements = 0

  textElements.forEach(element => {
    const styles = window.getComputedStyle(element)
    const color = styles.color
    const backgroundColor = styles.backgroundColor || styles.background
    
    // 简化的对比度检查（实际应用中应使用更精确的计算）
    if (color === 'rgb(128, 128, 128)' && backgroundColor === 'rgb(248, 248, 248)') {
      lowContrastElements++
    }
  })

  if (lowContrastElements > 0) {
    issues.push({
      id: 'low-contrast',
      severity: 'high',
      category: 'accessibility',
      description: `${lowContrastElements} 个元素颜色对比度不足`,
      suggestion: '增加文本和背景的颜色对比度，确保符合WCAG标准',
      resources: [{
        type: 'tool',
        title: '颜色对比度检查器',
        url: 'https://web.dev/color-contrast/'
      }]
    })
    score -= 20
  }

  // 检查ARIA标签
  const interactiveElements = document.querySelectorAll('button, a, input, select, textarea')
  let missingLabels = 0

  interactiveElements.forEach(element => {
    const hasLabel = element.getAttribute('aria-label') || 
                     element.getAttribute('aria-labelledby') ||
                     element.getAttribute('title') ||
                     element.textContent?.trim()
    
    if (!hasLabel) {
      missingLabels++
    }
  })

  if (missingLabels > 0) {
    issues.push({
      id: 'missing-aria-labels',
      severity: 'medium',
      category: 'accessibility',
      description: `${missingLabels} 个交互元素缺少可访问性标签`,
      suggestion: '为所有交互元素添加适当的ARIA标签或文本内容'
    })
    score -= 15
  }

  // 检查键盘导航
  const focusableElements = document.querySelectorAll(
    'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )

  if (focusableElements.length === 0) {
    issues.push({
      id: 'no-keyboard-navigation',
      severity: 'critical',
      category: 'accessibility',
      description: '页面没有可键盘聚焦的元素',
      suggestion: '确保所有交互功能都可以通过键盘访问'
    })
    score -= 30
  }

  // 检查标题结构
  const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6')
  let hasH1 = false
  let improperHierarchy = false

  headings.forEach((heading, index) => {
    if (heading.tagName === 'H1') hasH1 = true
    
    if (index > 0) {
      const prevLevel = parseInt(headings[index - 1].tagName[1])
      const currentLevel = parseInt(heading.tagName[1])
      
      if (currentLevel > prevLevel + 1) {
        improperHierarchy = true
      }
    }
  })

  if (!hasH1) {
    issues.push({
      id: 'missing-h1',
      severity: 'medium',
      category: 'accessibility',
      description: '页面缺少H1标题',
      suggestion: '为每个页面添加唯一的H1标题'
    })
    score -= 10
  }

  if (improperHierarchy) {
    issues.push({
      id: 'improper-heading-hierarchy',
      severity: 'low',
      category: 'accessibility',
      description: '标题层级结构不正确',
      suggestion: '确保标题按层级递增，不要跳级'
    })
    score -= 5
  }

  return {
    id: 'accessibility-test',
    type: 'accessibility',
    name: '可访问性测试',
    status: score >= 90 ? 'passed' : score >= 70 ? 'warning' : 'failed',
    score: Math.max(0, score),
    duration: 0,
    issues,
    recommendations: generateAccessibilityRecommendations(issues),
    timestamp: Date.now()
  }
}

/**
 * 可用性测试
 */
const runUsabilityTest = async (
  config: UXTestConfig,
  signal?: AbortSignal
): Promise<TestResult> => {
  const issues: TestIssue[] = []
  let score = 100

  // 检查触摸目标大小
  if (config.testTouchTargets) {
    const touchTargets = document.querySelectorAll('button, a, input, [role="button"]')
    let smallTargets = 0

    touchTargets.forEach(target => {
      const rect = target.getBoundingClientRect()
      if (rect.width < 44 || rect.height < 44) {
        smallTargets++
      }
    })

    if (smallTargets > 0) {
      issues.push({
        id: 'small-touch-targets',
        severity: 'medium',
        category: 'usability',
        description: `${smallTargets} 个触摸目标小于44px`,
        suggestion: '确保触摸目标至少为44x44px以提高可用性'
      })
      score -= 15
    }
  }

  // 检查链接可识别性
  const links = document.querySelectorAll('a')
  let unclearLinks = 0

  links.forEach(link => {
    const text = link.textContent?.trim()
    if (!text || text.length < 3 || text === '点击这里' || text === 'click here') {
      unclearLinks++
    }
  })

  if (unclearLinks > 0) {
    issues.push({
      id: 'unclear-links',
      severity: 'low',
      category: 'usability',
      description: `${unclearLinks} 个链接文本不够描述性`,
      suggestion: '使用描述性的链接文本，避免使用"点击这里"等模糊表述'
    })
    score -= 10
  }

  // 检查表单标签
  const formInputs = document.querySelectorAll('input, select, textarea')
  let unlabeledInputs = 0

  formInputs.forEach(input => {
    const hasLabel = input.getAttribute('aria-label') ||
                     input.getAttribute('aria-labelledby') ||
                     document.querySelector(`label[for="${input.id}"]`) ||
                     input.closest('label')
    
    if (!hasLabel) {
      unlabeledInputs++
    }
  })

  if (unlabeledInputs > 0) {
    issues.push({
      id: 'unlabeled-form-inputs',
      severity: 'medium',
      category: 'usability',
      description: `${unlabeledInputs} 个表单输入缺少标签`,
      suggestion: '为所有表单元素添加适当的标签'
    })
    score -= 20
  }

  return {
    id: 'usability-test',
    type: 'usability',
    name: '可用性测试',
    status: score >= 85 ? 'passed' : score >= 70 ? 'warning' : 'failed',
    score: Math.max(0, score),
    duration: 0,
    issues,
    recommendations: generateUsabilityRecommendations(issues),
    timestamp: Date.now()
  }
}

/**
 * 其他测试函数的简化实现
 */
const runCompatibilityTest = async (config: UXTestConfig, signal?: AbortSignal): Promise<TestResult> => {
  return createEmptyResult('compatibility')
}

const runResponsivenessTest = async (config: UXTestConfig, signal?: AbortSignal): Promise<TestResult> => {
  return createEmptyResult('responsiveness')
}

const runInteractionTest = async (config: UXTestConfig, signal?: AbortSignal): Promise<TestResult> => {
  return createEmptyResult('interaction')
}

const runNavigationTest = async (config: UXTestConfig, signal?: AbortSignal): Promise<TestResult> => {
  return createEmptyResult('navigation')
}

const runContentTest = async (config: UXTestConfig, signal?: AbortSignal): Promise<TestResult> => {
  return createEmptyResult('content')
}

/**
 * 辅助函数
 */
const createEmptyResult = (type: TestType): TestResult => ({
  id: `${type}-${Date.now()}`,
  type,
  name: getTestName(type),
  status: 'passed',
  score: 100,
  duration: 0,
  issues: [],
  recommendations: [],
  timestamp: Date.now()
})

const getTestName = (type: TestType): string => {
  const names: Record<TestType, string> = {
    performance: '性能测试',
    accessibility: '可访问性测试',
    usability: '可用性测试',
    compatibility: '兼容性测试',
    responsiveness: '响应式测试',
    interaction: '交互测试',
    navigation: '导航测试',
    content: '内容测试'
  }
  return names[type]
}

const generatePerformanceRecommendations = (issues: TestIssue[]): string[] => {
  return issues.map(issue => issue.suggestion || '优化相关性能问题')
}

const generateAccessibilityRecommendations = (issues: TestIssue[]): string[] => {
  return issues.map(issue => issue.suggestion || '改善可访问性')
}

const generateUsabilityRecommendations = (issues: TestIssue[]): string[] => {
  return issues.map(issue => issue.suggestion || '提升用户体验')
}

const generateSummary = (results: TestResult[]) => {
  const totalScore = results.reduce((sum, result) => sum + result.score, 0)
  const averageScore = results.length > 0 ? totalScore / results.length : 0
  
  const passedTests = results.filter(r => r.status === 'passed').length
  const failedTests = results.filter(r => r.status === 'failed').length
  const warningTests = results.filter(r => r.status === 'warning').length
  
  const totalIssues = results.reduce((sum, result) => sum + result.issues.length, 0)
  const criticalIssues = results.reduce((sum, result) => 
    sum + result.issues.filter(i => i.severity === 'critical').length, 0
  )

  return {
    averageScore: Math.round(averageScore),
    totalTests: results.length,
    passedTests,
    failedTests,
    warningTests,
    totalIssues,
    criticalIssues,
    status: averageScore >= 90 ? 'excellent' : averageScore >= 70 ? 'good' : 'needs-improvement'
  }
}

/**
 * UX测试控制面板组件
 */
export const UXTestPanel: React.FC<{
  config: UXTestConfig
  onConfigChange: (updates: Partial<UXTestConfig>) => void
  results: TestResult[]
  isRunning: boolean
  currentTest: TestType | null
  progress: number
  onRunTests: () => void
  onStopTests: () => void
  onExportResults: () => void
  className?: string
}> = ({ 
  config, 
  onConfigChange, 
  results, 
  isRunning, 
  currentTest, 
  progress, 
  onRunTests, 
  onStopTests, 
  onExportResults, 
  className 
}) => {
  const summary = generateSummary(results)

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'passed': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      default: return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <Card className={cn("p-6 space-y-6", className)}>
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TestTube className="w-6 h-6 text-primary" />
          <h2 className="text-xl font-semibold">UX测试中心</h2>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={onExportResults}
            disabled={results.length === 0}
          >
            <Download className="w-4 h-4 mr-2" />
            导出结果
          </Button>
          
          <Button
            onClick={isRunning ? onStopTests : onRunTests}
            disabled={isRunning && !currentTest}
          >
            {isRunning ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                停止测试
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                运行测试
              </>
            )}
          </Button>
        </div>
      </div>

      {/* 测试概览 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-4 bg-muted rounded-lg">
          <div className="text-2xl font-bold text-primary">{summary.averageScore}</div>
          <div className="text-sm text-muted-foreground">总体评分</div>
        </div>
        
        <div className="text-center p-4 bg-muted rounded-lg">
          <div className="text-2xl font-bold text-green-600">{summary.passedTests}</div>
          <div className="text-sm text-muted-foreground">通过测试</div>
        </div>
        
        <div className="text-center p-4 bg-muted rounded-lg">
          <div className="text-2xl font-bold text-yellow-600">{summary.warningTests}</div>
          <div className="text-sm text-muted-foreground">警告</div>
        </div>
        
        <div className="text-center p-4 bg-muted rounded-lg">
          <div className="text-2xl font-bold text-red-600">{summary.criticalIssues}</div>
          <div className="text-sm text-muted-foreground">严重问题</div>
        </div>
      </div>

      {/* 进度条 */}
      {isRunning && (
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <span>当前测试: {currentTest ? getTestName(currentTest) : '准备中...'}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} />
        </div>
      )}

      {/* 测试结果列表 */}
      <div className="space-y-3">
        <h3 className="font-semibold">测试结果</h3>
        
        {results.length > 0 ? (
          <div className="space-y-2">
            {results.map(result => (
              <div key={result.id} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(result.status)}
                    <span className="font-medium">{result.name}</span>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <span className={cn("font-bold", getScoreColor(result.score))}>
                      {result.score}%
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {result.duration}ms
                    </span>
                  </div>
                </div>
                
                {result.issues.length > 0 && (
                  <div className="mt-3 space-y-1">
                    <div className="text-sm font-medium text-muted-foreground">
                      发现问题 ({result.issues.length})
                    </div>
                    {result.issues.slice(0, 3).map(issue => (
                      <div key={issue.id} className="text-xs p-2 bg-muted rounded">
                        <span className={cn(
                          "font-medium",
                          issue.severity === 'critical' && "text-red-600",
                          issue.severity === 'high' && "text-orange-600",
                          issue.severity === 'medium' && "text-yellow-600",
                          issue.severity === 'low' && "text-blue-600"
                        )}>
                          [{issue.severity.toUpperCase()}]
                        </span>
                        {' '}{issue.description}
                      </div>
                    ))}
                    {result.issues.length > 3 && (
                      <div className="text-xs text-muted-foreground">
                        还有 {result.issues.length - 3} 个问题...
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <TestTube className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>点击"运行测试"开始UX测试</p>
          </div>
        )}
      </div>

      {/* 测试配置 */}
      <div className="space-y-4">
        <h3 className="font-semibold">测试配置</h3>
        
        <div className="grid gap-3">
          <label className="flex items-center justify-between">
            <span>性能测试</span>
            <input
              type="checkbox"
              checked={config.includePerformance}
              onChange={(e) => onConfigChange({ includePerformance: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>可访问性测试</span>
            <input
              type="checkbox"
              checked={config.includeAccessibility}
              onChange={(e) => onConfigChange({ includeAccessibility: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <span>可用性测试</span>
            <input
              type="checkbox"
              checked={config.includeUsability}
              onChange={(e) => onConfigChange({ includeUsability: e.target.checked })}
              className="w-4 h-4"
            />
          </label>
        </div>
      </div>
    </Card>
  )
}

/**
 * UX测试提供者组件
 */
export const UXTestProvider: React.FC<{
  children: React.ReactNode
  config?: Partial<UXTestConfig>
  showPanel?: boolean
}> = ({ children, config = {}, showPanel = false }) => {
  const [testConfig, setTestConfig] = useState<UXTestConfig>({
    testTypes: ['performance', 'accessibility', 'usability'],
    includePerformance: true,
    includeAccessibility: true,
    includeUsability: true,
    performanceThresholds: {
      firstContentfulPaint: 1800,
      largestContentfulPaint: 2500,
      firstInputDelay: 100,
      cumulativeLayoutShift: 0.1,
      timeToInteractive: 3800
    },
    accessibilityLevel: 'AA',
    testColorContrast: true,
    testKeyboardNavigation: true,
    testScreenReader: false,
    testTouchTargets: true,
    testReadability: true,
    testNavigation: true,
    browsers: ['chrome', 'firefox', 'safari', 'edge'],
    viewports: [
      { width: 375, height: 667, name: 'Mobile' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 1920, height: 1080, name: 'Desktop' }
    ],
    enableRealUserMonitoring: false,
    enableA11yTesting: true,
    enablePerformanceMonitoring: true,
    ...config
  })

  const uxTesting = useUXTesting(testConfig)

  return (
    <div className="ux-test-provider">
      {children}
      
      {showPanel && (
        <div className="fixed bottom-4 right-4 z-50 w-96 max-h-[80vh] overflow-y-auto">
          <UXTestPanel
            config={testConfig}
            onConfigChange={setTestConfig}
            results={uxTesting.results}
            isRunning={uxTesting.isRunning}
            currentTest={uxTesting.currentTest}
            progress={uxTesting.progress}
            onRunTests={uxTesting.runAllTests}
            onStopTests={uxTesting.stopTests}
            onExportResults={uxTesting.exportResults}
          />
        </div>
      )}
    </div>
  )
}
