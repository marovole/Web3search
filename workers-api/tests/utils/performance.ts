/**
 * Performance Testing Utilities
 * Helper functions for measuring and validating performance metrics
 */

/**
 * Calculate P95 (95th percentile) from an array of durations
 * @param durations - Array of duration measurements in milliseconds
 * @returns P95 value
 */
export function calculateP95(durations: number[]): number {
  if (durations.length === 0) {
    throw new Error('Cannot calculate P95 from empty array')
  }

  const sorted = [...durations].sort((a, b) => a - b)
  const index = Math.ceil(0.95 * sorted.length) - 1
  return sorted[Math.max(0, index)]
}

/**
 * Calculate average duration
 */
export function calculateAverage(durations: number[]): number {
  if (durations.length === 0) return 0
  return durations.reduce((sum, d) => sum + d, 0) / durations.length
}

/**
 * Calculate median duration
 */
export function calculateMedian(durations: number[]): number {
  if (durations.length === 0) return 0
  const sorted = [...durations].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
}

/**
 * Performance metrics tracker for KV cache
 */
export class KVMetricsTracker {
  private hits = 0
  private misses = 0

  recordHit() {
    this.hits++
  }

  recordMiss() {
    this.misses++
  }

  getHitRate(): number {
    const total = this.hits + this.misses
    return total === 0 ? 0 : this.hits / total
  }

  getMetrics() {
    return {
      hits: this.hits,
      misses: this.misses,
      total: this.hits + this.misses,
      hitRate: this.getHitRate(),
    }
  }

  reset() {
    this.hits = 0
    this.misses = 0
  }
}

/**
 * Run a performance test with multiple iterations
 * @param fn - Async function to test
 * @param iterations - Number of iterations
 * @returns Array of durations in milliseconds
 */
export async function runPerformanceTest(
  fn: () => Promise<void>,
  iterations: number
): Promise<number[]> {
  const durations: number[] = []

  for (let i = 0; i < iterations; i++) {
    const start = performance.now()
    await fn()
    durations.push(performance.now() - start)
  }

  return durations
}

/**
 * Create an instrumented KV namespace that tracks cache hits/misses
 */
export function createInstrumentedKV(tracker: KVMetricsTracker): KVNamespace {
  const store = new Map<string, string>()

  return {
    get: async (key: string) => {
      const value = store.get(key)
      if (value) {
        tracker.recordHit()
      } else {
        tracker.recordMiss()
      }
      return value || null
    },
    put: async (key: string, value: string) => {
      store.set(key, value)
    },
    delete: async (key: string) => {
      store.delete(key)
    },
    list: async () => ({
      keys: [],
      list_complete: true,
    }),
  } as unknown as KVNamespace
}
