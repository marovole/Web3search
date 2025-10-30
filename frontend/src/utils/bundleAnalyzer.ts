/**
 * Bundle分析报告生成器
 * 分析构建输出并生成优化建议报告
 */

interface BundleAnalysis {
  totalSize: number
  totalGzipSize: number
  totalBrotliSize: number
  chunks: Array<{
    name: string
    size: number
    gzipSize: number
    brotliSize: number
    modules: string[]
  }>
  recommendations: string[]
}

class BundleAnalyzer {
  /**
   * 分析bundle组成
   */
  async analyzeBundle(): Promise<BundleAnalysis> {
    // 这里应该读取rollup-plugin-visualizer生成的stats.html
    // 或者解析构建输出
    const analysis: BundleAnalysis = {
      totalSize: 0,
      totalGzipSize: 0,
      totalBrotliSize: 0,
      chunks: [],
      recommendations: [],
    }

    // 在实际实现中，这里应该：
    // 1. 读取dist/stats.html或stats.json
    // 2. 解析chunk信息
    // 3. 生成优化建议

    return analysis
  }

  /**
   * 生成优化建议
   */
  generateRecommendations(analysis: BundleAnalysis): string[] {
    const recommendations: string[] = []

    // 检查是否有过大的chunk（>500KB）
    analysis.chunks.forEach(chunk => {
      if (chunk.size > 500 * 1024) {
        recommendations.push(
          `Chunk "${chunk.name}" 过大 (${(chunk.size / 1024).toFixed(2)}KB)，建议进一步分割`
        )
      }
    })

    // 检查总大小
    if (analysis.totalSize > 1000 * 1024) {
      recommendations.push(
        `Bundle总大小过大 (${(analysis.totalSize / 1024).toFixed(2)}KB)，建议启用tree-shaking和代码分割`
      )
    }

    // 检查是否有重复依赖
    const moduleCounts = new Map<string, number>()
    analysis.chunks.forEach(chunk => {
      chunk.modules.forEach(module => {
        moduleCounts.set(module, (moduleCounts.get(module) || 0) + 1)
      })
    })

    moduleCounts.forEach((count, module) => {
      if (count > 1) {
        recommendations.push(
          `模块 "${module}" 出现在 ${count} 个chunk中，建议提取为公共chunk`
        )
      }
    })

    return recommendations
  }

  /**
   * 生成HTML报告
   */
  generateHTMLReport(analysis: BundleAnalysis): string {
    const recommendations = this.generateRecommendations(analysis)
    
    return `
<!DOCTYPE html>
<html>
<head>
  <title>Bundle分析报告</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    .chunk { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
    .recommendation { margin: 5px 0; padding: 5px; background: #fff3cd; }
  </style>
</head>
<body>
  <h1>Bundle分析报告</h1>
  <h2>总大小</h2>
  <p>原始: ${(analysis.totalSize / 1024).toFixed(2)}KB</p>
  <p>Gzip: ${(analysis.totalGzipSize / 1024).toFixed(2)}KB</p>
  <p>Brotli: ${(analysis.totalBrotliSize / 1024).toFixed(2)}KB</p>
  
  <h2>Chunks</h2>
  ${analysis.chunks.map(chunk => `
    <div class="chunk">
      <h3>${chunk.name}</h3>
      <p>大小: ${(chunk.size / 1024).toFixed(2)}KB</p>
      <p>Gzip: ${(chunk.gzipSize / 1024).toFixed(2)}KB</p>
      <p>Brotli: ${(chunk.brotliSize / 1024).toFixed(2)}KB</p>
    </div>
  `).join('')}
  
  <h2>优化建议</h2>
  ${recommendations.map(rec => `<div class="recommendation">${rec}</div>`).join('')}
</body>
</html>
    `.trim()
  }
}

export const bundleAnalyzer = new BundleAnalyzer()
export { BundleAnalyzer }
export type { BundleAnalysis }

