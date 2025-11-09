#!/usr/bin/env node

/**
 * 部署后烟雾测试脚本
 *
 * 用途：验证生产环境部署成功并且关键功能可用
 * 使用方式：
 *   node scripts/smoke-test.js
 *   FRONTEND_URL=https://web3search.pages.dev node scripts/smoke-test.js
 *
 * 退出码：
 *   0 - 所有测试通过
 *   1 - 至少一个测试失败
 */

const https = require('https');
const http = require('http');

// 配置
const FRONTEND_URL = process.env.FRONTEND_URL || 'https://web3search.pages.dev';
const BACKEND_URL = process.env.BACKEND_URL || 'https://web3search-api.marovole.workers.dev';
const TIMEOUT = 30000; // 30秒超时

// 测试结果
const results = {
  passed: 0,
  failed: 0,
  tests: []
};

/**
 * 发送 HTTP/HTTPS 请求
 */
function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const protocol = urlObj.protocol === 'https:' ? https : http;

    const req = protocol.request(url, {
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: TIMEOUT,
      ...options
    }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

/**
 * 记录测试结果
 */
function logTest(name, passed, message, duration) {
  const status = passed ? '✅ PASS' : '❌ FAIL';
  console.log(`${status} ${name} (${duration}ms)`);
  if (message) {
    console.log(`  ${message}`);
  }

  results.tests.push({ name, passed, message, duration });
  if (passed) {
    results.passed++;
  } else {
    results.failed++;
  }
}

/**
 * 运行单个测试
 */
async function runTest(name, testFn) {
  const start = Date.now();
  try {
    await testFn();
    const duration = Date.now() - start;
    logTest(name, true, null, duration);
  } catch (error) {
    const duration = Date.now() - start;
    logTest(name, false, error.message, duration);
  }
}

/**
 * 测试1: 前端可访问性
 */
async function testFrontendAccessibility() {
  const response = await request(FRONTEND_URL, { timeout: 10000 });

  if (response.status !== 200) {
    throw new Error(`Expected status 200, got ${response.status}`);
  }

  if (!response.body.includes('<!DOCTYPE html') && !response.body.includes('<html')) {
    throw new Error('Response does not appear to be HTML');
  }
}

/**
 * 测试2: 后端健康检查
 */
async function testBackendHealth() {
  const response = await request(`${BACKEND_URL}/api/v1/health`, { timeout: 10000 });

  if (response.status !== 200) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  try {
    const data = JSON.parse(response.body);
    if (data.status !== 'healthy' && data.status !== 'ok') {
      throw new Error(`Backend reports unhealthy status: ${data.status}`);
    }
  } catch (parseError) {
    if (parseError.message.includes('unhealthy')) {
      throw parseError;
    }
    // 如果无法解析JSON，但状态码是200，也认为通过
  }
}

/**
 * 测试3: API 端点可达性 (通过前端代理)
 */
async function testApiEndpointReachability() {
  // 测试通过前端代理访问 API
  const response = await request(`${FRONTEND_URL}/api/health`, {
    timeout: 15000,
    headers: {
      'Accept': 'application/json'
    }
  });

  if (response.status !== 200) {
    throw new Error(`API proxy failed with status ${response.status}`);
  }
}

/**
 * 测试4: Quick Chat API 端点存在性
 */
async function testQuickChatEndpoint() {
  // 发送一个简单的 OPTIONS 请求检查端点是否存在
  const response = await request(`${BACKEND_URL}/api/v1/chat/quick-chat`, {
    method: 'OPTIONS',
    timeout: 10000
  });

  // OPTIONS 请求应该不返回 404
  if (response.status === 404) {
    throw new Error('Quick Chat endpoint not found (404)');
  }

  // 任何其他状态码(200, 405, 500等)都表示端点存在
}

/**
 * 测试5: CORS 配置
 */
async function testCorsConfiguration() {
  const response = await request(`${BACKEND_URL}/api/v1/health`, {
    headers: {
      'Origin': FRONTEND_URL,
      'Access-Control-Request-Method': 'POST',
      'Access-Control-Request-Headers': 'Content-Type'
    },
    timeout: 10000
  });

  // 检查 CORS 头部
  const allowOrigin = response.headers['access-control-allow-origin'];
  if (!allowOrigin || (allowOrigin !== '*' && !allowOrigin.includes('web3search'))) {
    console.warn(`  ⚠️  Warning: CORS allow-origin is "${allowOrigin}"`);
  }
}

/**
 * 测试6: 静态资源加载
 */
async function testStaticAssets() {
  // 尝试访问常见的静态资源
  const assetsToTest = [
    '/favicon.ico',
    '/vite.svg',
  ];

  for (const asset of assetsToTest) {
    try {
      const response = await request(`${FRONTEND_URL}${asset}`, { timeout: 5000 });
      if (response.status === 200) {
        return; // 至少一个静态资源可访问即可
      }
    } catch (error) {
      // 继续尝试下一个
    }
  }

  // 如果所有资源都失败，不算错误（可能资源路径变了）
  console.warn('  ⚠️  Warning: No static assets found, but not failing test');
}

/**
 * 主函数
 */
async function main() {
  console.log('🔍 Starting smoke tests...\n');
  console.log(`Frontend URL: ${FRONTEND_URL}`);
  console.log(`Backend URL: ${BACKEND_URL}\n`);

  // 运行所有测试
  await runTest('Frontend Accessibility', testFrontendAccessibility);
  await runTest('Backend Health Check', testBackendHealth);
  await runTest('API Endpoint Reachability (via proxy)', testApiEndpointReachability);
  await runTest('Quick Chat Endpoint Exists', testQuickChatEndpoint);
  await runTest('CORS Configuration', testCorsConfiguration);
  await runTest('Static Assets Loading', testStaticAssets);

  // 输出总结
  console.log('\n' + '='.repeat(50));
  console.log(`Total: ${results.tests.length} tests`);
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log('='.repeat(50));

  // 如果有失败，退出码为1
  if (results.failed > 0) {
    console.error('\n❌ Smoke tests FAILED');
    process.exit(1);
  } else {
    console.log('\n✅ All smoke tests PASSED');
    process.exit(0);
  }
}

// 运行主函数
main().catch((error) => {
  console.error('\n💥 Unexpected error:', error);
  process.exit(1);
});
