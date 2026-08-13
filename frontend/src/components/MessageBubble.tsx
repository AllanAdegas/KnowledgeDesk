import type { ChatMessage } from '../types'

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex animate-fade-in-up gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
          isUser
            ? 'bg-white/10 text-slate-200'
            : 'bg-gradient-to-br from-indigo-400 via-violet-500 to-fuchsia-500 text-white'
        }`}
      >
        {isUser ? 'Eu' : 'K'}
      </div>

      <div
        data-testid={isUser ? 'user-message' : 'assistant-message'}
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed shadow-sm ${
          isUser
            ? 'rounded-tr-sm bg-gradient-to-br from-indigo-500 to-violet-600 text-white'
            : 'rounded-tl-sm border border-white/10 bg-white/[0.04] text-slate-100'
        }`}
      >
        <p className="whitespace-pre-wrap break-words">
          {message.content}
          {message.isStreaming && (
            <span data-testid="streaming-cursor" className="ml-0.5 animate-pulse text-indigo-300">
              ▍
            </span>
          )}
        </p>
      </div>
    </div>
  )
}
