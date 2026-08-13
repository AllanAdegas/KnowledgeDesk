import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DocumentUpload } from '../../src/components/DocumentUpload'
import type { IndexedDocument } from '../../src/types'

function makeFile(name: string, type: string): File {
  return new File(['conteúdo de teste'], name, { type })
}

describe('DocumentUpload', () => {
  it('renders dropzone', () => {
    render(<DocumentUpload documents={[]} isUploading={false} error={null} onUpload={vi.fn()} />)

    expect(screen.getByTestId('upload-zone')).toBeInTheDocument()
  })

  it('calls onUpload with file when selected via the hidden input', async () => {
    const onUpload = vi.fn()
    const user = userEvent.setup()
    render(<DocumentUpload documents={[]} isUploading={false} error={null} onUpload={onUpload} />)

    const file = makeFile('report.pdf', 'application/pdf')
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await user.upload(input, file)

    expect(onUpload).toHaveBeenCalledWith(file)
  })

  it('shows error state for invalid file type', () => {
    render(
      <DocumentUpload
        documents={[]}
        isUploading={false}
        error="Formato não suportado. Use: .pdf, .docx, .txt"
        onUpload={vi.fn()}
      />,
    )

    expect(screen.getByTestId('upload-error')).toHaveTextContent('Formato não suportado')
  })

  it('renders indexed documents with a badge', () => {
    const documents: IndexedDocument[] = [
      { id: '1', filename: 'policy.pdf', chunks_count: 4, status: 'indexed' },
    ]

    render(
      <DocumentUpload documents={documents} isUploading={false} error={null} onUpload={vi.fn()} />,
    )

    expect(screen.getByTestId('document-item')).toHaveTextContent('policy.pdf')
    expect(screen.getByTestId('document-badge')).toHaveTextContent('indexado')
  })

  it('shows the document summary when present', () => {
    const documents: IndexedDocument[] = [
      {
        id: '1',
        filename: 'policy.pdf',
        chunks_count: 4,
        status: 'indexed',
        summary: 'Política de trabalho remoto: duas vezes por semana no escritório.',
      },
    ]

    render(
      <DocumentUpload documents={documents} isUploading={false} error={null} onUpload={vi.fn()} />,
    )

    expect(screen.getByTestId('document-summary')).toHaveTextContent('Política de trabalho remoto')
  })

  it('does not render a summary element when the document has no summary', () => {
    const documents: IndexedDocument[] = [
      { id: '1', filename: 'policy.pdf', chunks_count: 4, status: 'indexed' },
    ]

    render(
      <DocumentUpload documents={documents} isUploading={false} error={null} onUpload={vi.fn()} />,
    )

    expect(screen.queryByTestId('document-summary')).not.toBeInTheDocument()
  })

  it('shows an "enviando" label while uploading', () => {
    render(<DocumentUpload documents={[]} isUploading={true} error={null} onUpload={vi.fn()} />)

    expect(screen.getByTestId('upload-zone')).toHaveTextContent('Enviando e indexando')
  })
})
