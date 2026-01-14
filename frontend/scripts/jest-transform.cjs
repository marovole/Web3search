const { createTransformer } = require('ts-jest').default

const tsJestTransformer = createTransformer({
  tsconfig: {
    module: 'CommonJS',
    jsx: 'react-jsx',
    esModuleInterop: true,
    allowJs: true,
  },
})

module.exports = {
  process(sourceText, sourcePath, config, options) {
    const replaced = sourceText.replace(/import\.meta\.env/g, 'globalThis.__VITE_ENV__')
    return tsJestTransformer.process(replaced, sourcePath, config, options)
  },
}
