import { useState, type FormEvent } from 'react'
import { ChatWindow } from '../components/ChatWindow'
import { DocsIcon, FileIcon, SendIcon } from '../components/icons'
import { useChat } from '../hooks/useChat'
import { useDocuments } from '../hooks/useDocuments'

export function ChatPage() {
  const [ragEnabled, setRagEnabled] = useState(false)
  const { messages, sendMessage, isStreaming } = useChat({ ragEnabled })
  const { documents } = useDocuments()
  const [inputValue, setInputValue] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault()
    if (!inputValue.trim() || isStreaming) return
    const toSend = inputValue
    setInputValue('')
    void sendMessage(toSend)
  }

  return (
    <div className="flex h-full">
      <aside className="flex w-64 shrink-0 flex-col gap-4 border-r border-white/10 bg-white/[0.02] p-4">
        <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2.5">
          <div className="flex items-center gap-1.5 text-sm font-medium text-slate-200">
            <SparkleLabel />
            RAG
          </div>
          <label
            className={`relative block h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors ${
              ragEnabled ? 'bg-indigo-500' : 'bg-white/15'
            }`}
          >
            <input
              data-testid="rag-toggle"
              type="checkbox"
              checked={ragEnabled}
              onChange={(event) => setRagEnabled(event.target.checked)}
              className="absolute inset-0 z-10 h-full w-full cursor-pointer opacity-0"
              aria-label="Ativar RAG"
            />
            <span
              className={`pointer-events-none absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${
                ragEnabled ? 'translate-x-4' : ''
              }`}
            />
          </label>
        </div>

        <div className="flex items-center gap-1.5 px-1 text-xs font-semibold tracking-wide text-slate-500 uppercase">
          <DocsIcon className="h-3.5 w-3.5" />
          Documentos
        </div>

        {documents.length === 0 ? (
          <p className="px-1 text-sm text-slate-600">Nenhum documento indexado ainda.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {documents.map((document) => (
              <li
                key={document.id}
                className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-slate-300 hover:bg-white/5"
              >
                <FileIcon className="h-4 w-4 shrink-0 text-slate-500" />
                <span className="truncate">{document.filename}</span>
              </li>
            ))}
          </ul>
        )}
      </aside>

      <div className="flex flex-1 flex-col">
        <ChatWindow messages={messages} isStreaming={isStreaming} />

        <form onSubmit={handleSubmit} className="border-t border-white/10 bg-white/[0.02] p-4">
          <div className="mx-auto flex max-w-3xl items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] p-1.5 pl-4 shadow-lg shadow-black/20 focus-within:border-indigo-400/50">
            <input
              data-testid="chat-input"
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              placeholder="Digite sua mensagem…"
              className="min-w-0 flex-1 bg-transparent text-[15px] text-slate-100 placeholder:text-slate-500 focus:outline-none"
            />
            <button
              data-testid="send-button"
              type="submit"
              disabled={isStreaming || !inputValue.trim()}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white transition-opacity disabled:opacity-30"
              aria-label="Enviar"
            >
              <SendIcon className="h-4 w-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function SparkleLabel() {
  return (
    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-300">
      <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
    </span>
  )
}
