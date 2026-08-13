import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SAMPLE_PDF = path.join(__dirname, '..', 'fixtures', 'sample.pdf')

test('complete RAG flow: upload a document, enable RAG, and get a grounded answer', async ({
  page,
}) => {
  await page.goto('/documents')

  await page.getByTestId('upload-zone').click()
  await page.setInputFiles('input[type="file"]', SAMPLE_PDF)
  await expect(page.getByTestId('document-badge').getByText('indexado')).toBeVisible({
    timeout: 15000,
  })

  await page.goto('/')

  await page.getByTestId('rag-toggle').click()

  await page.getByTestId('chat-input').fill('Qual o tema principal do documento?')
  await page.getByTestId('send-button').click()

  await expect(page.getByTestId('assistant-message')).toBeVisible({ timeout: 30000 })
})
