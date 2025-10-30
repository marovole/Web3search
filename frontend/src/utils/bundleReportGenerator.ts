/**
 * Bundle优化报告生成器
 * 分析构建输出并生成优化建议
 */

interface BundleReport {
  totalSize: number
  totalGzipSize: number
  chunkCount: number
  chunks: Array<{
    name: string
    size: number
    gzipSize: number
    percentage: number
  }>
  recommendations: string[]
}

class BundleReportGenerator {
  /**
   * 生成Bundle分析报告
   */
  async generateReport(): Promise<BundleReport> {
    // 在实际实现中，这里应该读取rollup-plugin-visualizer生成的stats.html
    // 或者解析构建输出
    const report: BundleReport = {
      totalSize: 0,
      totalGzipSize: 0,
      chunkCount: 0,
      chunks: [],
      recommendations: [],
    }

    // 从performance API获取资源信息
    if (typeof window !== 'undefined' && window.performance) {
      const resources = window.performance.getEntriesByType('resource') as PerformanceResourceTiming[]
      const jsResources = resources.filter(r => r.name.endsWith('.js'))
      
      report.totalSize = jsResources.reduce((sum, r) => {
        const size = (r as any).transferSize || 0
        return sum + size
      }, 0)

      report.chunkCount = jsResources.length

      // 分析各个chunk
      jsResources.forEach((resource, index) => {
        const size = (resource as any).transferSize || 0
        const name = resource.name.split('/').pop() || `chunk-${index}`
        
        report.chunks.push({
          name,
          size,
          gzipSize: size * 0.3, // 估算gzip压缩率
          percentage: (size / report.totalSize) * 100,
        })
      })

      // 生成优化建议
      report.recommendations = this.generateRecommendations(report)
    }

    return report
  }

  /**
   * 生成优化建议
   */
  private generateRecommendations(report: BundleReport): string[] {
    const recommendations: string[] = []

    // 检查总大小
    const totalSizeKB = report.totalSize / 1024
    if (totalSizeKB > 500) {
      recommendations.push(
        `Bundle总大小 ${totalSizeKB.toFixed(2)}KB 过大，建议启用代码分割和tree-shaking`
      )
    }

    // 检查是否有过大的chunk
    report.chunks.forEach(chunk => {
      const chunkSizeKB = chunk.size / 1024
      if (chunkSizeKB > 200) {
        recommendations.push(
          `Chunk "${chunk.name}" 过大 (${chunkSizeKB.toFixed(2)}KB)，建议进一步分割`
        )
      }
    })

    // 检查chunk数量
    if (report.chunkCount < 3) {
      recommendations.push(
        'Chunk数量过少，建议启用代码分割以优化加载性能'
      )
    } else if (report.chunkCount > 20) {
      recommendations.push(
        'Chunk数量过多，可能影响HTTP/2复用，建议合并相关chunk'
      )
    }

    // 检查是否有重复依赖
    const chunkNames = report.chunks.map(c => c.name)
    const duplicates = chunkNames.filter((name, index) => chunkNames.indexOf(name) !== index)
    if (duplicates.length > 0) {
      recommendations.push(
        `发现重复的chunk: ${duplicates.join(', ')}，建议提取为公共chunk`
      )
    }

    return recommendations
  }

  /**
   * 生成HTML报告
   */
  async generateHTMLReport(): Promise<string> {
    const report = await this.generateReport()

    return `
<!DOCTYPE html>
<html>
<head>
  <title>Bundle优化报告</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    .chunk { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
    .recommendation { margin: 5px 0; padding: 5px; background: #fff3cd; }
    .summary { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
  </style>
</head>
<body>
  <h1>Bundle优化报告</h1>
  
  <div class="summary">
    <h2>总览</h2>
    <p>总大小: ${(report.totalSize / 1024).toFixed(2)}KB</p>
    <p>Gzip后估计: ${(report.totalGzipSize / 1024).toFixed(2)}KB</p>
    <p>Chunk数量: ${report.chunkCount}</p>
  </div>
  
  <h2>Chunks详情</h2>
  ${report.chunks.map(chunk => `
    <div class="chunk">
      <h3>${chunk.name}</h3>
      <p>大小: ${(chunk.size / 1024).toFixed(2)}KB (${chunk.percentage.toFixed(2)}%)</p>
      <p>Gzip估计: ${(chunk.gzipSize / 1024).toFixed(2)}KB</p>
    </div>
  `).join('')}
  
  <h2>优化建议</h2>
  ${report.recommendations.length > 0
    ? report.recommendations.map(rec => `<div class="recommendation">${rec}</div>`).join('')
    : '<div class="recommendation">✅ Bundle大小合理，无需优化</div>'
  }
</body>
</html>
    `.trim()
  }

  /**
   * 保存报告到文件（开发环境）
   */
  async saveReport(): Promise<void> {
    const report = await this.generateReport()
    const html = await this.generateHTMLReport()

    console.log('📊 Bundle分析报告:')
    console.log(`总大小: ${(report.totalSize / 1024).toFixed(2)}KB`)
    console.log(`Chunk数量: ${report.chunkCount}`)
    console.log('\n优化建议:')
    report.recommendations.forEach(rec => console.log(`  - ${rec}`))

    // 在开发环境中，可以将报告保存到文件
    if (typeof window !== 'undefined' && 'Blob' in window) {
      const blob = new Blob([html], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      console.log('📄 报告已生成，可通过以下URL查看:', url)
    }
  }
}

export const bundleReportGenerator = new BundleReportGenerator()
export { BundleReportGenerator }
export type { BundleReport }

