import { describe, expect, it, vi, beforeEach } from 'vitest'
import type { Env } from '../../src/types/env'

const mockProcessPriceAlerts = vi.fn()
const mockProcessRiskMonitor = vi.fn()
const mockProcessNewsBrief = vi.fn()

vi.mock('../../src/lib/price-alert-processor', () => ({
  processPriceAlerts: (...args: unknown[]) => mockProcessPriceAlerts(...args),
}))

vi.mock('../../src/lib/risk-monitor-processor', () => ({
  processRiskMonitor: (...args: unknown[]) => mockProcessRiskMonitor(...args),
}))

vi.mock('../../src/lib/news-brief-processor', () => ({
  processNewsBrief: (...args: unknown[]) => mockProcessNewsBrief(...args),
}))

import { runAgentTasks } from '../../src/jobs/scheduled'

const createMockEnv = (): Env => ({
  ENVIRONMENT: 'test',
  CONVEX_URL: 'https://example.convex.cloud',
  OPENROUTER_API_KEY: 'test-key',
} as Env)

describe('Scheduled Agent Tasks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('runs price alert processor for price_alert tasks', async () => {
    const env = createMockEnv()
    await runAgentTasks(env, 'price_alert')

    expect(mockProcessPriceAlerts).toHaveBeenCalledWith(env)
  })

  it('runs risk monitor processor for risk_monitor tasks', async () => {
    const env = createMockEnv()
    await runAgentTasks(env, 'risk_monitor')

    expect(mockProcessRiskMonitor).toHaveBeenCalledWith(env)
  })

  it('runs news brief processor for news_brief tasks', async () => {
    const env = createMockEnv()
    await runAgentTasks(env, 'news_brief')

    expect(mockProcessNewsBrief).toHaveBeenCalledWith(env)
  })
})
