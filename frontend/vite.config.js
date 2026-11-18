import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

function appShellManifest() {
  return {
    name: 'demka-app-shell-manifest',
    generateBundle(_options, bundle) {
      const assets = Object.keys(bundle)
        .filter((fileName) => /^assets\/.*\.(js|css|svg|woff2?)$/.test(fileName))
        .map((fileName) => `/${fileName}`);
      this.emitFile({
        type: 'asset',
        fileName: 'precache-manifest.json',
        source: JSON.stringify(assets),
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), appShellManifest()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
        },
      },
    },
  },
});