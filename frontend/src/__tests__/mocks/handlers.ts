import { rest } from 'msw';

// API base URL - should match your actual API
const API_BASE_URL = 'http://localhost:3001/api';

// Mock API handlers
export const handlers = [
  // Auth endpoints
  rest.post(`${API_BASE_URL}/auth/login`, (req, res, ctx) => {
    const { email, password } = req.body as any;
    
    if (email === 'test@example.com' && password === 'password') {
      return res(
        ctx.status(200),
        ctx.json({
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
        })
      );
    }
    
    return res(
      ctx.status(401),
      ctx.json({
        success: false,
        error: 'Invalid credentials',
      })
    );
  }),

  rest.post(`${API_BASE_URL}/auth/register`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        success: true,
        data: {
          user: {
            id: '2',
            email: (req.body as any).email,
            name: (req.body as any).name,
            avatar: null,
          },
          token: 'mock-jwt-token-new',
          refreshToken: 'mock-refresh-token-new',
        },
      })
    );
  }),

  rest.post(`${API_BASE_URL}/auth/refresh`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          token: 'mock-refreshed-jwt-token',
          refreshToken: 'mock-refreshed-token',
        },
      })
    );
  }),

  // Search endpoints
  rest.get(`${API_BASE_URL}/search`, (req, res, ctx) => {
    const query = req.url.searchParams.get('q');
    
    return res(
      ctx.status(200),
      ctx.json({
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
          query: query || '',
          took: 15,
        },
      })
    );
  }),

  // Chat endpoints
  rest.post(`${API_BASE_URL}/chat/message`, (req, res, ctx) => {
    const { message, conversationId } = req.body as any;
    
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          id: 'msg-' + Date.now(),
          conversationId: conversationId || 'conv-1',
          message: `AI response to: ${message}`,
          sender: 'ai',
          timestamp: new Date().toISOString(),
          metadata: {
            model: 'gpt-4',
            tokensUsed: 150,
            processingTime: 1.2,
          },
        },
      })
    );
  }),

  rest.get(`${API_BASE_URL}/chat/conversations`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
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
      })
    );
  }),

  rest.get(`${API_BASE_URL}/chat/conversations/:id/messages`, (req, res, ctx) => {
    const { id } = req.params;
    
    return res(
      ctx.status(200),
      ctx.json({
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
      })
    );
  }),

  // Sentiment analysis endpoints
  rest.post(`${API_BASE_URL}/sentiment/analyze`, (req, res, ctx) => {
    const { text } = req.body as any;
    
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          sentiment: 'positive', // positive, negative, neutral
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
      })
    );
  }),

  rest.get(`${API_BASE_URL}/sentiment/history`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
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
      })
    );
  }),

  // Dashboard endpoints
  rest.get(`${API_BASE_URL}/dashboard/stats`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
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
      })
    );
  }),

  // User profile endpoints
  rest.get(`${API_BASE_URL}/user/profile`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
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
      })
    );
  }),

  rest.put(`${API_BASE_URL}/user/profile`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: {
          ...req.body,
          updatedAt: new Date().toISOString(),
        },
      })
    );
  }),
];
