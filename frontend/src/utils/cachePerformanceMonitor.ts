/**
 * 缓存性能监控
 * 监控缓存命中率、缓存大小和性能指标
 */

import cacheVersionManager from './cacheVersionManager'

interface CachePerformanceMetrics {
  hitRate: number
  missRate: number
  totalRequests: number
  cachedRequests: number
  networkRequests: number
  averageResponseTime: number
  cacheSize: number
  cacheCount: number
}

class CachePerformanceMonitor {
  private metrics: CachePerformanceMetrics = {
    hitRate: 0,
    missRate: 0,
    totalRequests: 0,
    cachedRequests: 0,
    networkRequests: 0,
    averageResponseTime: 0,
    cacheSize: 0,
    cacheCount: 0,
  }

  private responseTimes: number[] = []
  private readonly MAX_RESPONSE_TIMES = 100

  /**
   * 记录缓存命中
   */
  recordCacheHit(responseTime: number = 0) {
    this.metrics.totalRequests++
    this.metrics.cachedRequests++
    this.updateMetrics()
    this.recordResponseTime(responseTime)
  }

  /**
   * 记录缓存未命中
   */
  recordCacheMiss(responseTime: number = 0) {
    this.metrics.totalRequests++
    this.metrics.networkRequests++
    this.updateMetrics()
    this.recordResponseTime(responseTime)
  }

  /**
   * 记录响应时间
   */
  private recordResponseTime(time: number) {
    this.responseTimes.push(time)
    if (this.responseTimes.length > this.MAX_RESPONSE_TIMES) {
      this.responseTimes.shift()
    }

    // 计算平均响应时间
    const sum = this.responseTimes.reduce((a, b) => a + b, 0)
    this.metrics.averageResponseTime = sum / this.responseTimes.length
  }

  /**
   * 更新指标
   */
  private updateMetrics() {
    if (this.metrics.totalRequests > 0) {
      this.metrics.hitRate = (this.metrics.cachedRequests / this.metrics.totalRequests) * 100
      this.metrics.missRate = (this.metrics.networkRequests / this.metrics.totalRequests) * 100
    }
  }

  /**
   * 更新缓存统计信息
   */
  async updateCacheStats() {
    try {
      const stats = await cacheVersionManager.getCacheStats()
      this.metrics.cacheSize = stats.totalSize
      this.metrics.cacheCount = stats.cacheCount
    } catch (error) {
      console.error('Failed to update cache stats:', error)
    }
  }

  /**
   * 获取当前指标
   */
  getMetrics(): CachePerformanceMetrics {
    return { ...this.metrics }
  }

  /**
   * 获取缓存命中率
   */
  getHitRate(): number {
    return this.metrics.hitRate
  }

  /**
   * 重置指标
   */
  reset() {
    this.metrics = {
      hitRate: 0,
      missRate: 0,
      totalRequests: 0,
      cachedRequests: 0,
      networkRequests: 0,
      averageResponseTime: 0,
      cacheSize: 0,
      cacheCount: 0,
    }
    this.responseTimes = []
  }

  /**
   * 生成性能报告
   */
  generateReport(): string {
    return `
缓存性能报告:
- 总请求数: ${this.metrics.totalRequests}
- 缓存命中: ${this.metrics.cachedRequests} (${this.metrics.hitRate.toFixed(2)}%)
- 网络请求: ${this.metrics.networkRequests} (${this.metrics.missRate.toFixed(2)}%)
- 平均响应时间: ${this.metrics.averageResponseTime.toFixed(2)}ms
- 缓存大小: ${(this.metrics.cacheSize / 1024 / 1024).toFixed(2)}MB
- 缓存数量: ${this.metrics.cacheCount}
    `.trim()
  }
}

// 创建全局实例
const cachePerformanceMonitor = new CachePerformanceMonitor()

// 定期更新缓存统计信息
if (typeof window !== 'undefined') {
  setInterval(() => {
    cachePerformanceMonitor.updateCacheStats()
  }, 60000) // 每分钟更新一次

  // 初始更新
  cachePerformanceMonitor.updateCacheStats()
}

export default cachePerformanceMonitor
export { CachePerformanceMonitor }
export type { CachePerformanceMetrics }

