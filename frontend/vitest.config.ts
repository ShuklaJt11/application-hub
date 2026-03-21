import path from 'path';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/features/common/components'),
      '@hooks': path.resolve(__dirname, './src/features/common/hooks'),
      '@utils': path.resolve(__dirname, './src/features/common/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      '@features': path.resolve(__dirname, './src/features'),
      '@api': path.resolve(__dirname, './src/api'),
      '@styles': path.resolve(__dirname, './src/styles'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    clearMocks: true,
  },
});
