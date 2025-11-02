import { faker } from '@faker-js/faker';

export interface DashboardStats {
  totalSearches: number;
  totalConversations: number;
  totalSentimentAnalyses: number;
  averageResponseTime: number;
  userGrowth: number;
  popularQueries: PopularQuery[];
}

export interface PopularQuery {
  query: string;
  count: number;
}

export interface TimeSeriesData {
  date: string;
  searches: number;
  conversations: number;
  sentimentAnalyses: number;
}

export interface UserActivityData {
  userId: string;
  userName: string;
  lastActive: string;
  activityCount: number;
  type: 'search' | 'chat' | 'sentiment';
}

export const createDashboardFactory = () => ({
  buildStats: (overrides: Partial<DashboardStats> = {}): DashboardStats => ({
    totalSearches: faker.number.int({ min: 100, max: 10000 }),
    totalConversations: faker.number.int({ min: 10, max: 1000 }),
    totalSentimentAnalyses: faker.number.int({ min: 20, max: 2000 }),
    averageResponseTime: faker.number.float({ min: 0.5, max: 5.0, precision: 0.1 }),
    userGrowth: faker.number.float({ min: -10, max: 50, precision: 0.1 }),
    popularQueries: Array.from({ length: 5 }, (_, index) => ({
      query: faker.lorem.words({ min: 1, max: 3 }),
      count: faker.number.int({ min: 10, max: 100 }) - (index * 10),
    })),
    ...overrides,
  }),

  buildTimeSeriesData: (days = 30): TimeSeriesData[] =>
    Array.from({ length: days }, (_, index) => ({
      date: faker.date.past({ days: index }).toISOString().split('T')[0],
      searches: faker.number.int({ min: 20, max: 200 }),
      conversations: faker.number.int({ min: 5, max: 50 }),
      sentimentAnalyses: faker.number.int({ min: 10, max: 100 }),
    })),

  buildUserActivityData: (count = 50): UserActivityData[] =>
    Array.from({ length: count }, () => ({
      userId: faker.string.uuid(),
      userName: faker.person.fullName(),
      lastActive: faker.date.recent().toISOString(),
      activityCount: faker.number.int({ min: 1, max: 50 }),
      type: faker.helpers.arrayElement(['search', 'chat', 'sentiment']),
    })),

  // Predefined test data
  testStats: (): DashboardStats => this.buildStats({
    totalSearches: 1250,
    totalConversations: 45,
    totalSentimentAnalyses: 89,
    averageResponseTime: 1.2,
    userGrowth: 15.5,
    popularQueries: [
      { query: 'react testing', count: 45 },
      { query: 'web3 search', count: 38 },
      { query: 'AI chat', count: 32 },
      { query: 'sentiment analysis', count: 28 },
      { query: 'dashboard', count: 25 },
    ],
  }),

  emptyStats: (): DashboardStats => this.buildStats({
    totalSearches: 0,
    totalConversations: 0,
    totalSentimentAnalyses: 0,
    averageResponseTime: 0,
    userGrowth: 0,
    popularQueries: [],
  }),

  // Growing trend data
  growingTrendStats: (): DashboardStats => this.buildStats({
    totalSearches: 5000,
    totalConversations: 250,
    totalSentimentAnalyses: 400,
    averageResponseTime: 0.8,
    userGrowth: 45.2,
    popularQueries: [
      { query: 'AI tools', count: 120 },
      { query: 'testing frameworks', count: 95 },
      { query: 'web development', count: 87 },
      { query: 'machine learning', count: 76 },
      { query: 'blockchain', count: 65 },
    ],
  }),

  // Declining trend data
  decliningTrendStats: (): DashboardStats => this.buildStats({
    totalSearches: 800,
    totalConversations: 20,
    totalSentimentAnalyses: 35,
    averageResponseTime: 2.5,
    userGrowth: -5.3,
    popularQueries: [
      { query: 'old query', count: 15 },
      { query: 'another old', count: 12 },
      { query: 'deprecated', count: 8 },
    ],
  }),

  // Create realistic weekly data
  createWeeklyData: (): TimeSeriesData[] => {
    const data: TimeSeriesData[] = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      // Weekends have lower activity
      const isWeekend = date.getDay() === 0 || date.getDay() === 6;
      const multiplier = isWeekend ? 0.6 : 1;
      
      data.push({
        date: date.toISOString().split('T')[0],
        searches: Math.floor(faker.number.int({ min: 50, max: 200 }) * multiplier),
        conversations: Math.floor(faker.number.int({ min: 10, max: 50 }) * multiplier),
        sentimentAnalyses: Math.floor(faker.number.int({ min: 20, max: 80 }) * multiplier),
      });
    }
    
    return data;
  },

  // Create monthly trend data
  createMonthlyTrend: (months = 12): TimeSeriesData[] => {
    const data: TimeSeriesData[] = [];
    const today = new Date();
    
    for (let i = months - 1; i >= 0; i--) {
      const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
      
      // Simulate growth trend
      const growthFactor = 1 + (i * 0.05); // 5% growth per month
      
      data.push({
        date: date.toISOString().split('T')[0],
        searches: Math.floor(faker.number.int({ min: 500, max: 2000 }) * growthFactor),
        conversations: Math.floor(faker.number.int({ min: 100, max: 500 }) * growthFactor),
        sentimentAnalyses: Math.floor(faker.number.int({ min: 200, max: 800 }) * growthFactor),
      });
    }
    
    return data;
  },
});

export const dashboardFactory = createDashboardFactory();
