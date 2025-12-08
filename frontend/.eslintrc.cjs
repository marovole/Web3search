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
    'react-refresh/only-export-components': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-unused-vars': 'off',
    '@typescript-eslint/no-var-requires': 'off',
    'no-extra-semi': 'off',
    'no-case-declarations': 'off',
    'react-hooks/rules-of-hooks': 'off',
    'react-hooks/exhaustive-deps': 'off',
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
