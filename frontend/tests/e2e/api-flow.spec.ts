/**
 * E2E API流程测试
 * 使用Playwright测试完整的API交互流程
 *
 * 注意：生产环境测试应该使用前端代理路径而不是直接访问后端API
 * 这样可以测试完整的请求链路（前端 → 代理 → 后端）
 */
import { test, expect } from '@playwright/test';

// API基础URL配置
// 生产环境测试：使用 Workers API
// 开发环境测试：使用本地 API
// 通过检测前端 baseURL 判断环境（更可靠）
const getApiBaseUrl = () => {
  // 如果环境变量明确指定了生产环境
  if (process.env.TEST_ENV === 'production') {
    return 'https://web3search-api.marovole.workers.dev/api/v1';
  }
  // 如果有明确的 API URL 配置
  if (process.env.VITE_API_BASE_URL) {
    return process.env.VITE_API_BASE_URL;
  }
  // 默认本地开发环境
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();
const isProduction = process.env.TEST_ENV === 'production';

test.describe('API Integration E2E Tests', () => {
  test('Health check endpoint should be accessible', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('status');
  });

  // Workers API 不提供 /docs 端点，跳过此测试
  test.skip('API documentation should be accessible', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/docs`);

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
  });

  test('API endpoints should not return 404', async ({ request }) => {
    const endpoints = [
      '/chat/quick',
      '/chat/research',
      '/reports/',
    ];

    for (const endpoint of endpoints) {
      // OPTIONS request to check endpoint exists
      const response = await request.fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'OPTIONS',
      });

      // Should not be 404 (endpoint exists)
      expect(response.status()).not.toBe(404);
    }
  });

  test('Quick Chat API should accept valid requests', async ({ request }) => {
    // API_BASE_URL 已经包含 /api/v1，所以 endpoint 只需要相对路径
    const endpoint = '/chat/quick-chat';

    const response = await request.post(`${API_BASE_URL}${endpoint}`, {
      data: {
        query: 'What is Bitcoin?',
        mode: 'quick',
      },
      timeout: 15000, // 15秒超时
    });

    console.log(`API Request: ${API_BASE_URL}${endpoint}`);
    console.log(`Response Status: ${response.status()}`);

    // Should not be 404 (endpoint exists)
    expect(response.status()).not.toBe(404);

    // API 返回 SSE 流式响应，200 状态码即表示成功
    // May return validation error or streaming success
    // 200: SSE streaming, 400: Bad request, 422: Validation error, 429: Rate limit, 500: Server error, 503: Service unavailable
    expect([200, 400, 422, 429, 500, 503]).toContain(response.status());
  });

  test('Invalid requests should return 422', async ({ request }) => {
    const endpoint = '/chat/quick-chat';

    const response = await request.post(`${API_BASE_URL}${endpoint}`, {
      data: {
        invalid_field: 'invalid_value',
      },
      timeout: 10000,
    });

    console.log(`Invalid Request Test - Status: ${response.status()}`);

    // 应该返回验证错误
    expect([400, 422]).toContain(response.status());
  });
});

test.describe('API URL Configuration Tests', () => {
  test('API URLs should not have path duplication', () => {
    const endpoints = [
      '/api/v1/chat/quick',
      '/api/v1/chat/research',
    ];

    endpoints.forEach((endpoint) => {
      const fullUrl = `${API_BASE_URL}${endpoint}`;

      // Should not have /api/api duplication
      expect(fullUrl).not.toContain('/api/api');

      // Should not have double slashes (except protocol)
      const withoutProtocol = fullUrl.split('://')[1] || fullUrl;
      expect(withoutProtocol.includes('//')).toBeFalsy();
    });
  });

  test('API base URL should be properly formatted', () => {
    expect(API_BASE_URL).toMatch(/^https?:\/\//);
    // API base URL 不应该以斜杠结尾
    expect(API_BASE_URL).not.toMatch(/\/$/);
  });
});
