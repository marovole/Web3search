import { rest } from 'msw';
import { server } from '../mocks/server';

// Mock API response helpers
export const mockHelpers = {
  // Mock successful API response
  mockSuccess: (endpoint: string, response: any, method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET') => {
    const handler = {
      GET: rest.get,
      POST: rest.post,
      PUT: rest.put,
      DELETE: rest.delete,
    }[method];

    server.use(
      handler(endpoint, (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            success: true,
            data: response,
          })
        );
      })
    );
  },

  // Mock error API response
  mockError: (endpoint: string, errorMessage: string, status = 400, method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET') => {
    const handler = {
      GET: rest.get,
      POST: rest.post,
      PUT: rest.put,
      DELETE: rest.delete,
    }[method];

    server.use(
      handler(endpoint, (req, res, ctx) => {
        return res(
          ctx.status(status),
          ctx.json({
            success: false,
            error: errorMessage,
          })
        );
      })
    );
  },

  // Mock network error
  mockNetworkError: (endpoint: string, method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET') => {
    const handler = {
      GET: rest.get,
      POST: rest.post,
      PUT: rest.put,
      DELETE: rest.delete,
    }[method];

    server.use(
      handler(endpoint, (req, res, ctx) => {
        return res.networkError('Network error');
      })
    );
  },

  // Mock delayed response
  mockDelay: (endpoint: string, delayMs = 1000, response: any = {}, method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET') => {
    const handler = {
      GET: rest.get,
      POST: rest.post,
      PUT: rest.put,
      DELETE: rest.delete,
    }[method];

    server.use(
      handler(endpoint, (req, res, ctx) => {
        return res(
          ctx.delay(delayMs),
          ctx.status(200),
          ctx.json({
            success: true,
            data: response,
          })
        );
      })
    );
  },

  // Mock streaming response (for chat)
  mockStream: (endpoint: string, chunks: string[], delayBetweenChunks = 100) => {
    server.use(
      rest.post(endpoint, (req, res, ctx) => {
        const stream = new ReadableStream({
          start(controller) {
            chunks.forEach((chunk, index) => {
              setTimeout(() => {
                controller.enqueue(new TextEncoder().encode(chunk));
                if (index === chunks.length - 1) {
                  controller.close();
                }
              }, index * delayBetweenChunks);
            });
          },
        });

        return res(
          ctx.status(200),
          ctx.body(stream)
        );
      })
    );
  },

  // Mock paginated response
  mockPaginated: (endpoint: string, items: any[], page = 1, pageSize = 10) => {
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedItems = items.slice(startIndex, endIndex);

    server.use(
      rest.get(endpoint, (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            success: true,
            data: {
              items: paginatedItems,
              pagination: {
                page,
                pageSize,
                total: items.length,
                totalPages: Math.ceil(items.length / pageSize),
                hasNext: endIndex < items.length,
                hasPrev: page > 1,
              },
            },
          })
        );
      })
    );
  },

  // Mock file upload
  mockFileUpload: (endpoint: string, response: any) => {
    server.use(
      rest.post(endpoint, (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            success: true,
            data: response,
          })
        );
      })
    );
  },

  // Mock WebSocket connection
  mockWebSocket: (url: string, messages: any[]) => {
    // Note: WebSocket mocking requires additional setup
    // This is a placeholder for WebSocket mock implementation
    console.log('WebSocket mock setup for:', url, messages);
  },

  // Mock authentication
  mockAuth: {
    login: (userData: any) => {
      server.use(
        rest.post('/api/auth/login', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              success: true,
              data: {
                user: userData,
                token: 'mock-jwt-token',
                refreshToken: 'mock-refresh-token',
              },
            })
          );
        })
      );
    },

    logout: () => {
      server.use(
        rest.post('/api/auth/logout', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              success: true,
              message: 'Logged out successfully',
            })
          );
        })
      );
    },

    refresh: (newToken: string) => {
      server.use(
        rest.post('/api/auth/refresh', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              success: true,
              data: {
                token: newToken,
                refreshToken: 'mock-refreshed-token',
              },
            })
          );
        })
      );
    },
  },

  // Mock search functionality
  mockSearch: (query: string, results: any[]) => {
    server.use(
      rest.get('/api/search', (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            success: true,
            data: {
              results,
              total: results.length,
              query,
              took: 15,
            },
          })
        );
      })
    );
  },

  // Mock chat functionality
  mockChat: {
    sendMessage: (message: string, response: string) => {
      server.use(
        rest.post('/api/chat/message', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              success: true,
              data: {
                id: 'msg-' + Date.now(),
                message: response,
                sender: 'ai',
                timestamp: new Date().toISOString(),
              },
            })
          );
        })
      );
    },

    getConversations: (conversations: any[]) => {
      server.use(
        rest.get('/api/chat/conversations', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              success: true,
              data: conversations,
            })
          );
        })
      );
    },
  },

  // Reset all mocks to default handlers
  reset: () => {
    server.resetHandlers();
  },
};

// Re-export commonly used helpers
export const {
  mockSuccess,
  mockError,
  mockNetworkError,
  mockDelay,
  mockStream,
  mockPaginated,
  mockFileUpload,
  mockAuth,
  mockSearch,
  mockChat,
  reset,
} = mockHelpers;
