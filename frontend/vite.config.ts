import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    host: '0.0.0.0',
    proxy: {
      '/api': { target: 'http://localhost:9000', changeOrigin: true },
      '/y': { target: 'http://localhost:9000', changeOrigin: true },
      '/jieqi': { target: 'http://localhost:9000', changeOrigin: true },
      '/fangjia': { target: 'http://localhost:9000', changeOrigin: true },
      '/sitemap.xml': { target: 'http://localhost:9000', changeOrigin: true },
    },
  },
})
