#!/usr/bin/env node
/**
 * 前端性能测试验证脚本
 * 验证Core Web Vitals、Bundle大小、加载时间等性能指标
 */

import { execSync } from 'child_process'
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'

interface PerformanceMetrics {
  fcp: number // First Contentful Paint
  lcp: number // Largest Contentful Paint
  fid: number // First Input Delay
  cls: number // Cumulative Layout Shift
  loadTime: number // 页面加载时间
  bundleSize: number // Bundle大小 (KB)
  cacheHitRate: number // 缓存命中率
}

interface PerformanceThresholds {
  fcp: number
  lcp: number
  fid: number
  cls: number
  loadTime: number
  bundleSize: number
  cacheHitRate: number
}

class PerformanceValidator {
  private thresholds: PerformanceThresholds = {
    fcp: 1800, // 1.8秒
    lcp: 2500, // 2.5秒
    fid: 100, // 100ms
    cls: 0.1, // 0.1
    loadTime: 2000, // 2秒
    bundleSize: 500, // 500KB
    cacheHitRate: 80, // 80%
  }

  /**
   * 验证Bundle大小
   */
  validateBundleSize(): { passed: boolean; size: number; threshold: number; message: string } {
    const distPath = join(process.cwd(), 'frontend/dist')
    
    if (!existsSync(distPath)) {
      return {
        passed: false,
        size: 0,
        threshold: this.thresholds.bundleSize,
        message: '❌ dist目录不存在，请先运行 npm run build'
      }
    }

    try {
      // 计算所有JS文件的总大小
      const result = execSync(
        `find ${distPath} -name "*.js" -type f -exec stat -f%z {} \\; | awk '{s+=$1} END {print s}'`,
        { encoding: 'utf-8', cwd: join(process.cwd(), 'frontend') }
      )
      
      const totalSizeKB = parseInt(result.trim()) / 1024
      const passed = totalSizeKB <= this.thresholds.bundleSize
      const reductionTarget = totalSizeKB * 0.7 // 目标减少30%

      return {
        passed,
        size: totalSizeKB,
        threshold: this.thresholds.bundleSize,
        message: passed
          ? `✅ Bundle大小: ${totalSizeKB.toFixed(2)}KB (目标: ${this.thresholds.bundleSize}KB)`
          : `❌ Bundle大小: ${totalSizeKB.toFixed(2)}KB (超过目标: ${this.thresholds.bundleSize}KB)，建议减少到 ${reductionTarget.toFixed(2)}KB`
      }
    } catch (error) {
      return {
        passed: false,
        size: 0,
        threshold: this.thresholds.bundleSize,
        message: `❌ 无法计算Bundle大小: ${error}`
      }
    }
  }

  /**
   * 验证构建配置
   */
  validateBuildConfig(): { passed: boolean; checks: string[] } {
    const configPath = join(process.cwd(), 'frontend/vite.config.ts')
    const config = readFileSync(configPath, 'utf-8')
    
    const checks: string[] = []
    let passed = true

    // 检查代码分割
    if (config.includes('manualChunks')) {
      checks.push('✅ 代码分割配置已启用')
    } else {
      checks.push('❌ 代码分割配置缺失')
      passed = false
    }

    // 检查CSS代码分割
    if (config.includes('cssCodeSplit: true')) {
      checks.push('✅ CSS代码分割已启用')
    } else {
      checks.push('⚠️  CSS代码分割未启用')
    }

    // 检查压缩配置
    if (config.includes('minify')) {
      checks.push('✅ 代码压缩已配置')
    } else {
      checks.push('⚠️  代码压缩未配置')
    }

    // 检查Bundle分析工具
    if (config.includes('visualizer')) {
      checks.push('✅ Bundle分析工具已集成')
    } else {
      checks.push('⚠️  Bundle分析工具未集成')
    }

    return { passed, checks }
  }

  /**
   * 验证Service Worker缓存
   */
  validateServiceWorker(): { passed: boolean; message: string } {
    const swPath = join(process.cwd(), 'frontend/public/sw.js')
    
    if (!existsSync(swPath)) {
      return {
        passed: false,
        message: '❌ Service Worker文件不存在 (frontend/public/sw.js)'
      }
    }

    const swContent = readFileSync(swPath, 'utf-8')
    
    const hasCache = swContent.includes('STATIC_CACHE') || swContent.includes('CACHE')
    const hasOffline = swContent.includes('offline') || swContent.includes('OFFLINE')

    if (hasCache && hasOffline) {
      return {
        passed: true,
        message: '✅ Service Worker缓存策略已配置'
      }
    }

    return {
      passed: false,
      message: '⚠️  Service Worker缓存策略不完整'
    }
  }

  /**
   * 生成性能验证报告
   */
  generateReport(): void {
    console.log('\n📊 前端性能验证报告\n')
    console.log('=' .repeat(60))

    // 验证Bundle大小
    console.log('\n1. Bundle大小验证:')
    const bundleResult = this.validateBundleSize()
    console.log(`   ${bundleResult.message}`)

    // 验证构建配置
    console.log('\n2. 构建配置验证:')
    const configResult = this.validateBuildConfig()
    configResult.checks.forEach(check => console.log(`   ${check}`))

    // 验证Service Worker
    console.log('\n3. Service Worker缓存验证:')
    const swResult = this.validateServiceWorker()
    console.log(`   ${swResult.message}`)

    // 性能指标说明
    console.log('\n4. 性能指标说明:')
    console.log('   ⚠️  Core Web Vitals需要在浏览器中实际测试')
    console.log('   建议使用以下工具验证:')
    console.log('   - Lighthouse CLI: npx lighthouse http://localhost:3000 --view')
    console.log('   - Chrome DevTools: Performance面板')
    console.log('   - Web Vitals扩展: Chrome扩展程序')

    // 总结
    console.log('\n' + '='.repeat(60))
    const allPassed = bundleResult.passed && configResult.passed && swResult.passed
    
    if (allPassed) {
      console.log('\n✅ 所有静态验证通过！')
      console.log('💡 建议运行生产环境构建并实际测试性能指标')
    } else {
      console.log('\n⚠️  部分验证未通过，请检查上述问题')
    }

    console.log('\n📋 性能目标:')
    console.log(`   - 首屏加载时间: < ${this.thresholds.loadTime}ms`)
    console.log(`   - Bundle大小: < ${this.thresholds.bundleSize}KB`)
    console.log(`   - LCP: < ${this.thresholds.lcp}ms`)
    console.log(`   - FID: < ${this.thresholds.fid}ms`)
    console.log(`   - CLS: < ${this.thresholds.cls}`)
    console.log(`   - 缓存命中率: > ${this.thresholds.cacheHitRate}%`)
  }
}

// 运行验证
if (require.main === module) {
  const validator = new PerformanceValidator()
  validator.generateReport()
}

export { PerformanceValidator }

