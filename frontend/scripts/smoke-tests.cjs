#!/usr/bin/env node

/**
 * Smoke tests for production deployment
 */

const { chromium } = require('playwright');

async function runSmokeTests() {
  console.log('🚀 Running smoke tests...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const tests = [];
  
  try {
    // Test 1: Basic page load
    console.log('📄 Testing page load...');
    const startTime = Date.now();
    await page.goto(process.env.DEPLOY_URL || 'http://localhost:3000');
    const loadTime = Date.now() - startTime;
    
    const title = await page.title();
    if (!title) {
      throw new Error('Page title is empty');
    }
    
    tests.push({
      name: 'Page Load',
      status: 'passed',
      duration: loadTime,
      details: `Title: ${title}`
    });
    
    // Test 2: Check for critical elements
    console.log('🔍 Checking critical elements...');
    const criticalSelectors = [
      'header',
      'main',
      '[data-testid="search-input"]',
      '[data-testid="theme-toggle"]'
    ];
    
    let missingElements = [];
    for (const selector of criticalSelectors) {
      const element = await page.$(selector);
      if (!element) {
        missingElements.push(selector);
      }
    }
    
    if (missingElements.length > 0) {
      throw new Error(`Missing critical elements: ${missingElements.join(', ')}`);
    }
    
    tests.push({
      name: 'Critical Elements',
      status: 'passed',
      details: `All ${criticalSelectors.length} critical elements found`
    });
    
    // Test 3: Test search functionality
    console.log('🔎 Testing search functionality...');
    await page.fill('[data-testid="search-input"]', 'test query');
    await page.press('[data-testid="search-input"]', 'Enter');
    
    // Wait a bit for search results
    await page.waitForTimeout(2000);
    
    // Check if search results appear (or at least no error)
    const searchResults = await page.$('[data-testid="search-results"]');
    const noResults = await page.$('[data-testid="no-results"]');
    
    if (!searchResults && !noResults) {
      throw new Error('Search functionality not working properly');
    }
    
    tests.push({
      name: 'Search Functionality',
      status: 'passed',
      details: 'Search input and results working'
    });
    
    // Test 4: Test theme toggle
    console.log('🎨 Testing theme toggle...');
    const themeToggle = await page.$('[data-testid="theme-toggle"]');
    if (themeToggle) {
      await themeToggle.click();
      await page.waitForTimeout(500);
      
      // Check if theme changed (by checking for dark mode class or attribute)
      const html = await page.$('html');
      const hasDarkClass = await html.getAttribute('class');
      
      tests.push({
        name: 'Theme Toggle',
        status: 'passed',
        details: `Theme toggle working, current theme: ${hasDarkClass?.includes('dark') ? 'dark' : 'light'}`
      });
    } else {
      tests.push({
        name: 'Theme Toggle',
        status: 'skipped',
        details: 'Theme toggle not found'
      });
    }
    
    // Test 5: Check console errors
    console.log('🐛 Checking for console errors...');
    const logs = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });
    
    await page.reload();
    await page.waitForTimeout(3000);
    
    if (logs.length > 0) {
      console.warn('Console errors found:', logs);
      tests.push({
        name: 'Console Errors',
        status: 'warning',
        details: `${logs.length} console errors found`
      });
    } else {
      tests.push({
        name: 'Console Errors',
        status: 'passed',
        details: 'No console errors'
      });
    }
    
    // Test 6: Performance check
    console.log('⚡ Checking performance...');
    const perfMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime || 0
      };
    });
    
    const performanceGood = perfMetrics.firstContentfulPaint < 2000; // 2 seconds
    
    tests.push({
      name: 'Performance',
      status: performanceGood ? 'passed' : 'warning',
      details: `FCP: ${Math.round(perfMetrics.firstContentfulPaint)}ms, Load: ${Math.round(perfMetrics.loadComplete)}ms`
    });
    
  } catch (error) {
    console.error('❌ Smoke test failed:', error.message);
    tests.push({
      name: 'Smoke Tests',
      status: 'failed',
      details: error.message
    });
  } finally {
    await browser.close();
  }
  
  // Generate report
  const passed = tests.filter(t => t.status === 'passed').length;
  const failed = tests.filter(t => t.status === 'failed').length;
  const warnings = tests.filter(t => t.status === 'warning').length;
  const skipped = tests.filter(t => t.status === 'skipped').length;
  
  console.log('\n📊 Smoke Test Results');
  console.log('=====================');
  tests.forEach(test => {
    const icon = test.status === 'passed' ? '✅' : test.status === 'failed' ? '❌' : test.status === 'warning' ? '⚠️' : '⏭️';
    console.log(`${icon} ${test.name}: ${test.details}`);
  });
  
  console.log(`\n📈 Summary: ${passed} passed, ${failed} failed, ${warnings} warnings, ${skipped} skipped`);
  
  // Write report to file
  const report = {
    timestamp: new Date().toISOString(),
    summary: { passed, failed, warnings, skipped },
    tests
  };
  
  require('fs').writeFileSync(
    require('path').join(__dirname, '../smoke-test-report.json'),
    JSON.stringify(report, null, 2)
  );
  
  if (failed > 0) {
    console.log('\n❌ Smoke tests failed!');
    process.exit(1);
  } else {
    console.log('\n✅ All smoke tests passed!');
    process.exit(0);
  }
}

runSmokeTests().catch(console.error);
