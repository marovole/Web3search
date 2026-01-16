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
    
    // Test 2: Check for critical layout elements
    console.log('🔍 Checking critical elements...');
    const criticalSelectors = [
      '#root',
      'main',
      'aside'
    ];

    const errorText = await page.locator('text=哎呀，出现了一些问题').first();
    if (await errorText.isVisible()) {
      throw new Error('Error boundary rendered: application failed to start');
    }

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

    // Test 3: Check console errors
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

    // Test 4: Performance check
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
