import { faker } from '@faker-js/faker';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar: string | null;
  preferences: UserPreferences;
  subscription: UserSubscription;
  createdAt: string;
  updatedAt: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: boolean;
}

export interface UserSubscription {
  plan: 'free' | 'pro' | 'enterprise';
  expiresAt: string;
}

export const createUserFactory = () => ({
  build: (overrides: Partial<User> = {}): User => ({
    id: faker.string.uuid(),
    email: faker.internet.email(),
    name: faker.person.fullName(),
    avatar: faker.datatype.boolean() ? faker.image.avatar() : null,
    preferences: {
      theme: faker.helpers.arrayElement(['light', 'dark', 'system']),
      language: 'en',
      notifications: faker.datatype.boolean(),
    },
    subscription: {
      plan: faker.helpers.arrayElement(['free', 'pro', 'enterprise']),
      expiresAt: faker.date.future().toISOString(),
    },
    createdAt: faker.date.past().toISOString(),
    updatedAt: faker.date.recent().toISOString(),
    ...overrides,
  }),

  buildMany: (count: number, overrides: Partial<User> = {}): User[] =>
    Array.from({ length: count }, () => this.build(overrides)),

  // Predefined users for common test scenarios
  testUser: (): User => this.build({
    id: 'test-user-1',
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
  }),

  freeUser: (): User => this.build({
    subscription: {
      plan: 'free',
      expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    },
  }),

  enterpriseUser: (): User => this.build({
    subscription: {
      plan: 'enterprise',
      expiresAt: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
    },
  }),
});

export const userFactory = createUserFactory();
