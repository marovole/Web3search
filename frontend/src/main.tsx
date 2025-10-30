import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// 初始化资源预加载（关键资源）
import resourcePreloader from './utils/resourcePreloader'
resourcePreloader.initialize()

// 初始化组件优先级管理器
import componentPriorityManager from './utils/componentPriorityManager'
// 组件优先级管理器已自动初始化默认优先级

// 初始化监控和安全系统（延迟初始化，避免阻塞首屏）
import { monitoring } from './services/monitoring'
import { security } from './services/security'

// 性能测试工具（开发环境）
import performanceTester from './utils/performanceTester'
import performanceBaselineManager from './utils/performanceBaselineManager'

// 在空闲时初始化监控系统，避免阻塞首屏渲染
const initializeServices = () => {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(async () => {
      try {
        await Promise.all([
          monitoring.initialize(),
          security.initialize({
            csp: {
              enabled: true,
              reportOnly: process.env.NODE_ENV === 'development'
            },
            xss: {
              enabled: true
            },
            dependencies: {
              enabled: true,
              autoScan: true
            },
            headers: {
              enabled: true,
              hsts: true
            },
            monitoring: {
              enabled: true,
              reportViolations: true
            }
          })
        ])
      } catch (error) {
        console.error('服务初始化失败:', error)
      }
    }, { timeout: 5000 })
  } else {
    // 降级方案：使用setTimeout延迟初始化
    setTimeout(async () => {
      try {
        await Promise.all([
          monitoring.initialize(),
          security.initialize({
            csp: {
              enabled: true,
              reportOnly: process.env.NODE_ENV === 'development'
            },
            xss: {
              enabled: true
            },
            dependencies: {
              enabled: true,
              autoScan: true
            },
            headers: {
              enabled: true,
              hsts: true
            },
            monitoring: {
              enabled: true,
              reportViolations: true
            }
          })
        ])
      } catch (error) {
        console.error('服务初始化失败:', error)
      }
    }, 0)
  }
}

// 立即初始化服务，不等待
initializeServices()

// 开发环境：性能测试和基准线建立
if (import.meta.env.DEV) {
  window.addEventListener('load', () => {
    setTimeout(async () => {
      console.log('🧪 开发环境：运行性能测试...')
      
      // 建立性能基准线
      await performanceBaselineManager.establishBaseline()
      
      // 运行性能测试
      const validation = await performanceTester.validateAcceptanceCriteria()
      console.log(validation.summary)
      
      // 生成Bundle报告
      const bundleReportGenerator = (await import('./utils/bundleReportGenerator')).bundleReportGenerator
      await bundleReportGenerator.saveReport()
      
      // 运行完整验证
      const performanceValidator = (await import('./utils/performanceValidator')).performanceValidator
      await performanceValidator.runFullValidation()
      
      // 测试离线功能
      const offlineFunctionalityTester = (await import('./utils/offlineFunctionalityTester')).offlineFunctionalityTester
      await offlineFunctionalityTester.runAllTests()
    }, 10000) // 10秒后运行测试
  })
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
