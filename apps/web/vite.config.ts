import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath, URL } from 'node:url';

// Proxy /api to backend during dev. Override target with VITE_PROXY_TARGET or set VITE_API_BASE in the app.
const target = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@/components': fileURLToPath(new URL('./src/components', import.meta.url)),
      '@/types': fileURLToPath(new URL('./src/types', import.meta.url)),
      '@/lib': fileURLToPath(new URL('./src/lib', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': {
        target,
        changeOrigin: true,
      },
    },
  },
});