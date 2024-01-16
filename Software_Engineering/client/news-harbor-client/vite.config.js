import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": "/src",
    }
  },
  publicDir: 'public',
  server:  {
    proxy: {
      '/api': {
        target: "https://newsharbor.abenazzou.com/",
        changeOrigin:true
      }
    }
  }
})