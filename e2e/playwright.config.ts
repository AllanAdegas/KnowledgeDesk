import { defineConfig, devices } from '@playwright/test'

/**
 * E2E config for KnowledgeDesk.
 *
 * These tests exercise the real stack end-to-end — frontend, backend, and a
 * real local Ollama instance with the `llama3.2` and `nomic-embed-text`
 * models pulled. They are NOT run as part of `pytest`/`vitest` and are not
 * mocked; see the root README's "Running the E2E tests" section for
 * prerequisites before running `npm test` in this directory.
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['html', { open: 'never' }]],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
