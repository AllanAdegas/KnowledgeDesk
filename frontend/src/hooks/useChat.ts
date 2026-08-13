import { useCallback, useEffect, useRef, useState } from 'react'
import { createChatSession, streamChatMessage } from '../api/client'
import type { ChatMessage } from '../types'

interface UseChatOptions {
  ragEnabled: boolean
}

interface UseChatResult {
  messages: ChatMessage[]
  sendMessage: (content: string) => Promise<void>
  isStreaming: boolean
  sessionId: string | null
}

let messageIdCounter = 0
function nextMessageId(): string {
  messageIdCounter += 1
  return `msg-${messageIdCounter}`
}

/**
 * Central chat hook: owns session creation, message state, and SSE
 * streaming. Pages stay "dumb" and only render what this hook exposes.
 */
export function useChat({ ragEnabled }: UseChatOptions): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const sessionPromiseRef = useRef<Promise<string> | null>(null)

  useEffect(() => {
    if (sessionPromiseRef.current) return
    const promise = createChatSession()
    sessionPromiseRef.current = promise
    void promise.then(setSessionId)
  }, [])

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim()
      if (!trimmed) return

      const currentSessionId = sessionId ?? (await sessionPromiseRef.current)
      if (!currentSessionId) return

      const userMessage: ChatMessage = { id: nextMessageId(), role: 'user', content: trimmed }
      const assistantMessageId = nextMessageId()
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        isStreaming: true,
      }

      setMessages((previous) => [...previous, userMessage, assistantMessage])
      setIsStreaming(true)

      try {
        await streamChatMessage(
          currentSessionId,
          trimmed,
          ragEnabled,
          (token) => {
            setMessages((previous) =>
              previous.map((message) =>
                message.id === assistantMessageId
                  ? { ...message, content: message.content + token }
                  : message,
              ),
            )
          },
          () => {
            setMessages((previous) =>
              previous.map((message) =>
                message.id === assistantMessageId ? { ...message, isStreaming: false } : message,
              ),
            )
          },
        )
      } finally {
        setIsStreaming(false)
      }
    },
    [ragEnabled, sessionId],
  )

  return { messages, sendMessage, isStreaming, sessionId }
}
