import { useCallback, useEffect, useState } from 'react'
import { deleteDocument, listDocuments, uploadDocument } from '../api/client'
import type { IndexedDocument } from '../types'

interface UseDocumentsResult {
  documents: IndexedDocument[]
  isUploading: boolean
  error: string | null
  upload: (file: File) => Promise<void>
  remove: (id: string) => Promise<void>
  refresh: () => Promise<void>
}

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt']

function hasSupportedExtension(filename: string): boolean {
  const lowered = filename.toLowerCase()
  return SUPPORTED_EXTENSIONS.some((extension) => lowered.endsWith(extension))
}

/** Isolates all document fetch/upload logic away from DocumentsPage/DocumentUpload. */
export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<IndexedDocument[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const result = await listDocuments()
    setDocuments(result)
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const upload = useCallback(
    async (file: File) => {
      setError(null)

      if (!hasSupportedExtension(file.name)) {
        setError(`Formato não suportado. Use: ${SUPPORTED_EXTENSIONS.join(', ')}`)
        return
      }

      setIsUploading(true)
      try {
        await uploadDocument(file)
        await refresh()
      } catch {
        setError('Falha ao enviar ou indexar o documento.')
      } finally {
        setIsUploading(false)
      }
    },
    [refresh],
  )

  const remove = useCallback(
    async (id: string) => {
      await deleteDocument(id)
      await refresh()
    },
    [refresh],
  )

  return { documents, isUploading, error, upload, remove, refresh }
}
