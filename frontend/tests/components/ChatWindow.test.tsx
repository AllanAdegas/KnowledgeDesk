import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ChatWindow } from '../../src/components/ChatWindow'
import type { ChatMessage } from '../../src/types'

describe('ChatWindow', () => {
  it('renders empty state correctly', () => {
    render(<ChatWindow messages={[]} isStreaming={false} />)

    expect(screen.getByTestId('chat-empty-state')).toBeInTheDocument()
  })

  it('displays user and assistant messages', () => {
    const messages: ChatMessage[] = [
      { id: '1', role: 'user', content: 'Olá' },
      { id: '2', role: 'assistant', content: 'Oi, tudo bem?' },
    ]

    render(<ChatWindow messages={messages} isStreaming={false} />)

    expect(screen.getByTestId('user-message')).toHaveTextContent('Olá')
    expect(screen.getByTestId('assistant-message')).toHaveTextContent('Oi, tudo bem?')
  })

  it('shows streaming indicator when isStreaming is true', () => {
    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: 'Olá' }]

    render(<ChatWindow messages={messages} isStreaming={true} />)

    expect(screen.getByTestId('streaming-indicator')).toBeInTheDocument()
  })

  it('does not show streaming indicator when isStreaming is false', () => {
    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: 'Olá' }]

    render(<ChatWindow messages={messages} isStreaming={false} />)

    expect(screen.queryByTestId('streaming-indicator')).not.toBeInTheDocument()
  })

  it('scrolls to bottom on new message', () => {
    const scrollIntoViewMock = vi.fn()
    HTMLDivElement.prototype.scrollIntoView = scrollIntoViewMock

    const messages: ChatMessage[] = [{ id: '1', role: 'user', content: 'Olá' }]
    render(<ChatWindow messages={messages} isStreaming={false} />)

    expect(scrollIntoViewMock).toHaveBeenCalled()
  })

  it('renders a blinking cursor for a streaming assistant message', () => {
    const messages: ChatMessage[] = [
      { id: '1', role: 'assistant', content: 'Escrevendo', isStreaming: true },
    ]

    render(<ChatWindow messages={messages} isStreaming={true} />)

    expect(screen.getByTestId('streaming-cursor')).toBeInTheDocument()
  })
})
