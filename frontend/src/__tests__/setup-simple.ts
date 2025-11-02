// Simple test setup file - imports testing utilities without MSW

// Import factories for easy access
import * as factories from './factories';

// Import utilities (excluding mock helpers that depend on MSW)
import { testHelpers, a11yHelpers } from './utils';

// Make factories and utilities globally available for tests
global.factories = factories;
global.testHelpers = testHelpers;
global.a11yHelpers = a11yHelpers;

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
export { factories, testHelpers, a11yHelpers };
