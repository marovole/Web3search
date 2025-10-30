/**
 * 性能预算监控
 * 监控bundle大小和性能指标，超出预算时发出警告
 */

interface PerformanceBudget {
  bundleSize: {
    max: number // 最大bundle大小 (KB)
    warning: number // 警告阈值 (KB)
  }
  loadTime: {
    max: number // 最大加载时间 (ms)
    warning: number // 警告阈值 (ms)
  }
  webVitals: {
    lcp: { max: number; warning: number } // Largest Contentful Paint
    fid: { max: number; warning: number } // First Input Delay
    cls: { max: number; warning: number } // Cumulative Layout Shift
    fcp: { max: number; warning: number } // First Contentful Paint
  }
}

const DEFAULT_BUDGET: PerformanceBudget = {
  bundleSize: {
    max: 500, // 500KB
    warning: 400, // 400KB
  },
  loadTime: {
    max: 3000, // 3秒
    warning: 2000, // 2秒
  },
  webVitals: {
    lcp: { max: 4000, warning: 2500 },
    fid: { max: 300, warning: 100 },
    cls: { max: 0.25, warning: 0.1 },
    fcp: { max: 3000, warning: 1800 },
  },
}

class PerformanceBudgetMonitor {
  private budget: PerformanceBudget
  private violations: Array<{ metric: string; value: number; threshold: number; severity: 'warning' | 'error' }> = []

  constructor(budget: Partial<PerformanceBudget> = {}) {
    this.budget = { ...DEFAULT_BUDGET, ...budget }
  }

  /**
   * 检查bundle大小
   */
  checkBundleSize(size: number): boolean {
    if (size > this.budget.bundleSize.max) {
      this.violations.push({
        metric: 'Bundle Size',
        value: size,
        threshold: this.budget.bundleSize.max,
        severity: 'error',
      })
      console.error(`❌ Bundle大小超出预算: ${size}KB > ${this.budget.bundleSize.max}KB`)
      return false
    } else if (size > this.budget.bundleSize.warning) {
      this.violations.push({
        metric: 'Bundle Size',
        value: size,
        threshold: this.budget.bundleSize.warning,
        severity: 'warning',
      })
      console.warn(`⚠️ Bundle大小接近预算: ${size}KB > ${this.budget.bundleSize.warning}KB`)
      return true
    }
    return true
  }

  /**
   * 检查加载时间
   */
  checkLoadTime(time: number): boolean {
    if (time > this.budget.loadTime.max) {
      this.violations.push({
        metric: 'Load Time',
        value: time,
        threshold: this.budget.loadTime.max,
        severity: 'error',
      })
      console.error(`❌ 加载时间超出预算: ${time}ms > ${this.budget.loadTime.max}ms`)
      return false
    } else if (time > this.budget.loadTime.warning) {
      this.violations.push({
        metric: 'Load Time',
        value: time,
        threshold: this.budget.loadTime.warning,
        severity: 'warning',
      })
      console.warn(`⚠️ 加载时间接近预算: ${time}ms > ${this.budget.loadTime.warning}ms`)
      return true
    }
    return true
  }

  /**
   * 检查Web Vitals指标
   */
  checkWebVital(name: keyof PerformanceBudget['webVitals'], value: number): boolean {
    const thresholds = this.budget.webVitals[name]
    
    if (value > thresholds.max) {
      this.violations.push({
        metric: name.toUpperCase(),
        value,
        threshold: thresholds.max,
        severity: 'error',
      })
      console.error(`❌ ${name.toUpperCase()}超出预算: ${value} > ${thresholds.max}`)
      return false
    } else if (value > thresholds.warning) {
      this.violations.push({
        metric: name.toUpperCase(),
        value,
        threshold: thresholds.warning,
        severity: 'warning',
      })
      console.warn(`⚠️ ${name.toUpperCase()}接近预算: ${value} > ${thresholds.warning}`)
      return true
    }
    return true
  }

  /**
   * 获取所有违规记录
   */
  getViolations() {
    return [...this.violations]
  }

  /**
   * 清除违规记录
   */
  clearViolations() {
    this.violations = []
  }

  /**
   * 生成性能预算报告
   */
  generateReport(): string {
    const errors = this.violations.filter(v => v.severity === 'error')
    const warnings = this.violations.filter(v => v.severity === 'warning')

    return `
性能预算报告:
- 错误: ${errors.length}个
- 警告: ${warnings.length}个

${errors.length > 0 ? `错误详情:\n${errors.map(v => `  - ${v.metric}: ${v.value} > ${v.threshold}`).join('\n')}` : ''}
${warnings.length > 0 ? `警告详情:\n${warnings.map(v => `  - ${v.metric}: ${v.value} > ${v.threshold}`).join('\n')}` : ''}
    `.trim()
  }
}

// 创建全局实例
const performanceBudgetMonitor = new PerformanceBudgetMonitor()

// 在页面加载时检查性能指标
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    // 检查页面加载时间
    if (window.performance && window.performance.timing) {
      const timing = window.performance.timing
      const loadTime = timing.loadEventEnd - timing.navigationStart
      performanceBudgetMonitor.checkLoadTime(loadTime)
    }

    // 检查资源大小
    if (window.performance && window.performance.getEntriesByType) {
      const resources = window.performance.getEntriesByType('resource') as PerformanceResourceTiming[]
      const jsResources = resources.filter(r => r.name.endsWith('.js'))
      const totalJsSize = jsResources.reduce((sum, r) => {
        const size = (r as any).transferSize || 0
        return sum + size
      }, 0)
      
      if (totalJsSize > 0) {
        performanceBudgetMonitor.checkBundleSize(totalJsSize / 1024) // 转换为KB
      }
    }
  })
}

export default performanceBudgetMonitor
export { PerformanceBudgetMonitor }
export type { PerformanceBudget }

