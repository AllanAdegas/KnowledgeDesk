import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AgentPage } from '../../src/pages/AgentPage'
import * as apiClient from '../../src/api/client'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('AgentPage', () => {
  it('submits a task and renders the result', async () => {
    vi.spyOn(apiClient, 'submitAgentTask').mockResolvedValue('job-1')
    vi.spyOn(apiClient, 'getAgentTask').mockResolvedValue({
      job_id: 'job-1',
      status: 'done',
      result: 'Documentos disponíveis: a.pdf',
      iterations: 1,
      tool_calls: [{ tool: 'list' }],
    })

    const user = userEvent.setup()
    render(<AgentPage />)

    await user.type(screen.getByTestId('task-input'), 'liste todos os documentos')
    await user.click(screen.getByTestId('run-task'))

    await waitFor(() => expect(screen.getByTestId('agent-result')).toBeInTheDocument())
    expect(screen.getByTestId('agent-result')).toHaveTextContent('Documentos disponíveis: a.pdf')
  })

  it('keeps the run button disabled when the task input is empty', () => {
    render(<AgentPage />)

    expect(screen.getByTestId('run-task')).toBeDisabled()
  })
})
