import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Bundle分析插件
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
      template: 'treemap', // 使用treemap视图更清晰地显示
    }),
    // PWA插件
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'mask-icon.svg'],
      manifest: {
        name: 'Web3 AI Search Engine',
        short_name: 'Web3search',
        description: 'Web3加密货币AI搜索引擎 - 免费、开源、专业级研究工具',
        theme_color: '#667eea',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: 'icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable'
          },
          {
            src: 'icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // 预缓存重要资源
        additionalManifestEntries: [
          { url: '/', revision: null },
          { url: '/manifest.webmanifest', revision: null },
        ],
        runtimeCaching: [
          // API缓存策略
          {
            urlPattern: /^https:\/\/.*\.onrender\.com\/api\/v1\//,
            handler: 'NetworkFirst',
            method: 'GET',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 10 * 60, // 10分钟
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
              // 添加网络错误时的回退
              networkTimeoutSeconds: 3,
            },
          },
          // 健康检查 - 频繁更新
          {
            urlPattern: /^https:\/\/.*\.onrender\.com\/api\/v1\/health/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'health-cache',
              expiration: {
                maxEntries: 5,
                maxAgeSeconds: 30, // 30秒
              },
            },
          },
          // 报告数据 - 较长缓存
          {
            urlPattern: /^https:\/\/.*\.onrender\.com\/api\/v1\/reports/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'reports-cache',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 24 * 60 * 60, // 24小时
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          // 用户数据 - 中等缓存
          {
            urlPattern: /^https:\/\/.*\.onrender\.com\/api\/v1\/users/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'user-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60, // 1小时
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          // 静态资源优化
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 7 * 24 * 60 * 60, // 7天
              },
            },
          },
          // 字体文件
          {
            urlPattern: /\.(?:woff2?|ttf|eot)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 365 * 24 * 60 * 60, // 1年
              },
            },
          },
        ],
        cleanupOutdatedCaches: true,
        skipWaiting: true,
        clientsClaim: true,
        // 导航预加载
        navigateFallback: '/',
        navigateFallbackDenylist: [/^\/api\//],
      },
      devOptions: {
        enabled: false, // 开发环境禁用，避免干扰
        type: 'module',
      },
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
          const fs = require('fs')
          const path = require('path')
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
    sourcemap: true,
    // 启用CSS代码分割
    cssCodeSplit: true,
    // 设置chunk大小警告限制
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // 手动chunk分离策略 - 首屏优化
        manualChunks(id) {
          // 将Node_modules分离到单独的chunk
          if (id.includes('node_modules')) {
            // React核心库分离
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {
              return 'react-vendor'
            }
            // UI组件库分离
            if (id.includes('@radix-ui') || id.includes('@shadcn')) {
              return 'ui-vendor'
            }
            // 动画库分离
            if (id.includes('framer-motion') || id.includes('motion')) {
              return 'animation-vendor'
            }
            // Markdown相关库分离（按需加载）
            if (id.includes('react-markdown') || id.includes('remark-') || id.includes('micromark')) {
              return 'markdown-vendor'
            }
            // 代码高亮库分离（按需加载）
            if (id.includes('react-syntax-highlighter') || id.includes('highlight.js') || id.includes('prismjs')) {
              return 'syntax-vendor'
            }
            // 表单库分离
            if (id.includes('react-hook-form') || id.includes('@hookform')) {
              return 'form-vendor'
            }
            // 验证库分离
            if (id.includes('zod')) {
              return 'validation-vendor'
            }
            // 工具库分离
            if (id.includes('lucide-react') || id.includes('axios') || id.includes('clsx') || id.includes('tailwind-merge') || id.includes('class-variance-authority')) {
              return 'utils-vendor'
            }
            // 监控库分离（可以延迟加载）
            if (id.includes('@sentry') || id.includes('sentry')) {
              return 'monitor-vendor'
            }
            // Chart.js或图表库分离（如果将来添加）
            if (id.includes('chart.js') || id.includes('recharts') || id.includes('d3')) {
              return 'chart-vendor'
            }
            // 其他第三方库
            return 'vendor'
          }
          // 页面组件懒加载分离
          if (id.includes('/pages/')) {
            return 'pages'
          }
          // 组件库分离
          if (id.includes('/components/')) {
            return 'components'
          }
          // 服务和工具分离
          if (id.includes('/services/') || id.includes('/utils/') || id.includes('/hooks/')) {
            return 'utils'
          }
        },
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
    // 压缩配置
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: true,
        pure_funcs: ['console.log'],
      },
      mangle: {
        safari10: true,
      },
    },
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
    ],
    exclude: [
      // 排除大型库，让它们按需加载
      'react-markdown',
      'react-syntax-highlighter',
      'remark-gfm',
      // 排除监控库，延迟加载
      '@sentry/react',
      '@sentry/tracing',
    ],
    // 预构建依赖的浏览器缓存
    force: true,
  },
})
