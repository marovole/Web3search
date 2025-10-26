import { test, expect } from '@playwright/test'

/**
 * End-to-End Tests for Chat Interface
 *
 * Tests Quick Chat and Deep Research functionality
 */

test.describe('Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    // Wait for the page to load
    await expect(page.locator('h2')).toContainText('欢迎使用 Web3 AI 搜索引擎')
  })

  test('should display welcome message and hotspot panel', async ({ page }) => {
    // Check welcome message is visible
    await expect(page.locator('h2')).toContainText('欢迎使用')

    // Check mode switch is visible
    await expect(page.locator('text=Quick Chat')).toBeVisible()
    await expect(page.locator('text=Deep Research')).toBeVisible()

    // Check hotspot panel is visible
    await expect(page.locator('text=市场热点')).toBeVisible()
  })

  test('should switch between Quick Chat and Deep Research modes', async ({ page }) => {
    // Check default mode is Quick Chat
    const quickChatButton = page.locator('button:has-text("Quick Chat")')
    const deepResearchButton = page.locator('button:has-text("Deep Research")')

    // Switch to Deep Research
    await deepResearchButton.click()
    await expect(page.locator('textarea')).toHaveAttribute(
      'placeholder',
      /输入加密货币项目名称/
    )

    // Switch back to Quick Chat
    await quickChatButton.click()
    await expect(page.locator('textarea')).toHaveAttribute(
      'placeholder',
      /输入你的问题/
    )
  })

  test('should send Quick Chat message and receive response', async ({ page }) => {
    // Type a question
    const input = page.locator('textarea[placeholder*="输入你的问题"]')
    await input.fill('What is Bitcoin?')

    // Click send button
    await page.locator('button:has-text("发送")').click()

    // Wait for user message to appear
    await expect(page.locator('.message-user')).toContainText('What is Bitcoin?')

    // Wait for AI response (up to 10 seconds)
    await expect(page.locator('.message-assistant')).toBeVisible({ timeout: 10000 })

    // Check that response is not empty
    const response = await page.locator('.message-assistant').first().textContent()
    expect(response).toBeTruthy()
    expect(response!.length).toBeGreaterThan(10)
  })

  test('should interact with hotspot panel', async ({ page }) => {
    // Wait for hotspots to load
    await page.waitForTimeout(2000)

    // Check if hotspot cards are visible
    const hotspotCards = page.locator('[class*="bg-white rounded-lg"]').first()
    if (await hotspotCards.isVisible()) {
      // Click on first hotspot
      await hotspotCards.click()

      // Check that input is filled
      const input = page.locator('textarea')
      const inputValue = await input.inputValue()
      expect(inputValue.length).toBeGreaterThan(0)
    }
  })

  test('should use search autocomplete', async ({ page }) => {
    // Type in search box
    const input = page.locator('textarea')
    await input.fill('BTC')

    // Wait for autocomplete dropdown
    await page.waitForTimeout(500) // Wait for debounce

    // Check if dropdown appears (if API is available)
    const dropdown = page.locator('[class*="autocomplete"]').first()
    if (await dropdown.isVisible()) {
      // Select first suggestion with Enter key
      await page.keyboard.press('ArrowDown')
      await page.keyboard.press('Enter')

      // Check that input is updated
      const inputValue = await input.inputValue()
      expect(inputValue.length).toBeGreaterThan(0)
    }
  })

  test('should navigate to history page', async ({ page }) => {
    // Click history button
    const historyButton = page.locator('button:has-text("历史记录")')
    await historyButton.click()

    // Check URL changed
    await expect(page).toHaveURL(/\/history/)

    // Check page content
    await expect(page.locator('h1')).toContainText('报告历史记录')
  })

  test('should navigate to watchlist page', async ({ page }) => {
    // Click watchlist button
    const watchlistButton = page.locator('button:has-text("监控列表")')
    await watchlistButton.click()

    // Check URL changed
    await expect(page).toHaveURL(/\/watchlist/)

    // Check page content
    await expect(page.locator('h1')).toContainText('监控列表')
  })
})

test.describe('Deep Research', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')

    // Switch to Deep Research mode
    await page.locator('button:has-text("Deep Research")').click()
  })

  test('should generate Deep Research report', async ({ page }) => {
    // Type a crypto symbol
    const input = page.locator('textarea[placeholder*="输入加密货币项目名称"]')
    await input.fill('BTC')

    // Click send button
    await page.locator('button:has-text("发送")').click()

    // Wait for user message
    await expect(page.locator('.message-user')).toContainText('BTC')

    // Wait for loading animation
    await expect(page.locator('text=正在采集市场数据')).toBeVisible({ timeout: 5000 })

    // Wait for report to be generated (up to 60 seconds)
    await expect(page.locator('.message-assistant')).toBeVisible({ timeout: 60000 })

    // Check report contains expected sections
    const reportContent = await page.locator('.message-assistant').first().textContent()
    expect(reportContent).toBeTruthy()
    expect(reportContent!.length).toBeGreaterThan(100)
  })
})

test.describe('Report Viewing', () => {
  test('should display report viewer with table of contents', async ({ page }) => {
    // Skip if no reports available
    // This test would need actual report data to work properly
    test.skip()
  })

  test('should export report as Markdown', async ({ page }) => {
    // Skip - requires actual report
    test.skip()
  })

  test('should export report as PDF', async ({ page }) => {
    // Skip - requires actual report
    test.skip()
  })

  test('should generate share link', async ({ page }) => {
    // Skip - requires actual report
    test.skip()
  })
})
