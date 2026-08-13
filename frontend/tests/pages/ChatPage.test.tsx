import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ChatPage } from '../../src/pages/ChatPage'
import * as apiClient from '../../src/api/client'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ChatPage', () => {
  it('sends a message on submit and renders the streamed reply', async () => {
    vi.spyOn(apiClient, 'createChatSession').mockResolvedValue('session-1')
    vi.spyOn(apiClient, 'listDocuments').mockResolvedValue([])
    vi.spyOn(apiClient, 'streamChatMessage').mockImplementation(
      async (_sessionId, _message, _rag, onToken, onDone) => {
        onToken('Olá!')
        onDone()
      },
    )

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByTestId('chat-input'), 'oi')
    await waitFor(() => expect(screen.getByTestId('send-button')).not.toBeDisabled())
    await user.click(screen.getByTestId('send-button'))

    await waitFor(() => expect(screen.getByTestId('assistant-message')).toHaveTextContent('Olá!'))
    expect(screen.getByTestId('user-message')).toHaveTextContent('oi')
  })

  it('toggles the RAG checkbox', async () => {
    vi.spyOn(apiClient, 'createChatSession').mockResolvedValue('session-1')
    vi.spyOn(apiClient, 'listDocuments').mockResolvedValue([])

    const user = userEvent.setup()
    render(<ChatPage />)

    const toggle = screen.getByTestId('rag-toggle') as HTMLInputElement
    expect(toggle.checked).toBe(false)

    await user.click(toggle)

    expect(toggle.checked).toBe(true)
  })
})
