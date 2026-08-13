import { test, expect } from '@playwright/test'

test('agent completes a document listing task', async ({ page }) => {
  await page.goto('/agent')

  await page.getByTestId('task-input').fill('liste todos os documentos disponíveis')
  await page.getByTestId('run-task').click()

  await expect(page.getByTestId('agent-result')).toBeVisible({ timeout: 60000 })
})
