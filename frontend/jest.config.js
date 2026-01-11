import { defaults } from 'jest-config';

export default {
  // Use the Vite Jest preset
  preset: 'ts-jest/presets/default-esm',
  
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  
  // Module file extensions
  moduleFileExtensions: [...defaults.moduleFileExtensions, 'ts', 'tsx'],
  
  // Transform
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      useESM: true,
      tsconfig: {
        jsx: 'react-jsx',
        esModuleInterop: true,
      },
    }],
  },
  
  // Module name mapping for absolute imports
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^.+\\.module\\.(css|sass|scss)$': 'identity-obj-proxy',
    '^.+\\.(css|sass|scss)$': '<rootDir>/__mocks__/styleMock.js',
    '^.+\\.(jpg|jpeg|png|gif|webp|avif|svg)$': '<rootDir>/__mocks__/fileMock.js',
    '^(\\.\\./)*utils/env$': '<rootDir>/src/__tests__/mocks/envMock.ts',
    '^@/utils/env$': '<rootDir>/src/__tests__/mocks/envMock.ts',
    '^(\\.\\./)*utils/logger$': '<rootDir>/src/__tests__/mocks/loggerMock.ts',
    '^@/utils/logger$': '<rootDir>/src/__tests__/mocks/loggerMock.ts',
  },
  
  // Test file patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx}',
  ],
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts',
    '!src/**/*.stories.{ts,tsx}',
  ],
  
  // Coverage reporters
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],
  
  // Coverage thresholds - 设置合理的测试覆盖率要求
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 75,
      lines: 75,
      statements: 75,
    },
    // 关键安全相关文件要求更高覆盖率
    './src/utils/tokenManager.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './src/utils/inputValidation.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './src/services/api.ts': {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  
  // Ignore patterns
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/dist/',
    '<rootDir>/build/',
    '<rootDir>/src/__tests__/mocks/',
    '<rootDir>/src/__tests__/utils/',
    '<rootDir>/src/__tests__/factories/',
  ],
  
  // Transform ignore patterns - allow transformation of specific ES modules
  transformIgnorePatterns: [
    'node_modules/(?!(msw|@mswjs|until-async|@faker-js|faker|remark-gfm|react-markdown|unified|bail|is-plain-obj|trough|vfile|unist-util-stringify-position|unist-builder|remark-parse|mdast-util-from-markdown|mdast-util-to-markdown|micromark|decode-named-character-reference|character-entities|character-entities-legacy|character-reference-invalid|is-alphabetical|is-alphanumerical|is-decimal|is-hexadecimal|is-word-character|markdown-escape|remark-stringify|remark-rehype|rehype-remark|rehype-parse|hast-util-from-parse5|hast-util-to-parse5|hastscript|property-information|space-separated-tokens|comma-separated-tokens|web-namespaces|html-void-elements|parse5|ccount|escape-string-regexp|markdown-extensions|mdast-util-mdx-expression|mdast-util-mdx-jsx|mdast-util-mdxjs-esm|mdast-util-to-hast|mdast-util-to-string|micromark-core-commonmark|micromark-factory-destination|micromark-factory-label|micromark-factory-space|micromark-factory-title|micromark-factory-whitespace|micromark-util-character|micromark-util-chunked|micromark-util-combine-extensions|micromark-util-decode-numeric-character-reference|micromark-util-decode-string|micromark-util-encode|micromark-util-events-to-acorn|micromark-util-html-tag-name|micromark-util-normalize-identifier|micromark-util-resolve-all|micromark-util-subtokenize|micromark-util-symbol|micromark-util-syntax|micromark-util-classify-character)/)',
  ],

  // Test timeout (default: 5000ms)
  // Increased for async operations and slow CI environments
  testTimeout: 10000, // 10 seconds

  // Extensions to transform
  extensionsToTreatAsEsm: ['.ts', '.tsx'],
};
