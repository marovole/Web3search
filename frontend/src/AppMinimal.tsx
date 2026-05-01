/**
 * Minimal dev/debug router shell — production uses App.tsx.
 */
import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './components/theme-provider'
import { ToastProvider } from './components/ui/toast'
import { LoadingProvider } from './components/ui/loading'
import { KeyboardShortcutsProvider, useKeyboardShortcutsContext } from './contexts/KeyboardShortcutsContext'
import { UserPreferencesProvider } from './contexts/UserPreferencesContext'
import { SearchHistoryProvider } from './contexts/SearchHistoryContext'
import ErrorBoundary from './components/Error/ErrorBoundary'
import OfflineIndicator from './components/Network/OfflineIndicator'
import Sidebar from './components/Layout/Sidebar'
import { GlobalSearchDialog } from './components/Search/GlobalSearchDialog'
import { useSidebar } from './hooks/useSidebar'
import { useSmartPreload } from './hooks/usePreloadRoutes'
import { cn } from '@/lib/utils'

// Test adding components one by one
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

function AppContent() {
  // 启用智能预加载
  useSmartPreload()

  // Service Worker管理
  // const { updateAvailable: _updateAvailable, offline: _offline, activateUpdate: _activateUpdate } = useServiceWorker()

  return (
    <Routes>
      <Route path="/*" element={
        <AppLayout>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            backgroundColor: '#f0f0f0',
            fontSize: '24px'
          }}>
            应用已加载 - React working! 🎉
          </div>
        </AppLayout>
      } />
    </Routes>
  )
}

export default function AppMinimal() {
  return (
    <AuthProvider>
      <LoadingProvider>
        <UserPreferencesProvider>
          <SearchHistoryProvider>
            <KeyboardShortcutsProvider>
              <ThemeProvider>
                <ToastProvider>
                  <Router>
                    <OfflineIndicator />
                    <ErrorBoundary>
                      <AppContent />
                    </ErrorBoundary>
                  </Router>
                </ToastProvider>
              </ThemeProvider>
            </KeyboardShortcutsProvider>
          </SearchHistoryProvider>
        </UserPreferencesProvider>
      </LoadingProvider>
    </AuthProvider>
  )
}
