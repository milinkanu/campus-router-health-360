import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
  build: {
    // Vercel's @vercel/static-build looks for output in `dist/` by default
    outDir: 'dist',
  },
})
