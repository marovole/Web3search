import { describe, it, expect } from 'vitest'
import { 
  getEnvConfig, 
  isFeatureEnabled, 
  getApiConfig, 
  isDevelopment, 
  isProduction 
} from '../utils/env'

describe('env utilities', () => {
  describe('getEnvConfig', () => {
    it('should return configuration object', () => {
      const config = getEnvConfig()
      expect(config).toBeDefined()
      expect(config).toHaveProperty('ENVIRONMENT')
      expect(config).toHaveProperty('API_BASE_URL')
      expect(config).toHaveProperty('USE_MOCK_API')
    })
  })

  describe('isFeatureEnabled', () => {
    it('should return boolean value', () => {
      const enabled = isFeatureEnabled('ENABLE_SENTRY')
      expect(typeof enabled).toBe('boolean')
    })

    it('should check ENABLE_ANALYTICS feature', () => {
      const enabled = isFeatureEnabled('ENABLE_ANALYTICS')
      expect(typeof enabled).toBe('boolean')
    })
  })

  describe('getApiConfig', () => {
    it('should return API configuration', () => {
      const apiConfig = getApiConfig()
      expect(apiConfig).toHaveProperty('baseUrl')
      expect(apiConfig).toHaveProperty('useMock')
      expect(typeof apiConfig.baseUrl).toBe('string')
      expect(typeof apiConfig.useMock).toBe('boolean')
    })
  })

  describe('isDevelopment', () => {
    it('should return boolean value', () => {
      const result = isDevelopment()
      expect(typeof result).toBe('boolean')
    })
  })

  describe('isProduction', () => {
    it('should return boolean value', () => {
      const result = isProduction()
      expect(typeof result).toBe('boolean')
    })
  })
})

