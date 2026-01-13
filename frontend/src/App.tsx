import React, { Suspense, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { logger } from '@/utils/logger'
import ErrorBoundary from './components/Error/ErrorBoundary'
import OfflineIndicator from './components/Network/OfflineIndicator'
import { ToastProvider } from './components/ui/toast'
import { ThemeProvider } from './components/theme-provider'
import { LoadingProvider, AdaptiveSkeleton } from './components/ui/loading'
import { KeyboardShortcutsProvider } from './contexts/KeyboardShortcutsContext'
import { UserPreferencesProvider } from './contexts/UserPreferencesContext'
import { SearchHistoryProvider } from './contexts/SearchHistoryContext'
import { SearchFavoritesProvider } from './contexts/SearchFavoritesContext'
import { AuthProvider } from './contexts/AuthContext'
import { GlobalSearchDialog } from './components/Search/GlobalSearchDialog'
import { useSidebar } from './hooks/useSidebar'
import { useKeyboardShortcutsContext } from './contexts/KeyboardShortcutsContext'
import Sidebar from './components/Layout/Sidebar'

// 懒加载页面组件（已修复嵌套懒加载问题）
const ChatPage = React.lazy(() => import('./pages/ChatPage'))
const SharedReportPage = React.lazy(() => import('./pages/SharedReportPage'))
const HistoryPage = React.lazy(() => import('./pages/HistoryPage'))
const WatchlistPage = React.lazy(() => import('./pages/WatchlistPage'))
const SettingsPage = React.lazy(() => import('./pages/SettingsPage'))
const SearchPage = React.lazy(() => import('./pages/SearchPage'))
const GitHubSearchPage = React.lazy(() => import('./pages/GitHubSearchPage'))
const AgentsPage = React.lazy(() => import('./pages/AgentsPage'))
const UpgradePage = React.lazy(() => import('./pages/UpgradePage'))
const NotificationsPage = React.lazy(() => import('./pages/NotificationsPage'))
const ReportsPage = React.lazy(() => import('./pages/ReportsPage'))
const AnalyticsPage = React.lazy(() => import('./pages/AnalyticsPage'))
const HoldingsPage = React.lazy(() => import('./pages/HoldingsPage'))
const RecommendationsPage = React.lazy(() => import('./pages/RecommendationsPage'))
const AgentChatPage = React.lazy(() => import('./pages/AgentChatPage'))
const AgentDashboardPage = React.lazy(() => import('./pages/AgentDashboardPage'))

// 懒加载认证页面组件
const LoginPage = React.lazy(() => import('./pages/Auth/LoginPage'))
const RegisterPage = React.lazy(() => import('./pages/Auth/RegisterPage'))
const ForgotPasswordPage = React.lazy(() => import('./pages/Auth/ForgotPasswordPage'))
const ResetPasswordPage = React.lazy(() => import('./pages/Auth/ResetPasswordPage'))

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
    <div className="min-h-screen font-sans antialiased text-foreground">
      {/* Background is handled in index.css body, but we can add a subtle overlay if needed */}

      <Sidebar
        isOpen={isOpen}
        onToggle={toggle}
        isMobile={isMobile}
        currentPath={location.pathname}
      />

      <div className={cn(
        "transition-all duration-200 ease-out min-h-screen flex flex-col",
        // Add margin for desktop sidebar (w-64)
        !isMobile && "md:ml-64"
      )}>
        <main className="flex-1 relative h-screen">
          <div className="h-full relative z-0">
            {children}
          </div>
        </main>
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
  // UX enhancement config
  const uxConfig = { features: {} as Record<string, boolean> }

  // 初始化监控服务（延迟导入，避免React初始化冲突）
  React.useEffect(() => {
    const initMonitoring = async () => {
      try {
        const { initSentry, addBreadcrumb, setContext, trackCoreWebVitals, trackPageLoad, trackResourceLoading } = await import('./services/sentry-lite')

        // 初始化Sentry错误监控和RUM
        initSentry()

        // 设置应用上下文信息
        setContext('app', {
          version: import.meta.env.VITE_APP_VERSION || '1.0.0',
          name: 'Web3search Frontend',
          buildTime: new Date().toISOString(),
          uxEnhancements: uxConfig
        })

        // 添加面包屑导航
        addBreadcrumb({
          message: '应用启动',
          category: 'navigation',
          level: 'info',
          data: {
            userAgent: navigator.userAgent,
            url: window.location.href,
            uxFeatures: uxConfig.features
          }
        })

        // 初始化RUM监控
        trackCoreWebVitals()
        trackPageLoad()
        trackResourceLoading()
      } catch (error) {
        logger.error('初始化监控失败:', error)
      }
    }

    initMonitoring()

    // 清理函数
    return () => {
      // 清理监控（如需要）
    }
  }, [uxConfig])

  return (
    <ErrorBoundary>
      <AuthProvider>
        <LoadingProvider>
          <UserPreferencesProvider>
            <SearchHistoryProvider>
              <SearchFavoritesProvider>
                <KeyboardShortcutsProvider>
                  <Router>
                    <ThemeProvider defaultTheme="dark" storageKey="web3search-theme">
                      <ToastProvider>
                        <OfflineIndicator />
                        <Routes>
                          {/* 认证路由 - 不显示侧边栏 */}
                          <Route path="/auth/login" element={
                            <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
                              <LoginPage />
                            </Suspense>
                          } />
                          <Route path="/auth/register" element={
                            <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
                              <RegisterPage />
                            </Suspense>
                          } />
                          <Route path="/auth/forgot-password" element={
                            <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
                              <ForgotPasswordPage />
                            </Suspense>
                          } />
                          <Route path="/auth/reset-password" element={
                            <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
                              <ResetPasswordPage />
                            </Suspense>
                          } />
                          {/* 应用路由 - 显示侧边栏 */}
                          <Route path="/*" element={
                            <AppLayout>
                              <Routes>
                                <Route path="/" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="chat" />}>
                                    <ChatPage />
                                  </Suspense>
                                } />
                                <Route path="/chat" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="chat" />}>
                                    <ChatPage />
                                  </Suspense>
                                } />
                                <Route path="/shared/:shareToken" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="report" />}>
                                    <SharedReportPage />
                                  </Suspense>
                                } />
                                <Route path="/history" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="history" />}>
                                    <HistoryPage />
                                  </Suspense>
                                } />
                                <Route path="/watchlist" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
                                    <WatchlistPage />
                                  </Suspense>
                                } />
                                <Route path="/search" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
                                    <SearchPage />
                                  </Suspense>
                                } />
                                <Route path="/github" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
                                    <GitHubSearchPage />
                                  </Suspense>
                                } />
                                <Route path="/agents" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
                                    <AgentsPage />
                                  </Suspense>
                                } />
                                <Route path="/upgrade" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
                                    <UpgradePage />
                                  </Suspense>
                                } />
                                <Route path="/notifications" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
                                    <NotificationsPage />
                                  </Suspense>
                                } />
                                <Route path="/settings" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
                                    <SettingsPage />
                                  </Suspense>
                                } />
                                <Route path="/reports" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="report" />}>
                                    <ReportsPage />
                                  </Suspense>
                                } />
                                <Route path="/analytics" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
                                    <AnalyticsPage />
                                  </Suspense>
                                } />
                                <Route path="/holdings" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
                                    <HoldingsPage />
                                  </Suspense>
                                } />
                                <Route path="/portfolio" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
                                    <HoldingsPage />
                                  </Suspense>
                                } />
                                <Route path="/recommendations" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
                                    <RecommendationsPage />
                                  </Suspense>
                                } />
                                <Route path="/discover" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
                                    <RecommendationsPage />
                                  </Suspense>
                                } />
                                <Route path="/agent-chat" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="chat" />}>
                                    <AgentChatPage />
                                  </Suspense>
                                } />
                                <Route path="/assistant" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="chat" />}>
                                    <AgentChatPage />
                                  </Suspense>
                                } />
                                <Route path="/agent-dashboard" element={
                                  <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
                                    <AgentDashboardPage />
                                  </Suspense>
                                } />
                              </Routes>
                            </AppLayout>
                          } />
                        </Routes>
                      </ToastProvider>
                    </ThemeProvider>
                  </Router>
                </KeyboardShortcutsProvider>
              </SearchFavoritesProvider>
            </SearchHistoryProvider>
          </UserPreferencesProvider>
        </LoadingProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
