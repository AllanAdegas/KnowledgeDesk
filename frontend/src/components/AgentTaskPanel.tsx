import type { AgentTaskResult } from '../types'

interface AgentTaskPanelProps {
  result: AgentTaskResult | null
  isRunning: boolean
  error: string | null
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Em andamento',
  needs_clarification: 'Precisa de esclarecimento',
  refused: 'Recusado',
  done: 'Concluído',
  max_iterations_reached: 'Limite de iterações atingido',
}

export function AgentTaskPanel({ result, isRunning, error }: AgentTaskPanelProps) {
  return (
    <div className="flex flex-col gap-4">
      {isRunning && (
        <div data-testid="agent-running" className="text-sm text-gray-500">
          Executando tarefa…
        </div>
      )}

      {error && (
        <p data-testid="agent-error" className="text-sm text-red-600">
          {error}
        </p>
      )}

      {result && (
        <div data-testid="agent-result" className="flex flex-col gap-2 rounded border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">
              {STATUS_LABELS[result.status] ?? result.status}
            </span>
            <span className="text-xs text-gray-400">{result.iterations} iteração(ões)</span>
          </div>

          {result.tool_calls.length > 0 && (
            <ul data-testid="agent-tool-log" className="text-xs text-gray-400">
              {result.tool_calls.map((call, index) => (
                <li key={`${call.tool}-${index}`}>→ {call.tool}</li>
              ))}
            </ul>
          )}

          <p className="whitespace-pre-wrap">{result.result}</p>
        </div>
      )}
    </div>
  )
}
