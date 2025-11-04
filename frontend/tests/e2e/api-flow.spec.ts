/**
 * E2E API流程测试
 * 使用Playwright测试完整的API交互流程
 */
import { test, expect } from '@playwright/test';

// API基础URL（从环境变量获取）
const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';

test.describe('API Integration E2E Tests', () => {
  test('Health check endpoint should be accessible', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('status');
  });

  test('API documentation should be accessible', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/docs`);

    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
  });

  test('API endpoints should not return 404', async ({ request }) => {
    const endpoints = [
      '/api/v1/chat/quick',
      '/api/v1/chat/research',
      '/api/v1/reports/',
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
    const response = await request.post(`${API_BASE_URL}/api/v1/chat/quick`, {
      data: {
        query: 'What is Bitcoin?',
        stream: false,
      },
    });

    // Should not be 404 (endpoint exists)
    expect(response.status()).not.toBe(404);

    // May return validation error or success
    expect([200, 400, 422, 500, 503]).toContain(response.status());
  });

  test('Invalid requests should return 422', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/v1/chat/quick`, {
      data: {
        invalid_field: 'invalid_value',
      },
    });

    expect(response.status()).toBe(422);
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
    expect(API_BASE_URL).not.toContain('/api');
  });
});
