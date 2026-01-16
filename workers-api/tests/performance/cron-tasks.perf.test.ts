import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Env } from '../../src/types/env'
import { runAgentTasks } from '../../src/jobs/scheduled'
import { runPerformanceTest, calculateP95 } from '../utils/performance'

const mockExecuteAgentTask = vi.fn().mockResolvedValue(undefined)

const mockTasks = Array.from({ length: 50 }, (_, index) => ({
  id: `task-${index}`,
  user_id: 'user-123',
  task_type: 'custom',
  config: { index },
}))

vi.mock('../../src/lib/agent-engine', () => ({
  executeAgentTask: (...args: unknown[]) => mockExecuteAgentTask(...args),
}))

vi.mock('../../src/lib/supabase', () => ({
  getSupabaseClient: vi.fn(() => ({
    from: () => {
      const updateChain = {
        eq: vi.fn().mockResolvedValue({ error: null }),
      }

      return {
        select: vi.fn().mockReturnThis(),
        eq: vi.fn().mockReturnThis(),
        or: vi.fn().mockReturnThis(),
        limit: vi.fn().mockResolvedValue({ data: mockTasks, error: null }),
        update: vi.fn().mockReturnValue(updateChain),
      }
    }
  })),
}))

const createMockEnv = (): Env => ({
  ENVIRONMENT: 'test',
  CONVEX_URL: 'https://example.convex.cloud',
  OPENROUTER_API_KEY: 'test-key',
} as Env)

const PERF_TARGETS = {
  P95_MS: 750,
  ITERATIONS: 5,
}

describe('Cron Task Load Harness', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('processes 50 agent tasks within expected time', async () => {
    const env = createMockEnv()

    const durations = await runPerformanceTest(async () => {
      await runAgentTasks(env, 'custom')
    }, PERF_TARGETS.ITERATIONS)

    const p95 = calculateP95(durations)

    expect(p95).toBeLessThan(PERF_TARGETS.P95_MS)
    expect(mockExecuteAgentTask).toHaveBeenCalled()
  })
})
