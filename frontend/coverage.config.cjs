// Coverage configuration for quality gates
module.exports = {
  // Coverage thresholds for different environments
  development: {
    statements: 50,
    branches: 50,
    functions: 50,
    lines: 50,
  },
  ci: {
    statements: 80,
    branches: 80,
    functions: 80,
    lines: 80,
  },
  
  // Files that require higher coverage
  highPriorityFiles: [
    'src/components/Auth/**/*.{ts,tsx}',
    'src/components/Search/**/*.{ts,tsx}',
    'src/components/Chat/**/*.{ts,tsx}',
    'src/hooks/**/*.{ts,tsx}',
    'src/utils/**/*.{ts,tsx}',
  ],
  
  // Files that can have lower coverage (UI-only components)
  lowPriorityFiles: [
    'src/components/ui/**/*.{ts,tsx}',
    'src/**/*.stories.{ts,tsx}',
  ],
  
  // Coverage report formats
  reportFormats: ['html', 'lcov', 'text', 'json-summary'],
  
  // Coverage directory
  coverageDirectory: 'coverage',
  
  // Coverage reporters
  coverageReporters: ['text', 'lcov', 'html'],
};
