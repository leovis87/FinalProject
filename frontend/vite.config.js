import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      // 백엔드 API 서버 프록시
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // AI 주제 추천(RAG) 서버 프록시
      '/rag': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // 실시간 토론 소켓 프록시
      '/socket.io': {
        target: 'http://localhost:8000',
        ws: true,
      },
    },
  },
})