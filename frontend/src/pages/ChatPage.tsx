import { useState, type FormEvent } from 'react'
import { ChatWindow } from '../components/ChatWindow'
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
      <aside className="w-64 shrink-0 border-r border-gray-200 p-4">
        <div className="mb-4 flex items-center justify-between">
          <span className="font-medium">Documentos</span>
          <label className="flex items-center gap-2 text-sm">
            <input
              data-testid="rag-toggle"
              type="checkbox"
              checked={ragEnabled}
              onChange={(event) => setRagEnabled(event.target.checked)}
            />
            RAG
          </label>
        </div>
        <ul className="flex flex-col gap-1 text-sm text-gray-600">
          {documents.map((document) => (
            <li key={document.id}>{document.filename}</li>
          ))}
        </ul>
      </aside>

      <div className="flex flex-1 flex-col">
        <ChatWindow messages={messages} isStreaming={isStreaming} />

        <form onSubmit={handleSubmit} className="flex gap-2 border-t border-gray-200 p-4">
          <input
            data-testid="chat-input"
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            placeholder="Digite sua mensagem…"
            className="flex-1 rounded border border-gray-300 px-3 py-2"
          />
          <button
            data-testid="send-button"
            type="submit"
            disabled={isStreaming || !inputValue.trim()}
            className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
          >
            Enviar
          </button>
        </form>
      </div>
    </div>
  )
}
