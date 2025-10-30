/**
 * 性能测试工具
 * 自动化性能测试和验证
 */

import performanceMonitor from '../services/performance'
import performanceBudgetMonitor from '../services/performanceBudget'
import cachePerformanceMonitor from '../utils/cachePerformanceMonitor'
import performanceBaselineManager from '../utils/performanceBaselineManager'

interface PerformanceTestResult {
  testName: string
  passed: boolean
  metrics: Record<string, number>
  threshold: Record<string, number>
  message: string
}

class PerformanceTester {
  /**
   * 测试首屏加载时间
   */
  async testFirstPaintTime(): Promise<PerformanceTestResult> {
    const threshold = 2000 // 2秒
    let fcp = 0

    // 等待FCP收集
    await new Promise(resolve => setTimeout(resolve, 3000))

    const vitals = performanceMonitor.getWebVitals()
    fcp = vitals.firstContentfulPaint || 0

    const passed = fcp > 0 && fcp < threshold
    const loadTime = performance.now()

    return {
      testName: '首屏加载时间',
      passed,
      metrics: {
        fcp,
        loadTime,
      },
      threshold: {
        fcp: threshold,
      },
      message: passed
        ? `✅ 首屏加载时间 ${fcp.toFixed(2)}ms < ${threshold}ms`
        : `❌ 首屏加载时间 ${fcp.toFixed(2)}ms > ${threshold}ms`,
    }
  }

  /**
   * 测试Core Web Vitals
   */
  async testCoreWebVitals(): Promise<PerformanceTestResult> {
    await new Promise(resolve => setTimeout(resolve, 5000))

    const vitals = performanceMonitor.getWebVitals()
    const score = performanceMonitor.getPerformanceScore()

    const thresholds = {
      lcp: 2500,
      fid: 100,
      cls: 0.1,
      score: 90,
    }

    const metrics = {
      lcp: vitals.largestContentfulPaint || 0,
      fid: vitals.firstInputDelay || 0,
      cls: vitals.cumulativeLayoutShift || 0,
      score,
    }

    const passed =
      metrics.lcp <= thresholds.lcp &&
      metrics.fid <= thresholds.fid &&
      metrics.cls <= thresholds.cls &&
      metrics.score >= thresholds.score

    return {
      testName: 'Core Web Vitals',
      passed,
      metrics,
      threshold: thresholds,
      message: passed
        ? `✅ Core Web Vitals评分: ${score} (LCP: ${metrics.lcp.toFixed(2)}ms, FID: ${metrics.fid.toFixed(2)}ms, CLS: ${metrics.cls.toFixed(3)})`
        : `❌ Core Web Vitals未达标 (评分: ${score})`,
    }
  }

  /**
   * 测试Bundle大小
   */
  async testBundleSize(): Promise<PerformanceTestResult> {
    const threshold = 500 * 1024 // 500KB
    let bundleSize = 0

    if (typeof window !== 'undefined' && window.performance) {
      const resources = window.performance.getEntriesByType('resource') as PerformanceResourceTiming[]
      const jsResources = resources.filter(r => r.name.endsWith('.js'))
      bundleSize = jsResources.reduce((sum, r) => {
        const size = (r as any).transferSize || 0
        return sum + size
      }, 0)
    }

    const passed = bundleSize > 0 && bundleSize < threshold
    const reductionPercent = bundleSize > 0 
      ? ((threshold - bundleSize) / threshold) * 100 
      : 0

    return {
      testName: 'Bundle大小',
      passed,
      metrics: {
        bundleSize,
        reductionPercent,
      },
      threshold: {
        bundleSize: threshold,
      },
      message: passed
        ? `✅ Bundle大小 ${(bundleSize / 1024).toFixed(2)}KB < ${(threshold / 1024).toFixed(2)}KB`
        : `❌ Bundle大小 ${(bundleSize / 1024).toFixed(2)}KB > ${(threshold / 1024).toFixed(2)}KB`,
    }
  }

  /**
   * 测试缓存命中率
   */
  async testCacheHitRate(): Promise<PerformanceTestResult> {
    await cachePerformanceMonitor.updateCacheStats()
    const metrics = cachePerformanceMonitor.getMetrics()

    const threshold = 80 // 80%
    const passed = metrics.hitRate >= threshold

    return {
      testName: '缓存命中率',
      passed,
      metrics: {
        hitRate: metrics.hitRate,
        totalRequests: metrics.totalRequests,
        cachedRequests: metrics.cachedRequests,
      },
      threshold: {
        hitRate: threshold,
      },
      message: passed
        ? `✅ 缓存命中率 ${metrics.hitRate.toFixed(2)}% >= ${threshold}%`
        : `❌ 缓存命中率 ${metrics.hitRate.toFixed(2)}% < ${threshold}%`,
    }
  }

  /**
   * 运行所有性能测试
   */
  async runAllTests(): Promise<PerformanceTestResult[]> {
    console.log('🧪 开始性能测试...')

    const results = await Promise.all([
      this.testFirstPaintTime(),
      this.testCoreWebVitals(),
      this.testBundleSize(),
      this.testCacheHitRate(),
    ])

    const passedCount = results.filter(r => r.passed).length
    const totalCount = results.length

    console.log(`🧪 性能测试完成: ${passedCount}/${totalCount} 通过`)
    results.forEach(result => {
      console.log(result.message)
    })

    return results
  }

  /**
   * 验证性能指标是否达到验收标准
   */
  async validateAcceptanceCriteria(): Promise<{
    allPassed: boolean
    results: PerformanceTestResult[]
    summary: string
  }> {
    const results = await this.runAllTests()
    const allPassed = results.every(r => r.passed)

    const summary = `
性能验收测试结果:
${results.map(r => `  ${r.message}`).join('\n')}

总体结果: ${allPassed ? '✅ 通过' : '❌ 未通过'}
    `.trim()

    return {
      allPassed,
      results,
      summary,
    }
  }
}

// 创建全局实例
const performanceTester = new PerformanceTester()

export default performanceTester
export { PerformanceTester }
export type { PerformanceTestResult }

