import './index.css'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

const root = document.getElementById('root')

if (root) {
  const rootElement = ReactDOM.createRoot(root)
  rootElement.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  )
}

// 延迟初始化监控和安全服务
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => {
    initializeServices()
  })
} else {
  setTimeout(() => {
    initializeServices()
  }, 2000)
}

async function initializeServices() {
  try {
    const { monitoring } = await import('./services/monitoring')
    const { security } = await import('./services/security')

    await Promise.all([
      monitoring.initialize(),
      security.initialize({
        csp: { enabled: true, reportOnly: process.env.NODE_ENV === 'development' },
        xss: { enabled: true },
        dependencies: { enabled: true, autoScan: true },
        headers: { enabled: true, hsts: true },
        monitoring: { enabled: true, reportViolations: true }
      })
    ])
  } catch (error) {
    console.error('服务初始化失败:', error)
  }
}

// Service Worker注册
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}
