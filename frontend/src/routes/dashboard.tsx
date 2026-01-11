import React, { Suspense } from 'react'
import type { RouteObject } from 'react-router-dom'
import { AdaptiveSkeleton } from '../components/ui/loading'

const ChatPage = React.lazy(() => import('../pages/ChatPage'))
const SharedReportPage = React.lazy(() => import('../pages/SharedReportPage'))
const HistoryPage = React.lazy(() => import('../pages/HistoryPage'))
const WatchlistPage = React.lazy(() => import('../pages/WatchlistPage'))
const SettingsPage = React.lazy(() => import('../pages/SettingsPage'))
const SearchPage = React.lazy(() => import('../pages/SearchPage'))
const ReportsPage = React.lazy(() => import('../pages/ReportsPage'))
const AnalyticsPage = React.lazy(() => import('../pages/AnalyticsPage'))
const HoldingsPage = React.lazy(() => import('../pages/HoldingsPage'))
const RecommendationsPage = React.lazy(() => import('../pages/RecommendationsPage'))
const UpgradePage = React.lazy(() => import('../pages/UpgradePage'))
const NotificationsPage = React.lazy(() => import('../pages/NotificationsPage'))

export const dashboardRoutes: RouteObject[] = [
  {
    path: '/',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="chat" />}>
        <ChatPage />
      </Suspense>
    ),
  },
  {
    path: '/chat',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="chat" />}>
        <ChatPage />
      </Suspense>
    ),
  },
  {
    path: '/shared/:shareToken',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="report" />}>
        <SharedReportPage />
      </Suspense>
    ),
  },
  {
    path: '/history',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="history" />}>
        <HistoryPage />
      </Suspense>
    ),
  },
  {
    path: '/watchlist',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
        <WatchlistPage />
      </Suspense>
    ),
  },
  {
    path: '/search',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
        <SearchPage />
      </Suspense>
    ),
  },
  {
    path: '/reports',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="report" />}>
        <ReportsPage />
      </Suspense>
    ),
  },
  {
    path: '/analytics',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
        <AnalyticsPage />
      </Suspense>
    ),
  },
  {
    path: '/holdings',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
        <HoldingsPage />
      </Suspense>
    ),
  },
  {
    path: '/portfolio',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
        <HoldingsPage />
      </Suspense>
    ),
  },
  {
    path: '/recommendations',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
        <RecommendationsPage />
      </Suspense>
    ),
  },
  {
    path: '/discover',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
        <RecommendationsPage />
      </Suspense>
    ),
  },
  {
    path: '/upgrade',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
        <UpgradePage />
      </Suspense>
    ),
  },
  {
    path: '/notifications',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
        <NotificationsPage />
      </Suspense>
    ),
  },
  {
    path: '/settings',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
        <SettingsPage />
      </Suspense>
    ),
  },
]
