import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  envDir: '..',
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:8080',
      '/devices': 'http://127.0.0.1:8081',
      '/notifications': 'http://127.0.0.1:8081',
      '/telemetry': 'http://127.0.0.1:8081',
      '/stream': 'http://127.0.0.1:8081',
    },
  },
})
