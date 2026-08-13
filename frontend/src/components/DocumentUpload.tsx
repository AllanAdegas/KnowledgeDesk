import { useCallback, useRef, useState } from 'react'
import type { IndexedDocument } from '../types'

interface DocumentUploadProps {
  documents: IndexedDocument[]
  isUploading: boolean
  error: string | null
  onUpload: (file: File) => void
}

export function DocumentUpload({ documents, isUploading, error, onUpload }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = useCallback(
    (files: FileList | null) => {
      const file = files?.[0]
      if (file) onUpload(file)
    },
    [onUpload],
  )

  return (
    <div className="flex flex-col gap-4">
      <div
        data-testid="upload-zone"
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') inputRef.current?.click()
        }}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setIsDragging(false)
          handleFiles(event.dataTransfer.files)
        }}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(event) => handleFiles(event.target.files)}
        />
        <p className="text-gray-600">
          {isUploading ? 'Enviando e indexando…' : 'Arraste um arquivo ou clique para selecionar (PDF, DOCX, TXT)'}
        </p>
      </div>

      {error && (
        <p data-testid="upload-error" className="text-sm text-red-600">
          {error}
        </p>
      )}

      <ul className="flex flex-col gap-2">
        {documents.map((document) => (
          <li
            key={document.id}
            data-testid="document-item"
            className="flex items-center justify-between rounded border border-gray-200 px-3 py-2"
          >
            <span>{document.filename}</span>
            <span
              data-testid="document-badge"
              className={`rounded px-2 py-0.5 text-xs ${
                document.status === 'error'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-green-100 text-green-700'
              }`}
            >
              {document.status === 'error' ? 'erro' : 'indexado'}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
