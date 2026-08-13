import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DocumentsPage } from '../../src/pages/DocumentsPage'
import * as apiClient from '../../src/api/client'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('DocumentsPage', () => {
  it('renders the upload zone and any previously indexed documents', async () => {
    vi.spyOn(apiClient, 'listDocuments').mockResolvedValue([
      { id: '1', filename: 'manual.pdf', chunks_count: 5, status: 'indexed' },
    ])

    render(<DocumentsPage />)

    expect(screen.getByTestId('upload-zone')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByTestId('document-item')).toHaveTextContent('manual.pdf'))
  })
})
