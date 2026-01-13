import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Mock API response helpers
export const mockHelpers = {
  // Mock successful API response
  mockSuccess: (endpoint: string, response: any, method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET') => {
    const handler = {
      GET: http.get,
      POST: http.post,
      PUT: http.put,
      DELETE: http.delete,
    }[method];

    server.use(
      handler(endpoint, () => {
        return HttpResponse.json({
          success: true,
          data: response,
        });
      })
    );
  },

  // Mock error API response
  mockError: (endpoint: string, errorMessage: string, status = 400, method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET') => {
    const handler = {
      GET: http.get,
      POST: http.post,
      PUT: http.put,
      DELETE: http.delete,
    }[method];

    server.use(
      handler(endpoint, () => {
        return HttpResponse.json(
          {
            success: false,
            error: errorMessage,
          },
          { status }
        );
      })
    );
  },

  // Mock network error
  mockNetworkError: (endpoint: string, method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET') => {
    const handler = {
      GET: http.get,
      POST: http.post,
      PUT: http.put,
      DELETE: http.delete,
    }[method];

    server.use(
      handler(endpoint, () => {
        return HttpResponse.error();
      })
    );
  },

  // Mock delayed response
  mockDelay: (endpoint: string, delayMs = 1000, response: any = {}, method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET') => {
    const handler = {
      GET: http.get,
      POST: http.post,
      PUT: http.put,
      DELETE: http.delete,
    }[method];

    server.use(
      handler(endpoint, async () => {
        await pause(delayMs);
        return HttpResponse.json({
          success: true,
          data: response,
        });
      })
    );
  },

  // Mock streaming response (for chat)
  mockStream: (endpoint: string, chunks: string[], delayBetweenChunks = 100) => {
    server.use(
      http.post(endpoint, () => {
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

        return new HttpResponse(stream, {
          status: 200,
          headers: {
            'Content-Type': 'text/plain',
          },
        });
      })
    );
  },

  // Mock paginated response
  mockPaginated: (endpoint: string, items: any[], page = 1, pageSize = 10) => {
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedItems = items.slice(startIndex, endIndex);

    server.use(
      http.get(endpoint, () => {
        return HttpResponse.json({
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
        });
      })
    );
  },

  // Mock file upload
  mockFileUpload: (endpoint: string, response: any) => {
    server.use(
      http.post(endpoint, () => {
        return HttpResponse.json({
          success: true,
          data: response,
        });
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
        http.post('/api/auth/login', () => {
          return HttpResponse.json({
            success: true,
            data: {
              user: userData,
              token: 'mock-jwt-token',
              refreshToken: 'mock-refresh-token',
            },
          });
        })
      );
    },

    logout: () => {
      server.use(
        http.post('/api/auth/logout', () => {
          return HttpResponse.json({
            success: true,
            message: 'Logged out successfully',
          });
        })
      );
    },

    refresh: (newToken: string) => {
      server.use(
        http.post('/api/auth/refresh', () => {
          return HttpResponse.json({
            success: true,
            data: {
              token: newToken,
              refreshToken: 'mock-refreshed-token',
            },
          });
        })
      );
    },
  },

  // Mock search functionality
  mockSearch: (query: string, results: any[]) => {
    server.use(
      http.get('/api/search', () => {
        return HttpResponse.json({
          success: true,
          data: {
            results,
            total: results.length,
            query,
            took: 15,
          },
        });
      })
    );
  },

  // Mock chat functionality
  mockChat: {
    sendMessage: (message: string, response: string) => {
      server.use(
        http.post('/api/chat/message', () => {
          return HttpResponse.json({
            success: true,
            data: {
              id: `msg-${Date.now()}`,
              message: response,
              sender: 'ai',
              timestamp: new Date().toISOString(),
            },
          });
        })
      );
    },

    getConversations: (conversations: any[]) => {
      server.use(
        http.get('/api/chat/conversations', () => {
          return HttpResponse.json({
            success: true,
            data: conversations,
          });
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
