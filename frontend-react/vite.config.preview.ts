import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/// <reference types="vitest" />

// Preview configuration with HTTPS
export default defineConfig({
  plugins: [react()],

  preview: {
    port: 3003,
    host: true,
    strictPort: true,
    https: {
      key: path.resolve(__dirname, '../frontend/ssl/nginx-selfsigned.key'),
      cert: path.resolve(__dirname, '../frontend/ssl/nginx-selfsigned.crt'),
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'esbuild',
    cssMinify: true,
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
})
