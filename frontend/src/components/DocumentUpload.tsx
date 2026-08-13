import { useCallback, useRef, useState } from 'react'
import type { IndexedDocument } from '../types'
import { AlertCircleIcon, CheckCircleIcon, FileIcon, UploadCloudIcon } from './icons'

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
    <div className="flex flex-col gap-5">
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
        className={`group flex cursor-pointer flex-col items-center gap-3 rounded-2xl border-2 border-dashed p-10 text-center transition-colors ${
          isDragging
            ? 'border-indigo-400 bg-indigo-500/10'
            : 'border-white/15 bg-white/[0.02] hover:border-white/25 hover:bg-white/[0.04]'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(event) => handleFiles(event.target.files)}
        />
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-2xl transition-colors ${
            isDragging ? 'bg-indigo-500/20 text-indigo-300' : 'bg-white/5 text-slate-400 group-hover:text-slate-300'
          }`}
        >
          <UploadCloudIcon className="h-6 w-6" />
        </div>
        <p className="text-sm font-medium text-slate-300">
          {isUploading ? 'Enviando e indexando…' : 'Arraste um arquivo ou clique para selecionar'}
        </p>
        <p className="text-xs text-slate-600">PDF, DOCX ou TXT</p>
      </div>

      {error && (
        <p
          data-testid="upload-error"
          className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-300"
        >
          <AlertCircleIcon className="h-4 w-4 shrink-0" />
          {error}
        </p>
      )}

      {documents.length > 0 && (
        <ul className="flex flex-col gap-2">
          {documents.map((document) => (
            <li
              key={document.id}
              data-testid="document-item"
              className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.02] px-3.5 py-2.5"
            >
              <FileIcon className="h-4 w-4 shrink-0 text-slate-500" />
              <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="truncate text-sm text-slate-200">{document.filename}</span>
                {document.summary && (
                  <p
                    data-testid="document-summary"
                    className="line-clamp-2 text-xs text-slate-500"
                  >
                    {document.summary}
                  </p>
                )}
              </div>
              <span
                data-testid="document-badge"
                className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                  document.status === 'error'
                    ? 'bg-red-500/15 text-red-300'
                    : 'bg-emerald-500/15 text-emerald-300'
                }`}
              >
                {document.status === 'error' ? (
                  <AlertCircleIcon className="h-3 w-3" />
                ) : (
                  <CheckCircleIcon className="h-3 w-3" />
                )}
                {document.status === 'error' ? 'erro' : 'indexado'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
