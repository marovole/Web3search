import { defineConfig, devices } from '@playwright/test'

const PROD_API_BASE_URL = 'https://web3search-api.marovole.workers.dev/api/v1'

// Default to the production API unless a local backend is explicitly requested.
if (!process.env.TEST_ENV) {
  process.env.TEST_ENV = 'production'
}

if (process.env.TEST_ENV !== 'local') {
  process.env.VITE_API_BASE_URL = process.env.VITE_API_BASE_URL || PROD_API_BASE_URL
} else {
  process.env.VITE_API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000'
}

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
  timeout: 120000, // 2分钟每个测试 (历史页面导航、Deep Research等需要较长时间)
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1, // 本地也重试一次
  workers: process.env.CI ? 1 : undefined,
  expect: { timeout: 15000 }, // 增加到15秒以适应生产环境

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }], // 添加 JSON 报告
  ],

  use: {
    baseURL: process.env.VITE_APP_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    /* 增加操作超时以适应生产环境 */
    actionTimeout: 10000, // 操作超时: 10秒
    navigationTimeout: 30000, // 导航超时: 30秒
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
