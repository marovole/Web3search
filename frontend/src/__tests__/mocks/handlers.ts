import { http, HttpResponse } from 'msw';

// API base URL - should match your actual API
const API_BASE_URL = 'http://localhost:3001/api';

const readJsonBody = async (request: Request): Promise<Record<string, unknown>> => {
  try {
    return (await request.json()) as Record<string, unknown>;
  } catch {
    return {};
  }
};

const getString = (value: unknown): string | undefined => {
  return typeof value === 'string' ? value : undefined;
};

const getParam = (value: string | readonly string[] | undefined): string | undefined => {
  if (Array.isArray(value)) {
    return value[0];
  }
  return value;
};

// Mock API handlers
export const handlers = [
  // Auth endpoints
  http.post(`${API_BASE_URL}/auth/login`, async ({ request }) => {
    const body = await readJsonBody(request);
    const email = getString(body.email);
    const password = getString(body.password);

    if (email === 'test@example.com' && password === 'password') {
      return HttpResponse.json({
        success: true,
        data: {
          user: {
            id: '1',
            email: 'test@example.com',
            name: 'Test User',
            avatar: 'https://example.com/avatar.jpg',
          },
          token: 'mock-jwt-token',
          refreshToken: 'mock-refresh-token',
        },
      });
    }

    return HttpResponse.json(
      {
        success: false,
        error: 'Invalid credentials',
      },
      { status: 401 }
    );
  }),

  http.post(`${API_BASE_URL}/auth/register`, async ({ request }) => {
    const body = await readJsonBody(request);

    return HttpResponse.json(
      {
        success: true,
        data: {
          user: {
            id: '2',
            email: getString(body.email) ?? 'test@example.com',
            name: getString(body.name) ?? 'Test User',
            avatar: null,
          },
          token: 'mock-jwt-token-new',
          refreshToken: 'mock-refresh-token-new',
        },
      },
      { status: 201 }
    );
  }),

  http.post(`${API_BASE_URL}/auth/refresh`, () => {
    return HttpResponse.json({
      success: true,
      data: {
        token: 'mock-refreshed-jwt-token',
        refreshToken: 'mock-refreshed-token',
      },
    });
  }),

  // Search endpoints
  http.get(`${API_BASE_URL}/search`, ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('q') ?? '';

    return HttpResponse.json({
      success: true,
      data: {
        results: [
          {
            id: '1',
            title: `Search result for ${query}`,
            description: 'This is a mock search result',
            url: 'https://example.com/result1',
            type: 'web',
            relevanceScore: 0.95,
          },
          {
            id: '2',
            title: `Another result for ${query}`,
            description: 'Another mock search result',
            url: 'https://example.com/result2',
            type: 'web',
            relevanceScore: 0.87,
          },
        ],
        total: 2,
        query,
        took: 15,
      },
    });
  }),

  // Chat endpoints
  http.post(`${API_BASE_URL}/chat/message`, async ({ request }) => {
    const body = await readJsonBody(request);
    const message = getString(body.message) ?? '';
    const conversationId = getString(body.conversationId) ?? 'conv-1';

    return HttpResponse.json({
      success: true,
      data: {
        id: `msg-${Date.now()}`,
        conversationId,
        message: `AI response to: ${message}`,
        sender: 'ai',
        timestamp: new Date().toISOString(),
        metadata: {
          model: 'gpt-4',
          tokensUsed: 150,
          processingTime: 1.2,
        },
      },
    });
  }),

  http.get(`${API_BASE_URL}/chat/conversations`, () => {
    return HttpResponse.json({
      success: true,
      data: [
        {
          id: 'conv-1',
          title: 'Test Conversation',
          lastMessage: 'Hello, how can I help you?',
          timestamp: new Date().toISOString(),
          messageCount: 5,
        },
        {
          id: 'conv-2',
          title: 'Another Conversation',
          lastMessage: 'This is another test conversation',
          timestamp: new Date(Date.now() - 86400000).toISOString(),
          messageCount: 3,
        },
      ],
    });
  }),

  http.get(`${API_BASE_URL}/chat/conversations/:id/messages`, ({ params }) => {
    const id = getParam(params.id) ?? 'conv-1';

    return HttpResponse.json({
      success: true,
      data: [
        {
          id: 'msg-1',
          conversationId: id,
          message: 'Hello, how can I help you?',
          sender: 'ai',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: 'msg-2',
          conversationId: id,
          message: 'I need help with testing',
          sender: 'user',
          timestamp: new Date(Date.now() - 3000000).toISOString(),
        },
      ],
    });
  }),

  // Sentiment analysis endpoints
  http.post(`${API_BASE_URL}/sentiment/analyze`, async ({ request }) => {
    const body = await readJsonBody(request);
    const text = getString(body.text) ?? '';

    return HttpResponse.json({
      success: true,
      data: {
        text,
        sentiment: 'positive',
        confidence: 0.85,
        scores: {
          positive: 0.75,
          negative: 0.10,
          neutral: 0.15,
        },
        emotions: {
          joy: 0.6,
          anger: 0.1,
          fear: 0.05,
          sadness: 0.25,
        },
        processedAt: new Date().toISOString(),
      },
    });
  }),

  http.get(`${API_BASE_URL}/sentiment/history`, () => {
    return HttpResponse.json({
      success: true,
      data: [
        {
          id: '1',
          text: 'I love this product!',
          sentiment: 'positive',
          confidence: 0.92,
          timestamp: new Date(Date.now() - 86400000).toISOString(),
        },
        {
          id: '2',
          text: 'This is terrible',
          sentiment: 'negative',
          confidence: 0.88,
          timestamp: new Date(Date.now() - 172800000).toISOString(),
        },
      ],
    });
  }),

  // Dashboard endpoints
  http.get(`${API_BASE_URL}/dashboard/stats`, () => {
    return HttpResponse.json({
      success: true,
      data: {
        totalSearches: 1250,
        totalConversations: 45,
        totalSentimentAnalyses: 89,
        averageResponseTime: 1.2,
        userGrowth: 15.5,
        popularQueries: [
          { query: 'react testing', count: 45 },
          { query: 'web3 search', count: 38 },
          { query: 'AI chat', count: 32 },
        ],
      },
    });
  }),

  // User profile endpoints
  http.get(`${API_BASE_URL}/user/profile`, () => {
    return HttpResponse.json({
      success: true,
      data: {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        avatar: 'https://example.com/avatar.jpg',
        preferences: {
          theme: 'light',
          language: 'en',
          notifications: true,
        },
        subscription: {
          plan: 'pro',
          expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        },
        createdAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
      },
    });
  }),

  http.put(`${API_BASE_URL}/user/profile`, async ({ request }) => {
    const body = await readJsonBody(request);

    return HttpResponse.json({
      success: true,
      data: {
        ...body,
        updatedAt: new Date().toISOString(),
      },
    });
  }),
];
