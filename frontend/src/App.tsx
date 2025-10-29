import React, { Suspense, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { cn } from './lib/utils'
import ErrorBoundary from './components/Error/ErrorBoundary'
import OfflineIndicator from './components/Network/OfflineIndicator'
import { ToastProvider } from './components/ui/toast'
import { ThemeProvider } from './components/theme-provider'
import { KeyboardShortcutsProvider } from './contexts/KeyboardShortcutsContext'
import { UserPreferencesProvider } from './contexts/UserPreferencesContext'
import { SearchHistoryProvider } from './contexts/SearchHistoryContext'
import { GlobalSearchDialog } from './components/Search/GlobalSearchDialog'
import { useSidebar } from './hooks/useSidebar'
import { useSmartPreload } from './hooks/usePreloadRoutes'
import { useServiceWorker } from './hooks/useServiceWorker'
import { useKeyboardShortcutsContext } from './contexts/KeyboardShortcutsContext'
import Sidebar from './components/Layout/Sidebar'
import { initSentry, addBreadcrumb, setContext } from './services/sentry'
import performanceMonitor from './services/performance'
import { PageLoading, ChatLoading, ReportLoading } from './components/Loading/PageLoading'

// 懒加载页面组件
const ChatPage = React.lazy(() => import('./pages/ChatPage'))
const SharedReportPage = React.lazy(() => import('./pages/SharedReportPage'))
const HistoryPage = React.lazy(() => import('./pages/HistoryPage'))
const WatchlistPage = React.lazy(() => import('./pages/WatchlistPage'))
const SettingsPage = React.lazy(() => import('./pages/SettingsPage'))
const SearchPage = React.lazy(() => import('./pages/SearchPage'))

// Layout component that includes sidebar
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation()
  const { isOpen, isMobile, toggle } = useSidebar()
  const { registerShortcut } = useKeyboardShortcutsContext()
  const [searchOpen, setSearchOpen] = useState(false)

  // 注册全局搜索快捷键
  React.useEffect(() => {
    registerShortcut({
      key: '/',
      handler: () => setSearchOpen(true),
      description: '打开全局搜索',
      enabled: true
    })
  }, [registerShortcut])

  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      <Sidebar
        isOpen={isOpen}
        onToggle={toggle}
        isMobile={isMobile}
        currentPath={location.pathname}
      />

      <div className={cn(
        "transition-all duration-300 ease-in-out",
        // Add padding for desktop sidebar
        !isMobile && "md:ml-72 lg:ml-80"
      )}>
        <div className="relative flex min-h-screen flex-col">
          <main className="flex-1 overflow-hidden">
            {children}
          </main>
        </div>
      </div>

      {/* 全局搜索对话框 */}
      <GlobalSearchDialog
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
      />
    </div>
  )
}

function App() {
  // 启用智能预加载
  useSmartPreload()

  // Service Worker管理
  const { updateAvailable, offline, activateUpdate } = useServiceWorker()

  // 初始化监控服务
  React.useEffect(() => {
    // 初始化Sentry错误监控
    initSentry()

    // 设置应用上下文信息
    setContext('app', {
      version: process.env.npm_package_version || '1.0.0',
      name: 'Web3search Frontend',
      buildTime: new Date().toISOString()
    })

    // 添加面包屑导航
    addBreadcrumb({
      message: '应用启动',
      category: 'navigation',
      level: 'info',
      data: {
        userAgent: navigator.userAgent,
        url: window.location.href
      }
    })

    // 性能监控已在性能监控服务中自动初始化

    // 清理函数
    return () => {
      // 如果需要，可以在这里清理监控
      performanceMonitor.dispose()
    }
  }, [])

  return (
    <UserPreferencesProvider>
      <SearchHistoryProvider>
        <KeyboardShortcutsProvider>
          <Router>
            <ThemeProvider defaultTheme="system" storageKey="web3search-theme">
              <ToastProvider>
                <OfflineIndicator />
                <ErrorBoundary>
                  <Routes>
                    <Route path="/*" element={
                      <AppLayout>
                        <Routes>
                          <Route path="/" element={
                            <Suspense fallback={<ChatLoading />}>
                              <ChatPage />
                            </Suspense>
                          } />
                          <Route path="/shared/:shareToken" element={
                            <Suspense fallback={<ReportLoading />}>
                              <SharedReportPage />
                            </Suspense>
                          } />
                          <Route path="/history" element={
                            <Suspense fallback={<PageLoading message="加载历史记录..." />}>
                              <HistoryPage />
                            </Suspense>
                          } />
                          <Route path="/watchlist" element={
                            <Suspense fallback={<PageLoading message="加载监控列表..." />}>
                              <WatchlistPage />
                            </Suspense>
                          } />
                          <Route path="/search" element={
                            <Suspense fallback={<PageLoading message="加载搜索..." />}>
                              <SearchPage />
                            </Suspense>
                          } />
                          <Route path="/settings" element={
                            <Suspense fallback={<PageLoading message="加载设置..." />}>
                              <SettingsPage />
                            </Suspense>
                          } />
                        </Routes>
                      </AppLayout>
                    } />
                  </Routes>
                </ErrorBoundary>
              </ToastProvider>
            </ThemeProvider>
          </Router>
        </KeyboardShortcutsProvider>
      </SearchHistoryProvider>
    </UserPreferencesProvider>
  )
}

export default App
