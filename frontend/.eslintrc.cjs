module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs', 'tests', 'playwright-report', 'src/__tests__', 'src/components/ui'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': 'warn',
    '@typescript-eslint/no-var-requires': 'warn',
    'no-extra-semi': 'warn',
    'no-case-declarations': 'warn',
    'react-hooks/rules-of-hooks': 'warn',
  },
  overrides: [
    {
      files: ['**/__tests__/**', 'tests/**/*', '**/*.test.*', '**/*.spec.*'],
      env: { jest: true, node: true },
      rules: {
        '@typescript-eslint/no-var-requires': 'off'
      }
    }
  ],
}
