import { DocumentUpload } from '../components/DocumentUpload'
import { useDocuments } from '../hooks/useDocuments'

export function DocumentsPage() {
  const { documents, isUploading, error, upload } = useDocuments()

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-4 text-xl font-semibold">Documentos</h1>
      <DocumentUpload
        documents={documents}
        isUploading={isUploading}
        error={error}
        onUpload={(file) => void upload(file)}
      />
    </div>
  )
}
