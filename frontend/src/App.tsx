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
import { ConvexProvider } from "convex/react";
import { convex } from "./lib/convex";

// 懒加载页面组件
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
      <Sidebar
        isOpen={isOpen}
        onToggle={toggle}
        isMobile={isMobile}
        currentPath={location.pathname}
      />

      <div className={cn(
        "transition-all duration-200 ease-out min-h-screen flex flex-col",
        !isMobile && "md:ml-64"
      )}>
        <main className="flex-1 relative h-screen">
          <div className="h-full relative z-0">
            {children}
          </div>
        </main>
      </div>

      <GlobalSearchDialog
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
      />
    </div>
  )
}

function App() {
  const uxConfig = { features: {} as Record<string, boolean> }

  React.useEffect(() => {
    const initMonitoring = async () => {
      try {
        const { initSentry, setContext, trackCoreWebVitals, trackPageLoad, trackResourceLoading } = await import('./services/sentry-lite')
        initSentry()
        setContext('app', {
          version: import.meta.env.VITE_APP_VERSION || '1.0.0',
          name: 'Web3search Frontend',
          buildTime: new Date().toISOString(),
          uxEnhancements: uxConfig
        })
        trackCoreWebVitals()
        trackPageLoad()
        trackResourceLoading()
      } catch (error) {
        logger.error('初始化监控失败:', error)
      }
    }
    initMonitoring()
  }, [uxConfig])

  return (
    <ErrorBoundary>
      <ConvexProvider client={convex}>
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
                            <Route path="/*" element={
                              <AppLayout>
                                <Routes>
                                  <Route path="/" element={<Suspense fallback={<AdaptiveSkeleton pageType="chat" />}><ChatPage /></Suspense>} />
                                  <Route path="/chat" element={<Suspense fallback={<AdaptiveSkeleton pageType="chat" />}><ChatPage /></Suspense>} />
                                  <Route path="/shared/:shareToken" element={<Suspense fallback={<AdaptiveSkeleton pageType="report" />}><SharedReportPage /></Suspense>} />
                                  <Route path="/history" element={<Suspense fallback={<AdaptiveSkeleton pageType="history" />}><HistoryPage /></Suspense>} />
                                  <Route path="/watchlist" element={<Suspense fallback={<AdaptiveSkeleton pageType="search" />}><WatchlistPage /></Suspense>} />
                                  <Route path="/search" element={<Suspense fallback={<AdaptiveSkeleton pageType="search" />}><SearchPage /></Suspense>} />
                                  <Route path="/github" element={<Suspense fallback={<AdaptiveSkeleton pageType="search" />}><GitHubSearchPage /></Suspense>} />
                                  <Route path="/agents" element={<Suspense fallback={<AdaptiveSkeleton pageType="settings" />}><AgentsPage /></Suspense>} />
                                  <Route path="/upgrade" element={<Suspense fallback={<AdaptiveSkeleton pageType="settings" />}><UpgradePage /></Suspense>} />
                                  <Route path="/notifications" element={<Suspense fallback={<AdaptiveSkeleton pageType="settings" />}><NotificationsPage /></Suspense>} />
                                  <Route path="/settings" element={<Suspense fallback={<AdaptiveSkeleton pageType="settings" />}><SettingsPage /></Suspense>} />
                                  <Route path="/reports" element={<Suspense fallback={<AdaptiveSkeleton pageType="report" />}><ReportsPage /></Suspense>} />
                                  <Route path="/analytics" element={<Suspense fallback={<AdaptiveSkeleton pageType="search" />}><AnalyticsPage /></Suspense>} />
                                  <Route path="/holdings" element={<Suspense fallback={<AdaptiveSkeleton pageType="search" />}><HoldingsPage /></Suspense>} />
                                  <Route path="/portfolio" element={<Suspense fallback={<AdaptiveSkeleton pageType="search" />}><HoldingsPage /></Suspense>} />
                                  <Route path="/recommendations" element={<Suspense fallback={<AdaptiveSkeleton pageType="search" />}><RecommendationsPage /></Suspense>} />
                                  <Route path="/discover" element={<Suspense fallback={<AdaptiveSkeleton pageType="search" />}><RecommendationsPage /></Suspense>} />
                                  <Route path="/agent-chat" element={<Suspense fallback={<AdaptiveSkeleton pageType="chat" />}><AgentChatPage /></Suspense>} />
                                  <Route path="/assistant" element={<Suspense fallback={<AdaptiveSkeleton pageType="chat" />}><AgentChatPage /></Suspense>} />
                                  <Route path="/agent-dashboard" element={<Suspense fallback={<AdaptiveSkeleton pageType="settings" />}><AgentDashboardPage /></Suspense>} />
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
      </ConvexProvider>
    </ErrorBoundary>
  )
}

export default App
