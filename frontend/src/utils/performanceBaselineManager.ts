/**
 * 性能基准线建立和管理
 * 记录性能指标的历史基准，用于对比和优化
 */

import performanceMonitor from '../services/performance'
import performanceBudgetMonitor from '../services/performanceBudget'
import cachePerformanceMonitor from '../utils/cachePerformanceMonitor'
import cacheVersionManager from '../utils/cacheVersionManager'

interface PerformanceBaseline {
  timestamp: number
  webVitals: {
    fcp: number
    lcp: number
    fid: number
    cls: number
  }
  bundleSize: number
  loadTime: number
  cacheHitRate: number
  performanceScore: number
}

interface BaselineComparison {
  metric: string
  current: number
  baseline: number
  improvement: number
  improvementPercent: number
}

class PerformanceBaselineManager {
  private readonly STORAGE_KEY = 'performance-baseline'
  private baseline: PerformanceBaseline | null = null

  /**
   * 建立性能基准线
   */
  async establishBaseline(): Promise<PerformanceBaseline> {
    // 等待性能指标收集完成
    await new Promise(resolve => setTimeout(resolve, 5000))

    const vitals = performanceMonitor.getWebVitals()
    const performanceScore = performanceMonitor.getPerformanceScore()
    
    // 获取缓存统计
    await cachePerformanceMonitor.updateCacheStats()
    const cacheMetrics = cachePerformanceMonitor.getMetrics()
    
    // 计算Bundle大小（从performance API获取）
    let bundleSize = 0
    if (typeof window !== 'undefined' && window.performance) {
      const resources = window.performance.getEntriesByType('resource') as PerformanceResourceTiming[]
      const jsResources = resources.filter(r => r.name.endsWith('.js'))
      bundleSize = jsResources.reduce((sum, r) => {
        const size = (r as any).transferSize || 0
        return sum + size
      }, 0)
    }

    // 计算页面加载时间
    let loadTime = 0
    if (window.performance && window.performance.timing) {
      const timing = window.performance.timing
      loadTime = timing.loadEventEnd - timing.navigationStart
    }

    const baseline: PerformanceBaseline = {
      timestamp: Date.now(),
      webVitals: {
        fcp: vitals.firstContentfulPaint || 0,
        lcp: vitals.largestContentfulPaint || 0,
        fid: vitals.firstInputDelay || 0,
        cls: vitals.cumulativeLayoutShift || 0,
      },
      bundleSize,
      loadTime,
      cacheHitRate: cacheMetrics.hitRate,
      performanceScore,
    }

    this.baseline = baseline
    this.saveBaseline(baseline)
    
    console.log('📊 性能基准线已建立:', baseline)
    return baseline
  }

