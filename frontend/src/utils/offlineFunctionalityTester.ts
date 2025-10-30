/**
 * 离线功能测试工具
 * 测试Service Worker和离线功能
 */

import { useServiceWorker } from '../hooks/useServiceWorker'
import { useOfflineStatus } from '../hooks/useServiceWorker'

class OfflineFunctionalityTester {
  /**
   * 测试Service Worker注册
   */
  async testServiceWorkerRegistration(): Promise<{
    passed: boolean
    message: string
    details: any
  }> {
    if (!('serviceWorker' in navigator)) {
      return {
        passed: false,
        message: '❌ Service Worker不支持（浏览器不支持）',
        details: {},
      }
    }

    try {
      const registration = await navigator.serviceWorker.getRegistration()
      
      if (registration) {
        return {
          passed: true,
          message: '✅ Service Worker已注册',
          details: {
            scope: registration.scope,
            active: !!registration.active,
            installing: !!registration.installing,
            waiting: !!registration.waiting,
          },
        }
      } else {
        return {
          passed: false,
          message: '❌ Service Worker未注册',
          details: {},
        }
      }
    } catch (error) {
      return {
        passed: false,
        message: `❌ Service Worker注册测试失败: ${error}`,
        details: { error },
      }
    }
  }

  /**
   * 测试缓存API
   */
  async testCacheAPI(): Promise<{
    passed: boolean
    message: string
    details: any
  }> {
    if (!('caches' in window)) {
      return {
        passed: false,
        message: '❌ Cache API不支持（浏览器不支持）',
        details: {},
      }
    }

    try {
      const cacheNames = await caches.keys()
      const cacheStats = []

      for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName)
        const keys = await cache.keys()
        cacheStats.push({
          name: cacheName,
          size: keys.length,
        })
      }

      return {
        passed: true,
        message: `✅ Cache API可用，发现 ${cacheNames.length} 个缓存`,
        details: {
          cacheCount: cacheNames.length,
          caches: cacheStats,
        },
      }
    } catch (error) {
      return {
        passed: false,
        message: `❌ Cache API测试失败: ${error}`,
        details: { error },
      }
    }
  }

  /**
   * 测试离线检测
   */
  testOfflineDetection(): {
    passed: boolean
    message: string
    details: any
  } {
    const isOnline = navigator.onLine

    return {
      passed: true,
      message: isOnline ? '✅ 当前在线' : '⚠️  当前离线',
      details: {
        online: isOnline,
        connectionType: (navigator as any).connection?.effectiveType || 'unknown',
      },
    }
  }

  /**
   * 测试离线页面访问
   */
  async testOfflinePageAccess(): Promise<{
    passed: boolean
    message: string
    details: any
  }> {
    try {
      // 尝试访问离线页面
      const response = await fetch('/offline.html', { cache: 'force-cache' })
      
      if (response.ok) {
        return {
          passed: true,
          message: '✅ 离线页面可访问',
          details: {
            status: response.status,
            cached: response.headers.get('x-cache') === 'HIT',
          },
        }
      } else {
        return {
          passed: false,
          message: `❌ 离线页面访问失败: ${response.status}`,
          details: {
            status: response.status,
          },
        }
      }
    } catch (error) {
      return {
        passed: false,
        message: `❌ 离线页面访问失败: ${error}`,
        details: { error },
      }
    }
  }

  /**
   * 运行所有离线功能测试
   */
  async runAllTests(): Promise<{
    allPassed: boolean
    results: Array<{ testName: string; passed: boolean; message: string; details: any }>
    summary: string
  }> {
    console.log('🧪 开始离线功能测试...')

    const results = [
      {
        testName: 'Service Worker注册',
        ...await this.testServiceWorkerRegistration(),
      },
      {
        testName: 'Cache API',
        ...await this.testCacheAPI(),
      },
      {
        testName: '离线检测',
        ...this.testOfflineDetection(),
      },
      {
        testName: '离线页面访问',
        ...await this.testOfflinePageAccess(),
      },
    ]

    const allPassed = results.every(r => r.passed)

    const summary = `
离线功能测试结果:
${results.map(r => `  ${r.testName}: ${r.message}`).join('\n')}

总体结果: ${allPassed ? '✅ 通过' : '⚠️  部分失败'}
    `.trim()

    console.log(summary)

    return {
      allPassed,
      results,
      summary,
    }
  }
}

export const offlineFunctionalityTester = new OfflineFunctionalityTester()
export { OfflineFunctionalityTester }

