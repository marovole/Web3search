import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    // Use node environment for testing (simpler and more compatible)
    environment: 'node',

    // Enable global test APIs (describe, it, expect, etc.)
    globals: true,

    // Test file patterns
    include: ['src/**/*.test.ts', 'src/**/*.spec.ts', 'tests/**/*.test.ts'],

    // Isolate tests to prevent state leakage
    isolate: true,

    // Setup files for global mocks
    setupFiles: ['./tests/setup.ts'],

    // Coverage configuration
    coverage: {
      // Use v8 for coverage (fast and accurate)
      provider: 'v8',

      // Include all source files
      all: true,

      // Files to include in coverage
      include: ['src/**/*.ts'],

      // Files to exclude from coverage
      exclude: [
        'src/types/**',
        'src/**/*.d.ts',
        'tests/**',
        '**/*.test.ts',
        '**/*.spec.ts',
        'src/lib/mock-helpers.ts',
      ],

      // Coverage reporters
      reporter: ['text', 'json-summary', 'html', 'lcov'],

      // Coverage thresholds (60% minimum)
      statements: 60,
      branches: 60,
      functions: 60,
      lines: 60,

      // Report directory
      reportsDirectory: './coverage',
    },
  },
})