  /**
   * 保存基准线到localStorage
   */
  private saveBaseline(baseline: PerformanceBaseline): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(baseline))
    } catch (error) {
      console.error('Failed to save baseline:', error)
    }
  }

  /**
   * 从localStorage加载基准线
   */
  loadBaseline(): PerformanceBaseline | null {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY)
      if (stored) {
        this.baseline = JSON.parse(stored)
        return this.baseline
      }
    } catch (error) {
      console.error('Failed to load baseline:', error)
    }
    return null
  }

  /**
   * 获取当前性能指标
   */
  async getCurrentMetrics(): Promise<PerformanceBaseline> {
    await new Promise(resolve => setTimeout(resolve, 2000))

    const vitals = performanceMonitor.getWebVitals()
    const performanceScore = performanceMonitor.getPerformanceScore()
    
    await cachePerformanceMonitor.updateCacheStats()
    const cacheMetrics = cachePerformanceMonitor.getMetrics()
    
    let bundleSize = 0
    let loadTime = 0
    
    if (typeof window !== 'undefined' && window.performance) {
      const resources = window.performance.getEntriesByType('resource') as PerformanceResourceTiming[]
      const jsResources = resources.filter(r => r.name.endsWith('.js'))
      bundleSize = jsResources.reduce((sum, r) => {
        const size = (r as any).transferSize || 0
        return sum + size
      }, 0)

      if (window.performance.timing) {
        const timing = window.performance.timing
        loadTime = timing.loadEventEnd - timing.navigationStart
      }
    }

    return {
      timestamp: Date.now(),
      webVitals: {
        fcp: vitals.firstContentfulPaint || 0,
        lcp: vitals.largestContentfulPaint || 0,
        fid: vitals.firstInputDelay || 0,
        cls: vitals.cumulativeLayoutShift || 0,
      },
      bundleSize,
      loadTime,
      cacheHitRate: cacheMetrics.hitRate,
      performanceScore,
    }
  }

  /**
   * 对比当前性能与基准线
   */
  async compareWithBaseline(): Promise<BaselineComparison[]> {
    const baseline = this.baseline || this.loadBaseline()
    if (!baseline) {
      console.warn('No baseline found, establishing new baseline...')
      await this.establishBaseline()
      return []
    }

    const current = await this.getCurrentMetrics()
    const comparisons: BaselineComparison[] = []

    // 对比各个指标
    comparisons.push({
      metric: 'FCP',
      current: current.webVitals.fcp,
      baseline: baseline.webVitals.fcp,
      improvement: baseline.webVitals.fcp - current.webVitals.fcp,
      improvementPercent: ((baseline.webVitals.fcp - current.webVitals.fcp) / baseline.webVitals.fcp) * 100,
    })

    comparisons.push({
      metric: 'LCP',
      current: current.webVitals.lcp,
      baseline: baseline.webVitals.lcp,
      improvement: baseline.webVitals.lcp - current.webVitals.lcp,
      improvementPercent: ((baseline.webVitals.lcp - current.webVitals.lcp) / baseline.webVitals.lcp) * 100,
    })

    comparisons.push({
      metric: 'Bundle Size',
      current: current.bundleSize,
      baseline: baseline.bundleSize,
      improvement: baseline.bundleSize - current.bundleSize,
      improvementPercent: ((baseline.bundleSize - current.bundleSize) / baseline.bundleSize) * 100,
    })

    comparisons.push({
      metric: 'Load Time',
      current: current.loadTime,
      baseline: baseline.loadTime,
      improvement: baseline.loadTime - current.loadTime,
      improvementPercent: ((baseline.loadTime - current.loadTime) / baseline.loadTime) * 100,
    })

    comparisons.push({
      metric: 'Performance Score',
      current: current.performanceScore,
      baseline: baseline.performanceScore,
      improvement: current.performanceScore - baseline.performanceScore,
      improvementPercent: ((current.performanceScore - baseline.performanceScore) / baseline.performanceScore) * 100,
    })

    comparisons.push({
      metric: 'Cache Hit Rate',
      current: current.cacheHitRate,
      baseline: baseline.cacheHitRate,
      improvement: current.cacheHitRate - baseline.cacheHitRate,
      improvementPercent: ((current.cacheHitRate - baseline.cacheHitRate) / baseline.cacheHitRate) * 100,
    })

    return comparisons
  }

  /**
   * 生成性能对比报告
   */
  async generateComparisonReport(): Promise<string> {
    const comparisons = await this.compareWithBaseline()
    const baseline = this.baseline || this.loadBaseline()

    if (!baseline) {
      return '尚未建立性能基准线'
    }

    return `
性能对比报告（相对于基准线 ${new Date(baseline.timestamp).toLocaleString()}）:
${comparisons.map(c => `
${c.metric}:
  当前值: ${c.current.toFixed(2)}${c.metric.includes('Score') || c.metric.includes('Rate') ? '%' : 'ms'}
  基准值: ${c.baseline.toFixed(2)}${c.metric.includes('Score') || c.metric.includes('Rate') ? '%' : 'ms'}
  改进: ${c.improvement >= 0 ? '+' : ''}${c.improvement.toFixed(2)} (${c.improvementPercent >= 0 ? '+' : ''}${c.improvementPercent.toFixed(2)}%)
`).join('')}
    `.trim()
  }
}

// 创建全局实例
const performanceBaselineManager = new PerformanceBaselineManager()

// 页面加载后自动建立基准线（如果不存在）
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    setTimeout(async () => {
      const baseline = performanceBaselineManager.loadBaseline()
      if (!baseline) {
        console.log('📊 首次运行，建立性能基准线...')
        await performanceBaselineManager.establishBaseline()
      } else {
        console.log('📊 加载性能基准线:', baseline)
        // 对比当前性能
        const comparisons = await performanceBaselineManager.compareWithBaseline()
        console.log('📊 性能对比:', comparisons)
      }
    }, 5000)
  })
}

export default performanceBaselineManager
export { PerformanceBaselineManager }
export type { PerformanceBaseline, BaselineComparison }

