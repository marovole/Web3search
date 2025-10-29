import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// 初始化监控和安全系统（延迟初始化，避免阻塞首屏）
import { monitoring } from './services/monitoring'
import { security } from './services/security'

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

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
