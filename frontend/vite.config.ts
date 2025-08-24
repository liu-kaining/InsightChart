import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: process.env.DOCKER_ENV === 'true' ? 3000 : 3003,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.DOCKER_ENV === 'true' 
          ? 'http://backend-dev:5000'  // Docker环境中使用服务名和内部端口
          : 'http://localhost:5004',   // 本地开发环境使用外部映射端口
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue'],
          echarts: ['echarts'],
          elementPlus: ['element-plus'],
        },
      },
    },
  },
})