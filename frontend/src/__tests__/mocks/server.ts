import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

export const handlers = [
  http.get('/api/v1/health', () => {
    return HttpResponse.json({ status: 'ok' });
  }),
];

export const server = setupServer(...handlers);

export const setupMockServer = () => {
  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());
};

export const addCustomHandler = (handler: Parameters<typeof server.use>[0]) => {
  server.use(handler);
};

export const mockApiResponse = (
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  response: unknown,
  status = 200
) => {
  const handler = {
    get: http.get,
    post: http.post,
    put: http.put,
    delete: http.delete,
  }[method];

  server.use(
    handler(url, () => {
      return HttpResponse.json(response, { status });
    })
  );
};
