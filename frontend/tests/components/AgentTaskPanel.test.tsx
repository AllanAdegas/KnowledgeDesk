import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AgentTaskPanel } from '../../src/components/AgentTaskPanel'

describe('AgentTaskPanel', () => {
  it('renders nothing but stays idle when there is no result yet', () => {
    render(<AgentTaskPanel result={null} isRunning={false} error={null} />)

    expect(screen.queryByTestId('agent-result')).not.toBeInTheDocument()
  })

  it('shows the running indicator', () => {
    render(<AgentTaskPanel result={null} isRunning={true} error={null} />)

    expect(screen.getByTestId('agent-running')).toBeInTheDocument()
  })

  it('shows the error message', () => {
    render(<AgentTaskPanel result={null} isRunning={false} error="Falha ao executar" />)

    expect(screen.getByTestId('agent-error')).toHaveTextContent('Falha ao executar')
  })

  it('renders the result with status label, tool log, and content', () => {
    render(
      <AgentTaskPanel
        result={{
          job_id: 'job-1',
          status: 'done',
          result: 'Documentos: a.pdf, b.pdf',
          iterations: 2,
          tool_calls: [{ tool: 'list' }],
        }}
        isRunning={false}
        error={null}
      />,
    )

    expect(screen.getByTestId('agent-result')).toHaveTextContent('Documentos: a.pdf, b.pdf')
    expect(screen.getByTestId('agent-tool-log')).toHaveTextContent('list')
    expect(screen.getByText('Concluído')).toBeInTheDocument()
  })

  it('falls back to the raw status string for unknown statuses', () => {
    render(
      <AgentTaskPanel
        result={{
          job_id: 'job-1',
          status: 'unknown_status' as never,
          result: 'texto',
          iterations: 1,
          tool_calls: [],
        }}
        isRunning={false}
        error={null}
      />,
    )

    expect(screen.getByText('unknown_status')).toBeInTheDocument()
  })
})
