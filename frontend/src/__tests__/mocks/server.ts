import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Setup MSW server with our handlers
export const server = setupServer(...handlers);

// Test lifecycle helpers
export const setupMockServer = () => {
  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());
};

// Helper to add custom handlers for specific tests
export const addCustomHandler = (handler: any) => {
  server.use(handler);
};

// Helper to mock specific responses
export const mockApiResponse = (
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  response: any,
  status = 200
) => {
  const handler = {
    get: rest.get,
    post: rest.post,
    put: rest.put,
    delete: rest.delete,
  }[method];

  server.use(
    handler(url, (req, res, ctx) => {
      return res(
        ctx.status(status),
        ctx.json(response)
      );
    })
  );
};
