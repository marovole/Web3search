export function loadEnvConfig() {
  return {
    ENVIRONMENT: 'development' as const,
    USE_MOCK_API: false,
    API_BASE_URL: 'http://localhost:8787',
    ENABLE_SENTRY: false,
    ENABLE_ANALYTICS: false,
    ENABLE_EXPERIMENTAL_FEATURES: false,
    ENABLE_PERFORMANCE_MONITORING: false,
    DEBUG_MODE: false,
    SENTRY_DSN: '',
    SENTRY_ENVIRONMENT: 'development',
    GA_MEASUREMENT_ID: '',
    DEFAULT_CHAT_MODE: 'quick' as const,
  };
}

export function getEnvConfig() {
  return loadEnvConfig();
}

export function isFeatureEnabled(_feature: string): boolean {
  return false;
}

export function getApiConfig() {
  return {
    baseUrl: 'http://localhost:8787',
    useMock: false,
  };
}

export function isDevelopment(): boolean {
  return true;
}

export function isProduction(): boolean {
  return false;
}
