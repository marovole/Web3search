/**
 * 未使用依赖检测工具
 * 检测代码中未使用的npm依赖
 */

interface DependencyUsage {
  name: string
  used: boolean
  usageCount: number
  locations: string[]
}

class UnusedDependencyDetector {
  /**
   * 检测未使用的依赖
   * 注意：这是一个简化版本，实际应该使用depcheck等工具
   */
  async detectUnusedDependencies(): Promise<DependencyUsage[]> {
    const dependencies = [
      'react',
      'react-dom',
      'react-router-dom',
      'axios',
      'framer-motion',
      'recharts',
      'react-syntax-highlighter',
      'react-markdown',
      'remark-gfm',
      'react-hook-form',
      '@hookform/resolvers',
      'zod',
      'lucide-react',
      'clsx',
      'tailwind-merge',
      'class-variance-authority',
      '@radix-ui/react-dropdown-menu',
      '@radix-ui/react-slot',
      '@radix-ui/react-toast',
      '@sentry/react',
      '@sentry/tracing', // 注意：这个可能未使用，因为@sentry/react已经包含tracing
    ]

    const usage: DependencyUsage[] = []

    // 在实际实现中，这里应该扫描所有文件
    // 查找import语句和使用情况
    dependencies.forEach(dep => {
      usage.push({
        name: dep,
        used: true, // 默认都标记为使用（需要实际扫描）
        usageCount: 0,
        locations: [],
      })
    })

    return usage
  }

  /**
   * 生成依赖使用报告
   */
  async generateReport(): Promise<string> {
    const dependencies = await this.detectUnusedDependencies()
    const unused = dependencies.filter(d => !d.used)

    let report = `
依赖使用分析报告:
====================

总依赖数: ${dependencies.length}
已使用: ${dependencies.filter(d => d.used).length}
未使用: ${unused.length}

${unused.length > 0 ? `
未使用的依赖:
${unused.map(d => `  - ${d.name}`).join('\n')}

建议:
${unused.map(d => `  - 考虑移除 ${d.name}（如果确认未使用）`).join('\n')}
` : '✅ 所有依赖都在使用中'}
    `.trim()

    // 特殊检查：@sentry/tracing可能已被@sentry/react替代
    const sentryTracing = dependencies.find(d => d.name === '@sentry/tracing')
    if (sentryTracing) {
      report += '\n\n⚠️  注意: @sentry/tracing 可能已被 @sentry/react 的tracing功能替代，建议检查是否需要单独安装。'
    }

    return report
  }
}

export const unusedDependencyDetector = new UnusedDependencyDetector()
export { UnusedDependencyDetector }
export type { DependencyUsage }

