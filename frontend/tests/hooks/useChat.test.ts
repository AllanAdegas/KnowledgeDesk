import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useChat } from '../../src/hooks/useChat'
import * as apiClient from '../../src/api/client'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('useChat', () => {
  it('creates a session on mount', async () => {
    vi.spyOn(apiClient, 'createChatSession').mockResolvedValue('session-1')

    const { result } = renderHook(() => useChat({ ragEnabled: false }))

    await waitFor(() => expect(result.current.sessionId).toBe('session-1'))
  })

  it('accumulates streamed tokens into the assistant message', async () => {
    vi.spyOn(apiClient, 'createChatSession').mockResolvedValue('session-1')
    vi.spyOn(apiClient, 'streamChatMessage').mockImplementation(
      async (_sessionId, _message, _rag, onToken, onDone) => {
        onToken('Olá')
        onToken(' mundo')
        onDone()
      },
    )

    const { result } = renderHook(() => useChat({ ragEnabled: false }))
    await waitFor(() => expect(result.current.sessionId).toBe('session-1'))

    await act(async () => {
      await result.current.sendMessage('oi')
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[0]).toMatchObject({ role: 'user', content: 'oi' })
    expect(result.current.messages[1]).toMatchObject({ role: 'assistant', content: 'Olá mundo' })
    expect(result.current.isStreaming).toBe(false)
  })

  it('ignores empty messages', async () => {
    vi.spyOn(apiClient, 'createChatSession').mockResolvedValue('session-1')
    const streamSpy = vi.spyOn(apiClient, 'streamChatMessage')

    const { result } = renderHook(() => useChat({ ragEnabled: false }))
    await waitFor(() => expect(result.current.sessionId).toBe('session-1'))

    await act(async () => {
      await result.current.sendMessage('   ')
    })

    expect(streamSpy).not.toHaveBeenCalled()
    expect(result.current.messages).toHaveLength(0)
  })
})
