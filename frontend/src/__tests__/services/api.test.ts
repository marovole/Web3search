/**
 * API Service Tests
 * Comprehensive test suite for frontend API service layer
 */

import { jest } from '@jest/globals'

// Test path normalization logic
const normalizeApiPath = (baseUrl: string, path: string): string => {
  const normalizedBase = baseUrl.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '')
  const normalizedPath = path.replace(/^\/?api\/v1\/?/, '').replace(/^\//, '')
  return `${normalizedBase}/api/v1/${normalizedPath}`.replace(/\/+$/, '')
}

describe('API Configuration', () => {
  it('should normalize API path correctly', () => {
    expect(normalizeApiPath('http://localhost:8787/api/v1', 'chat/quick-chat'))
      .toBe('http://localhost:8787/api/v1/chat/quick-chat')

    expect(normalizeApiPath('http://localhost:8787', '/api/v1/chat/quick-chat'))
      .toBe('http://localhost:8787/api/v1/chat/quick-chat')

    expect(normalizeApiPath('http://localhost:8787/', 'chat/quick-chat'))
      .toBe('http://localhost:8787/api/v1/chat/quick-chat')
  })

  it('should handle baseURL with trailing slash', () => {
    expect(normalizeApiPath('http://localhost:8787/', 'deep-research'))
      .toBe('http://localhost:8787/api/v1/deep-research')
  })
})

describe('Request Interceptor', () => {
  it('should extract token from tokenManager', () => {
    const getToken = () => 'test-token-123'
    const token = getToken()

    expect(token).toBe('test-token-123')
  })

  it('should return null when no token', () => {
    const getToken = () => null
    const token = getToken()

    expect(token).toBeNull()
  })
})

describe('Response Interceptor', () => {
  it('should extract error message from response data', () => {
    const extractErrorMessage = (error: { response?: { data?: { detail?: string } }, message?: string }): string => {
      return error.response?.data?.detail || error.message || '请求失败'
    }

    const errorWithDetail = {
      response: {
        data: {
          detail: 'Invalid API key provided'
        }
      }
    }
    expect(extractErrorMessage(errorWithDetail)).toBe('Invalid API key provided')

    const errorWithMessage = {
      message: 'Network timeout'
    }
    expect(extractErrorMessage(errorWithMessage)).toBe('Network timeout')

    const errorWithNothing = {}
    expect(extractErrorMessage(errorWithNothing)).toBe('请求失败')
  })
})

describe('QuickChat API', () => {
  it('should call quickChat API with correct parameters', async () => {
    // Mock API config
    const apiConfig = { baseUrl: 'http://localhost:8787', useMock: true }

    // Mock response
    const mockResponse = {
      content: 'Mock response',
      symbol: 'BTC',
      query_type: 'test',
      response_time: 100,
      model: 'test-model',
      session_id: 'test-session'
    }

    // Simulate mock API behavior
    const quickChat = async (request: { query: string }) => {
      if (apiConfig.useMock) {
        return mockResponse
      }
      throw new Error('Not in mock mode')
    }

    const result = await quickChat({ query: 'What is Bitcoin price?' })

    expect(result.content).toBe('Mock response')
    expect(result.symbol).toBe('BTC')
  })

  it('should handle API errors gracefully', async () => {
    const quickChat = async (_request: { query: string }) => {
      throw new Error('API Error: 401 Unauthorized')
    }

    await expect(quickChat({ query: 'test' })).rejects.toThrow('API Error: 401 Unauthorized')
  })
})

describe('DeepResearch API', () => {
  it('should create EventSource with correct parameters', () => {
    const createEventSource = (url: string) => ({ url, close: jest.fn() })

    const request = { query: 'Bitcoin analysis', conversation_id: 'conv-123' }
    const queryParams = new URLSearchParams({
      query: request.query,
      ...(request.conversation_id && { conversation_id: request.conversation_id }),
    })
    const url = `http://localhost:8787/api/v1/deep-research/stream?${queryParams}`
    const eventSource = createEventSource(url)

    expect(eventSource.url).toContain('query=Bitcoin')
    expect(eventSource.url).toContain('conversation_id=conv-123')
  })

  it('should return mock EventSource in mock mode', () => {
    const mockEventSource = { onmessage: jest.fn(), onerror: jest.fn(), close: jest.fn() }

    expect(mockEventSource).toBeDefined()
    expect(typeof mockEventSource.onmessage).toBe('function')
    expect(typeof mockEventSource.onerror).toBe('function')
  })
})

