import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../types'
import { MessageBubble } from './MessageBubble'

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
      <div data-testid="chat-empty-state" className="flex flex-1 items-center justify-center text-gray-400">
        Envie uma mensagem para começar a conversa.
      </div>
    )
  }

  return (
    <div data-testid="chat-window" className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isStreaming && (
        <div data-testid="streaming-indicator" className="text-sm text-gray-400">
          Respondendo…
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
