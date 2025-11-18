import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import tsconfigPaths from 'vite-tsconfig-paths'
import fs from 'fs'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/', // Vercel 部署到根路径
  plugins: [
    react(),
    tsconfigPaths(), // 支持 TypeScript 路径别名解析
    // Bundle分析插件
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
      template: 'treemap', // 使用treemap视图更清晰地显示
    }),
    // 性能预算插件（自定义）
    {
      name: 'performance-budget',
      generateBundle(options, bundle) {
        const maxChunkSize = 800 * 1024 // 800KB per chunk (考虑到AI应用复杂度)
        const maxTotalSize = 3 * 1024 * 1024 // 3MB total (AI应用需要更多功能)
        const maxGzipSize = 300 * 1024 // 300KB gzipped per chunk

        let totalSize = 0
        let totalGzipSize = 0
        const warnings: string[] = []
        const chunks: Array<{
          name: string
          size: number
          gzipSize?: number
          formattedSize: string
          formattedGzipSize?: string
        }> = []

        for (const [fileName, chunk] of Object.entries(bundle)) {
          if (chunk.type === 'chunk') {
            const size = chunk.code.length
            totalSize += size
            const gzipSize = (chunk as any).gzipSize
            if (gzipSize) {
              totalGzipSize += gzipSize
            }

            chunks.push({
              name: fileName,
              size,
              gzipSize,
              formattedSize: `${(size / 1024).toFixed(2)}KB`,
              formattedGzipSize: gzipSize ? `${(gzipSize / 1024).toFixed(2)}KB` : undefined,
            })

            if (size > maxChunkSize) {
              warnings.push(`⚠️  Chunk ${fileName} exceeds ${maxChunkSize / 1024}KB: ${(size / 1024).toFixed(2)}KB`)
            }
            if (gzipSize && gzipSize > maxGzipSize) {
              warnings.push(`⚠️  Chunk ${fileName} (gzipped) exceeds ${maxGzipSize / 1024}KB: ${(gzipSize / 1024).toFixed(2)}KB`)
            }
          }
        }

        if (totalSize > maxTotalSize) {
          warnings.push(`⚠️  Total bundle size exceeds ${maxTotalSize / 1024 / 1024}MB: ${(totalSize / 1024 / 1024).toFixed(2)}MB`)
        }

        // 生成优化报告
        const report = {
          timestamp: new Date().toISOString(),
          summary: {
            totalChunks: chunks.length,
            totalSize: `${(totalSize / 1024 / 1024).toFixed(2)}MB`,
            totalGzipSize: totalGzipSize > 0 ? `${(totalGzipSize / 1024 / 1024).toFixed(2)}MB` : 'N/A',
            warnings: warnings.length,
          },
          chunks: chunks.sort((a, b) => b.size - a.size),
          warnings,
        }

        // 输出到控制台
        if (warnings.length > 0) {
          console.warn('\n🚨 Performance Budget Warnings:\n')
          warnings.forEach(warning => console.warn(warning))
          console.warn('\n📊 Bundle Size Report:')
          console.table(chunks.map(c => ({
            'Chunk': c.name.split('/').pop(),
            'Size': c.formattedSize,
            'Gzipped': c.formattedGzipSize || 'N/A',
          })))
          console.warn('\n')
        } else {
          console.log(`✅ Performance budget check passed`)
          console.log(`📊 Total bundle: ${(totalSize / 1024 / 1024).toFixed(2)}MB (${(totalGzipSize / 1024 / 1024).toFixed(2)}MB gzipped)`)
        }

        // 保存报告到文件（可选）
        if (process.env.GENERATE_BUNDLE_REPORT === 'true') {
          const reportPath = path.join(__dirname, 'dist', 'bundle-report.json')
          fs.writeFileSync(reportPath, JSON.stringify(report, null, 2))
          console.log(`📄 Bundle report saved to: ${reportPath}`)
        }
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.VITE_ENVIRONMENT !== 'production',
    // 启用CSS代码分割
    cssCodeSplit: true,
    // 设置chunk大小警告限制
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // 禁用手动代码分割，让Vite自动处理
        // manualChunks: undefined,
        // 优化chunk命名
        chunkFileNames: (chunkInfo) => {
          // 保持chunk名称的可读性
          const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId.split('/').pop() : 'chunk'
          return `js/[name]-[hash].js`
        },
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          // 按文件类型分离资源
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name)) {
            return `media/[name]-[hash][extname]`
          }
          if (/\.(png|jpe?g|gif|svg|ico|webp)(\?.*)?$/i.test(assetInfo.name)) {
            return `images/[name]-[hash][extname]`
          }
          if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name)) {
            return `fonts/[name]-[hash][extname]`
          }
          return `${ext}/[name]-[hash][extname]`
        },
      },
      // 外部依赖优化（如果有CDN版本）
      external: [],
    },
    // 压缩配置 - 使用esbuild替代terser以避免React初始化问题
    minify: 'esbuild',
    // terserOptions已移除，使用esbuild默认配置
  },
  // 优化依赖预构建
    optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'axios',
      'lucide-react',
      'clsx',
      'tailwind-merge',
      'class-variance-authority',
      'react-markdown',
      'remark-gfm',
    ],
    exclude: [
      // 排除大型库，让它们按需加载
      'react-syntax-highlighter',
      // 排除监控库，延迟加载
      '@sentry/react',
      '@sentry/tracing',
    ],
  },
})