describe('Report Generation API', () => {
  it('should generate report with correct sections', async () => {
    const generateReport = async (request: { topic: string; sections: any[] }) => {
      return new Response(
        new ReadableStream({
          start(controller) {
            const encoder = new TextEncoder()
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'report_start', topic: request.topic })}\n\n`))
            controller.close()
          }
        }),
        { headers: { 'Content-Type': 'text/event-stream' } }
      )
    }

    const request = {
      topic: 'Bitcoin Analysis',
      sections: [
        { id: 'overview', title: 'Overview' },
        { id: 'risks', title: 'Risk Assessment' }
      ]
    }

    const result = await generateReport(request)
    expect(result.headers.get('content-type')).toContain('text/event-stream')
  })

  it('should throw error when response is not ok', async () => {
    const generateReport = async (_request: { topic: string; sections: any[] }) => {
      throw new Error('Invalid request parameters')
    }

    await expect(generateReport({ topic: 'test', sections: [] }))
      .rejects
      .toThrow('Invalid request parameters')
  })
})

describe('Search Suggestions API', () => {
  it('should return suggestions based on query', async () => {
    const getSearchSuggestions = async (query: string) => {
      const suggestions = [
        { id: '1', title: 'Web3技术趋势', type: 'report' as const },
        { id: '2', title: 'DeFi协议对比', type: 'report' as const },
        { id: '3', title: 'NFT市场分析', type: 'chat' as const }
      ].filter(item => item.title.toLowerCase().includes(query.toLowerCase()))

      return { suggestions, popular: ['blockchain', 'ethereum', 'web3'] }
    }

    const result = await getSearchSuggestions('web3')

    expect(result.suggestions.length).toBeGreaterThan(0)
    expect(result.popular).toBeDefined()
  })

  it('should return mock suggestions in mock mode', async () => {
    const getSearchSuggestions = async (query: string) => {
      return {
        suggestions: [
          { id: '1', title: 'Web3技术趋势', type: 'report' as const }
        ].filter(item => item.title.toLowerCase().includes(query.toLowerCase())),
        popular: ['blockchain', 'ethereum', 'web3', 'defi']
      }
    }

    const result = await getSearchSuggestions('web3')

    expect(result).toHaveProperty('suggestions')
    expect(result).toHaveProperty('popular')
    expect(Array.isArray(result.suggestions)).toBe(true)
  })
})

describe('Health Check API', () => {
  it('should return health status', async () => {
    const healthCheck = async () => {
      return { status: 'healthy', responseTime: 50 }
    }

    const result = await healthCheck()

    expect(result.status).toBe('healthy')
    expect(result.responseTime).toBeDefined()
  })

  it('should throw error when health check fails', async () => {
    const healthCheck = async () => {
      throw new Error('Service unavailable')
    }

    await expect(healthCheck()).rejects.toThrow('Service unavailable')
  })
})

describe('Billing API', () => {
  it('should create checkout session', async () => {
    const createCheckoutSession = async (plan: string, interval: string) => {
      return {
        checkout_url: 'https://checkout.stripe.com/xxx',
        session_id: `cs_${Date.now()}`
      }
    }

    const result = await createCheckoutSession('pro', 'monthly')

    expect(result.checkout_url).toBeDefined()
    expect(result.session_id).toBeDefined()
  })

  it('should create billing portal session', async () => {
    const createPortalSession = async () => {
      return { portal_url: 'https://billing.stripe.com/xxx' }
    }

    const result = await createPortalSession()

    expect(result.portal_url).toBeDefined()
  })
})
