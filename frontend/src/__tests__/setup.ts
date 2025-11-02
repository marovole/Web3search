// Test setup file - imports all testing utilities and sets up global test environment

// Import MSW server setup
import { setupMockServer } from './mocks/server';

// Import factories for easy access
import * as factories from './factories';

// Import utilities
import * as utils from './utils';

// Setup MSW server for all tests
setupMockServer();

// Make factories and utilities globally available for tests
global.factories = factories;
global.utils = utils;

// Global test helpers
global.testHelpers = utils.testHelpers;
global.mockHelpers = utils.mockHelpers;
global.a11yHelpers = utils.a11yHelpers;

// Add custom matchers
import '@testing-library/jest-dom';

// Add accessibility matchers
import { toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

// Global test configuration
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
  
  // Reset localStorage and sessionStorage
  localStorage.clear();
  sessionStorage.clear();
  
  // Reset console methods to avoid noise in tests
  jest.spyOn(console, 'error').mockImplementation(() => {});
  jest.spyOn(console, 'warn').mockImplementation(() => {});
});

afterEach(() => {
  // Restore console methods after each test
  console.error.mockRestore();
  console.warn.mockRestore();
});

// Export for use in test files
export { factories, utils };
export { testHelpers, mockHelpers, a11yHelpers } from './utils';
