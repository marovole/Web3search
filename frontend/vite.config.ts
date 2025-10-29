import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
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
    })
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
            // 工具库分离
            if (id.includes('lucide-react') || id.includes('axios') || id.includes('clsx') || id.includes('tailwind-merge')) {
              return 'utils-vendor'
            }
            // 监控库分离
            if (id.includes('@sentry')) {
              return 'monitor-vendor'
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
    ],
    // 预构建依赖的浏览器缓存
    force: true,
  },
  // 实验性功能
  experimental: {
    renderBuiltUrl(filename, { hostType }) {
      if (hostType === 'js') {
        return { js: `/${filename}` }
      } else {
        return { relative: true }
      }
    },
  },
})
