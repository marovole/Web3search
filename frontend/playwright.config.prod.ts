import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright Configuration for Production Environment Testing
 *
 * Tests https://web3search.pages.dev/ production deployment
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 120000, // 2 minutes per test (Deep Research can take 60s)
  fullyParallel: false, // Sequential execution for production testing
  forbidOnly: !!process.env.CI,
  retries: 1, // Retry once for production flakiness
  workers: 1, // Single worker for predictable results
  expect: { timeout: 10000 },

  reporter: [
    ['html', { outputFolder: 'playwright-report-prod' }],
    ['list'],
    ['json', { outputFile: 'playwright-report-prod/results.json' }],
  ],

  use: {
    baseURL: 'https://web3search.pages.dev',
    trace: 'on',
    screenshot: 'on',
    video: 'on',
    viewport: { width: 1920, height: 1080 },
  },

  projects: [
    {
      name: 'chromium-production',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          slowMo: 50, // Slow down actions for better observability
        },
      },
    },
  ],

  // Do not start local web server for production testing
  // webServer: {
  //   command: 'echo "Testing production environment"',
  //   url: 'https://web3search.pages.dev',
  //   reuseExistingServer: true,
  //   timeout: 10000,
  // },
})
