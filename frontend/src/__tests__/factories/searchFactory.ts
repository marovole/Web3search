import { faker } from '@faker-js/faker';

export interface SearchResult {
  id: string;
  title: string;
  description: string;
  url: string;
  type: 'web' | 'image' | 'video' | 'news';
  relevanceScore: number;
  thumbnail?: string;
  publishedAt?: string;
  author?: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  took: number;
  page: number;
  pageSize: number;
}

export const createSearchFactory = () => {
  const buildResult = (overrides: Partial<SearchResult> = {}): SearchResult => ({
    id: faker.string.uuid(),
    title: faker.lorem.sentence(),
    description: faker.lorem.paragraph(),
    url: faker.internet.url(),
    type: faker.helpers.arrayElement(['web', 'image', 'video', 'news']),
    relevanceScore: faker.number.float({ min: 0.1, max: 1.0, precision: 0.01 }),
    thumbnail: faker.datatype.boolean() ? faker.image.url() : undefined,
    publishedAt: faker.datatype.boolean() ? faker.date.past().toISOString() : undefined,
    author: faker.datatype.boolean() ? faker.person.fullName() : undefined,
    ...overrides,
  });

  const buildResults = (count: number, overrides: Partial<SearchResult> = {}): SearchResult[] =>
    Array.from({ length: count }, () => buildResult(overrides));

  const buildResponse = (overrides: Partial<SearchResponse> = {}): SearchResponse => {
    const results = buildResults(faker.number.int({ min: 5, max: 20 }));
    return {
      results,
      total: results.length,
      query: faker.lorem.words(3),
      took: faker.number.int({ min: 10, max: 100 }),
      page: 1,
      pageSize: 10,
      ...overrides,
    };
  };

  const webResult = (title?: string): SearchResult => buildResult({
    title: title || 'React Testing Library Documentation',
    description: 'Learn how to test React components with React Testing Library',
    url: 'https://testing-library.com/docs/react-testing-library/intro/',
    type: 'web',
    relevanceScore: 0.95,
  });

  const imageResult = (): SearchResult => buildResult({
    title: 'Test Image',
    description: 'A beautiful test image',
    url: 'https://example.com/image.jpg',
    type: 'image',
    relevanceScore: 0.87,
    thumbnail: faker.image.url(),
  });

  const videoResult = (): SearchResult => buildResult({
    title: 'Testing Tutorial Video',
    description: 'Learn about software testing best practices',
    url: 'https://youtube.com/watch?v=test',
    type: 'video',
    relevanceScore: 0.82,
    thumbnail: faker.image.url(),
  });

  const newsResult = (): SearchResult => buildResult({
    title: 'Latest Testing Framework News',
    description: 'Breaking news about testing tools and frameworks',
    url: 'https://news.example.com/testing-news',
    type: 'news',
    relevanceScore: 0.79,
    author: faker.person.fullName(),
    publishedAt: faker.date.recent().toISOString(),
  });

  const searchForQuery = (query: string, resultCount = 10): SearchResponse => ({
    results: Array.from({ length: resultCount }, (_, index) =>
      buildResult({
        title: `${query} - Result ${index + 1}`,
        description: `This is a search result for ${query}`,
        relevanceScore: 1.0 - (index * 0.05),
      })
    ),
    total: resultCount,
    query,
    took: faker.number.int({ min: 15, max: 50 }),
    page: 1,
    pageSize: 10,
  });

  const emptyResponse = (query: string): SearchResponse => ({
    results: [],
    total: 0,
    query,
    took: 5,
    page: 1,
    pageSize: 10,
  });

  const errorResponse = (query: string): SearchResponse => ({
    results: [],
    total: 0,
    query,
    took: 0,
    page: 1,
    pageSize: 10,
  });

  return {
    buildResult,
    buildResults,
    buildResponse,
    webResult,
    imageResult,
    videoResult,
    newsResult,
    searchForQuery,
    emptyResponse,
    errorResponse,
  };
};

export const searchFactory = createSearchFactory();
