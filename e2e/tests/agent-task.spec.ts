import { test, expect } from '@playwright/test'

test('agent completes a document listing task', async ({ page }) => {
  await page.goto('/agent')

  await page.getByTestId('task-input').fill('liste todos os documentos disponíveis')
  await page.getByTestId('run-task').click()

  // POST /api/agent/task runs the LangGraph agent synchronously to
  // completion (clarify -> plan -> execute_tools -> respond), each step a
  // real LLM call on local CPU — comfortably over a minute for llama3.2.
  await expect(page.getByTestId('agent-result')).toBeVisible({ timeout: 150_000 })
})
