import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import App from '../src/App'
import * as apiClient from '../src/api/client'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('App', () => {
  it('renders the navigation and defaults to the chat page', () => {
    vi.spyOn(apiClient, 'createChatSession').mockResolvedValue('session-1')
    vi.spyOn(apiClient, 'listDocuments').mockResolvedValue([])

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    )

    expect(screen.getByText('KnowledgeDesk')).toBeInTheDocument()
    expect(screen.getByTestId('chat-input')).toBeInTheDocument()
  })
})
