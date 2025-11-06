import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/// <reference types="vitest" />
/// <reference types="vite/client" />

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  server: {
    port: 3002,
    host: true,
    strictPort: true,
    https: {
      key: path.resolve(__dirname, '../frontend/ssl/nginx-selfsigned.key'),
      cert: path.resolve(__dirname, '../frontend/ssl/nginx-selfsigned.crt'),
    },
    proxy: {
      // Proxy API calls to backend services
      '/api': {
        target: 'https://localhost:3000',
        changeOrigin: true,
        secure: false,
      },
      '/auth': {
        target: 'https://localhost:3000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'wss://localhost:8011',
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'esbuild', // Enable minification
    cssMinify: true, // Enable CSS minification
    reportCompressedSize: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'state-vendor': ['@reduxjs/toolkit', 'react-redux', 'zustand'],
          'query-vendor': ['@tanstack/react-query', 'axios'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@features': path.resolve(__dirname, './src/features'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@services': path.resolve(__dirname, './src/services'),
      '@store': path.resolve(__dirname, './src/store'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@styles': path.resolve(__dirname, './src/styles'),
    },
  },

  // @ts-expect-error - Vitest config not recognized by Vite types
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    css: true,
  },
})
