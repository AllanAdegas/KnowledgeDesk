import type { ChatMessage } from '../types'

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div
      data-testid={isUser ? 'user-message' : 'assistant-message'}
      className={`max-w-[75%] rounded-lg px-4 py-2 ${
        isUser ? 'ml-auto bg-blue-600 text-white' : 'mr-auto bg-gray-100 text-gray-900'
      }`}
    >
      <p className="whitespace-pre-wrap break-words">
        {message.content}
        {message.isStreaming && (
          <span data-testid="streaming-cursor" className="ml-0.5 animate-pulse">
            ▍
          </span>
        )}
      </p>
    </div>
  )
}
