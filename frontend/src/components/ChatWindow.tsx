import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../types'
import { MessageBubble } from './MessageBubble'
import { SparkleIcon } from './icons'

interface ChatWindowProps {
  messages: ChatMessage[]
  isStreaming: boolean
}

export function ChatWindow({ messages, isStreaming }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div
        data-testid="chat-empty-state"
        className="flex flex-1 flex-col items-center justify-center gap-3 text-center text-slate-500"
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/5 text-indigo-300">
          <SparkleIcon className="h-6 w-6" />
        </div>
        <p className="max-w-xs text-sm">Envie uma mensagem para começar a conversa.</p>
      </div>
    )
  }

  return (
    <div data-testid="chat-window" className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-6 sm:px-8">
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isStreaming && (
          <div
            data-testid="streaming-indicator"
            className="flex items-center gap-1.5 pl-9.5 text-xs font-medium text-slate-500"
          >
            <span className="inline-flex gap-0.5">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-500" />
            </span>
            Respondendo…
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
