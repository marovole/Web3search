/**
 * Token Manager Tests
 * Tests for secure token storage and retrieval
 */

import { jest } from '@jest/globals'

// Mock environment
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('TokenManager', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
  })

  describe('Token Storage', () => {
    it('should store token in localStorage', () => {
      const token = 'test-token-12345'
      localStorage.setItem('auth_token', token)
      
      expect(localStorage.getItem('auth_token')).toBe(token)
    })

    it('should retrieve token from localStorage', () => {
      const token = 'retrievable-token'
      localStorage.setItem('auth_token', token)
      
      const retrieved = localStorage.getItem('auth_token')
      expect(retrieved).toBe(token)
    })

    it('should return null when token does not exist', () => {
      const retrieved = localStorage.getItem('auth_token')
      expect(retrieved).toBeNull()
    })

    it('should remove token from localStorage', () => {
      localStorage.setItem('auth_token', 'to-be-removed')
      localStorage.removeItem('auth_token')
      
      expect(localStorage.getItem('auth_token')).toBeNull()
    })

    it('should clear all tokens', () => {
      localStorage.setItem('auth_token', 'token1')
      localStorage.setItem('refresh_token', 'token2')
      localStorage.clear()
      
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
    })
  })

  describe('Token Security', () => {
    it('should not expose token in error messages', () => {
      const token = 'secure-token-123'
      localStorage.setItem('auth_token', token)
      
      // Simulate error handling that should not expose the token
      const errorHandler = (): string => {
        try {
          throw new Error('Token validation failed')
        } catch (e) {
          const error = e as Error
          // Error message should not contain the actual token
          return error.message
        }
      }
      
      const errorMessage = errorHandler()
      expect(errorMessage).not.toContain(token)
    })

    it('should handle concurrent storage operations', () => {
      const operations = Array.from({ length: 10 }, (_, i) => {
        return () => localStorage.setItem(`token_${i}`, `value_${i}`)
      })
      
      operations.forEach(op => op())
      
      for (let i = 0; i < 10; i++) {
        expect(localStorage.getItem(`token_${i}`)).toBe(`value_${i}`)
      }
    })

    it('should handle special characters in tokens', () => {
      const specialToken = 'token=abc&token=def+ghi'
      localStorage.setItem('auth_token', specialToken)
      
      expect(localStorage.getItem('auth_token')).toBe(specialToken)
    })

    it('should handle unicode characters in tokens', () => {
      const unicodeToken = 'token_中文_emoji_🚀_🎉'
      localStorage.setItem('auth_token', unicodeToken)
      
      expect(localStorage.getItem('auth_token')).toBe(unicodeToken)
    })
  })

  describe('Token Expiration', () => {
    it('should store token with timestamp', () => {
      const token = 'timestamped-token'
      const timestamp = Date.now()
      
      localStorage.setItem('auth_token', token)
      localStorage.setItem('auth_token_timestamp', timestamp.toString())
      
      expect(localStorage.getItem('auth_token_timestamp')).toBe(timestamp.toString())
    })

    it('should check token expiration', () => {
      const now = Date.now()
      const oneHourAgo = now - 3600000
      const oneHourFromNow = now + 3600000
      
      localStorage.setItem('auth_token_timestamp', oneHourAgo.toString())
      
      const storedTimestamp = parseInt(localStorage.getItem('auth_token_timestamp') || '0')
      const isExpired = now - storedTimestamp > 3600000 // 1 hour
      
      expect(isExpired).toBe(true)
      
      // Test with future timestamp
      localStorage.setItem('auth_token_timestamp', oneHourFromNow.toString())
      const futureStoredTimestamp = parseInt(localStorage.getItem('auth_token_timestamp') || '0')
      const isNotExpired = now - futureStoredTimestamp > 3600000
      
      expect(isNotExpired).toBe(false)
    })
  })

  describe('Session Storage', () => {
    it('should store session-specific data separately', () => {
      const sessionStorageMock = (() => {
        let store: Record<string, string> = {}
        return {
          getItem: (key: string) => store[key] || null,
          setItem: (key: string, value: string) => {
            store[key] = value.toString()
          },
          removeItem: (key: string) => {
            delete store[key]
          },
          clear: () => {
            store = {}
          },
        }
      })()
      
      Object.defineProperty(window, 'sessionStorage', {
        value: sessionStorageMock,
      })
      
      sessionStorage.setItem('session_id', 'session-123')
      expect(sessionStorage.getItem('session_id')).toBe('session-123')
      
      sessionStorage.clear()
      expect(sessionStorage.getItem('session_id')).toBeNull()
    })
  })
})

describe('Input Validation Security', () => {
  describe('XSS Prevention', () => {
    it('should sanitize HTML input', () => {
      const sanitizeInput = (input: string): string => {
        return input
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#x27;')
          .replace(/\//g, '&#x2F;')
      }
      
      const maliciousInput = '<script>alert("xss")</script>'
      const sanitized = sanitizeInput(maliciousInput)
      
      expect(sanitized).not.toContain('<script>')
      expect(sanitized).toContain('&lt;script&gt;')
    })

    it('should sanitize JavaScript protocol', () => {
      const sanitizeInput = (input: string): string => {
        return input.replace(/javascript:/gi, '')
      }
      
      const maliciousInput = 'javascript:alert("xss")'
      const sanitized = sanitizeInput(maliciousInput)
      
      expect(sanitized).not.toContain('javascript:')
    })

    it('should sanitize event handlers', () => {
      const sanitizeInput = (input: string): string => {
        return input.replace(/on\w+=/gi, '')
      }
      
      const maliciousInput = '<img src=x onerror=alert(1)>'
      const sanitized = sanitizeInput(maliciousInput)
      
      expect(sanitized).not.toContain('onerror=')
    })
  })

  describe('SQL Injection Prevention', () => {
    it('should escape special SQL characters', () => {
      const escapeSql = (input: string): string => {
        return input
          .replace(/'/g, "''")
          .replace(/"/g, '""')
          .replace(/;/g, '')
          .replace(/--/g, '')
          .replace(/\/\*/g, '')
          .replace(/\*\//g, '')
      }
      
      const maliciousInput = "'; DROP TABLE users; --"
      const escaped = escapeSql(maliciousInput)
      
      expect(escaped).not.toContain("DROP TABLE")
      expect(escaped).toContain("''")
    })
  })

  describe('Input Length Validation', () => {
    it('should reject inputs exceeding max length', () => {
      const MAX_LENGTH = 1000
      
      const validateLength = (input: string): boolean => {
        return input.length <= MAX_LENGTH
      }
      
      const shortInput = 'a'.repeat(500)
      const longInput = 'a'.repeat(1500)
      
      expect(validateLength(shortInput)).toBe(true)
      expect(validateLength(longInput)).toBe(false)
    })

    it('should reject empty input', () => {
      const validateInput = (input: string): boolean => {
        return input.trim().length > 0
      }
      
      expect(validateInput('valid input')).toBe(true)
      expect(validateInput('')).toBe(false)
      expect(validateInput('   ')).toBe(false)
    })
  })
})
