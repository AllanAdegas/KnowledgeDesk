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
  // Real local LLM calls (llama3.2 on CPU) run well past Playwright's 30s
  // default, especially the agent's multi-step LangGraph flow (clarify ->
  // plan -> execute_tools -> respond can mean several sequential inferences).
  timeout: 180_000,
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
