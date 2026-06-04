import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    include: ['src/**/*.test.{ts,tsx}'],
    env: {
      VITE_API_URL: 'http://localhost:8000/api/v1',
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: [
        'src/app/api/**/*.ts',
        'src/app/hooks/**/*.ts',
        'src/app/components/CarCard.tsx',
        'src/app/components/ThemeToggle.tsx',
        'src/app/components/Header.tsx',
      ],
      exclude: ['src/app/components/ui/**'],
    },
  },
});
