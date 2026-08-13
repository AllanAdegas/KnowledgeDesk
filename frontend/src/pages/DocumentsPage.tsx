import { DocumentUpload } from '../components/DocumentUpload'
import { DocsIcon } from '../components/icons'
import { useDocuments } from '../hooks/useDocuments'

export function DocumentsPage() {
  const { documents, isUploading, error, upload } = useDocuments()

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-2xl px-6 py-10">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 text-indigo-300">
            <DocsIcon className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-100">Documentos</h1>
            <p className="text-sm text-slate-500">Envie arquivos para consultar com o assistente.</p>
          </div>
        </div>

        <DocumentUpload
          documents={documents}
          isUploading={isUploading}
          error={error}
          onUpload={(file) => void upload(file)}
        />
      </div>
    </div>
  )
}
