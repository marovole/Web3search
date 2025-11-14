/**
 * Vitest Setup File
 * Initializes global mocks and test environment for Cloudflare Workers
 */

import { vi } from 'vitest'

// Mock crypto.randomUUID if not available in test environment
if (typeof crypto === 'undefined' || !crypto.randomUUID) {
  global.crypto = {
    ...global.crypto,
    randomUUID: vi.fn(() => '00000000-0000-0000-0000-000000000000'),
  } as any
}

// Mock console methods to reduce noise in tests (optional)
// Uncomment if you want to suppress console output during tests
// global.console = {
//   ...console,
//   log: vi.fn(),
//   debug: vi.fn(),
//   info: vi.fn(),
//   warn: vi.fn(),
//   error: vi.fn(),
// }

// Add any other global mocks or setup here
// For example, mock KV namespace, Supabase clients, etc.
