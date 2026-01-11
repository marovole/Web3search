import React, { Suspense } from 'react'
import type { RouteObject } from 'react-router-dom'
import { AdaptiveSkeleton } from '../components/ui/loading'

const AgentsPage = React.lazy(() => import('../pages/AgentsPage'))
const AgentChatPage = React.lazy(() => import('../pages/AgentChatPage'))
const AgentDashboardPage = React.lazy(() => import('../pages/AgentDashboardPage'))
const GitHubSearchPage = React.lazy(() => import('../pages/GitHubSearchPage'))

export const agentRoutes: RouteObject[] = [
  {
    path: '/agents',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
        <AgentsPage />
      </Suspense>
    ),
  },
  {
    path: '/github',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="search" />}>
        <GitHubSearchPage />
      </Suspense>
    ),
  },
  {
    path: '/agent-chat',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="chat" />}>
        <AgentChatPage />
      </Suspense>
    ),
  },
  {
    path: '/assistant',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="chat" />}>
        <AgentChatPage />
      </Suspense>
    ),
  },
  {
    path: '/agent-dashboard',
    element: (
      <Suspense fallback={<AdaptiveSkeleton pageType="settings" />}>
        <AgentDashboardPage />
      </Suspense>
    ),
  },
]
