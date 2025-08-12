import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Proxy /api to backend during dev. Override target with VITE_PROXY_TARGET or set VITE_API_BASE in the app.
const target = process.env.VITE_PROXY_TARGET || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@components': path.resolve(__dirname, 'src/components'),
      '@types': path.resolve(__dirname, 'src/types'),
      '@lib': path.resolve(__dirname, 'src/lib'),
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