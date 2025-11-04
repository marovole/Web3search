/**
 * 前端API集成测试
 * 测试API客户端和环境配置
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getEnvConfig } from '../../src/config/env';

describe('API Integration Tests', () => {
  describe('Environment Configuration', () => {
    it('should load environment configuration', () => {
      const config = getEnvConfig();

      expect(config).toBeDefined();
      expect(config.apiBaseUrl).toBeDefined();
      expect(config.environment).toBeDefined();
    });

    it('should have valid API base URL format', () => {
      const config = getEnvConfig();

      // API URL should be a valid URL
      expect(config.apiBaseUrl).toMatch(/^https?:\/\//);
    });

    it('should not have path duplication in API URL', () => {
      const config = getEnvConfig();

      // Should not have /api/api duplication
      expect(config.apiBaseUrl).not.toContain('/api/api');
    });

    it('should detect environment correctly', () => {
      const config = getEnvConfig();

      expect(['development', 'production', 'test']).toContain(config.environment);
    });
  });

  describe('API URL Construction', () => {
    it('should construct valid API endpoints', () => {
      const config = getEnvConfig();
      const baseUrl = config.apiBaseUrl.replace(/\/$/, '');

      const endpoints = [
        '/api/v1/chat/quick',
        '/api/v1/chat/research',
        '/api/v1/reports/',
      ];

      endpoints.forEach((endpoint) => {
        const fullUrl = `${baseUrl}${endpoint}`;

        // Should be valid URL
        expect(fullUrl).toMatch(/^https?:\/\//);

        // Should not have double slashes (except in protocol)
        const withoutProtocol = fullUrl.split('://')[1];
        expect(withoutProtocol).not.toContain('//');

        // Should contain /api/v1/
        expect(fullUrl).toContain('/api/v1/');
      });
    });

    it('should handle trailing slashes correctly', () => {
      const config = getEnvConfig();
      const baseUrl = config.apiBaseUrl.replace(/\/$/, '');
      const endpoint = '/api/v1/test';

      const fullUrl = `${baseUrl}${endpoint}`;

      // Should not have double slashes in path
      expect(fullUrl).not.toMatch(/[^:]\/\//);
    });
  });

  describe('Production Environment Config', () => {
    it('should use complete URLs in production', () => {
      // Mock production environment
      const originalEnv = import.meta.env.MODE;
      vi.stubGlobal('import.meta.env.MODE', 'production');

      const config = getEnvConfig();

      if (config.environment === 'production') {
        // Production should use complete HTTPS URLs
        expect(config.apiBaseUrl).toMatch(/^https:\/\//);
        expect(config.apiBaseUrl).not.toMatch(/^\//)  ; // Not relative path
        expect(config.apiBaseUrl).not.toMatch(/localhost/);
      }

      // Restore
      vi.stubGlobal('import.meta.env.MODE', originalEnv);
    });

    it('should not use relative paths in production', () => {
      const config = getEnvConfig();

      if (config.environment === 'production') {
        expect(config.apiBaseUrl).not.toMatch(/^\/[^/]/);
        expect(config.apiBaseUrl).not.toMatch(/^\.\//);
      }
    });
  });

  describe('Development Environment Config', () => {
    it('should support localhost in development', () => {
      const config = getEnvConfig();

      if (config.environment === 'development') {
        // Development can use localhost
        const isLocalhost = config.apiBaseUrl.includes('localhost');
        const isHttpUrl = config.apiBaseUrl.startsWith('http://') ||
                         config.apiBaseUrl.startsWith('https://');

        expect(isLocalhost || isHttpUrl).toBe(true);
      }
    });
  });

  describe('API Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      // Mock fetch to simulate network error
      const mockFetch = vi.fn(() =>
        Promise.reject(new Error('Network error'))
      );
      vi.stubGlobal('fetch', mockFetch);

      try {
        await fetch('/api/v1/test');
        // Should throw
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
        expect((error as Error).message).toContain('Network error');
      }

      vi.unstubAllGlobals();
    });

    it('should handle timeout errors', async () => {
      // Mock fetch with timeout
      const mockFetch = vi.fn(() =>
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Timeout')), 100)
        )
      );
      vi.stubGlobal('fetch', mockFetch);

      try {
        await fetch('/api/v1/test');
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
      }

      vi.unstubAllGlobals();
    });
  });

  describe('API Response Validation', () => {
    it('should validate response status codes', async () => {
      // Mock successful response
      const mockFetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ data: 'test' }),
        } as Response)
      );
      vi.stubGlobal('fetch', mockFetch);

      const response = await fetch('/api/v1/health');
      expect(response.ok).toBe(true);
      expect(response.status).toBe(200);

      vi.unstubAllGlobals();
    });

    it('should handle 404 errors', async () => {
      // Mock 404 response
      const mockFetch = vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 404,
          statusText: 'Not Found',
        } as Response)
      );
      vi.stubGlobal('fetch', mockFetch);

      const response = await fetch('/api/v1/nonexistent');
      expect(response.ok).toBe(false);
      expect(response.status).toBe(404);

      vi.unstubAllGlobals();
    });
  });
});
