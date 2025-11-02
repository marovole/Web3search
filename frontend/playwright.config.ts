import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright End-to-End Testing Configuration
 *
 * Tests the following scenarios:
 * - Quick Chat functionality
 * - Deep Research report generation
 * - Report export and sharing
 * - Search autocomplete
 * - Hotspot panel interaction
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 120000, // 2 minutes per test (Deep Research can take 30s)
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  expect: { timeout: 10000 },

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],

  use: {
    baseURL: process.env.VITE_APP_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npm run build && npm run preview',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
})
