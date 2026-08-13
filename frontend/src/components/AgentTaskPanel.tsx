import type { AgentTaskResult } from '../types'
import { AgentIcon, AlertCircleIcon, CheckCircleIcon } from './icons'

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

const STATUS_STYLES: Record<string, string> = {
  done: 'bg-emerald-500/15 text-emerald-300',
  needs_clarification: 'bg-amber-500/15 text-amber-300',
  refused: 'bg-red-500/15 text-red-300',
  max_iterations_reached: 'bg-amber-500/15 text-amber-300',
}

export function AgentTaskPanel({ result, isRunning, error }: AgentTaskPanelProps) {
  return (
    <div className="flex flex-col gap-4">
      {isRunning && (
        <div
          data-testid="agent-running"
          className="flex items-center gap-2.5 rounded-2xl border border-white/10 bg-white/[0.02] px-4 py-3 text-sm text-slate-400"
        >
          <span className="flex h-7 w-7 shrink-0 animate-pulse items-center justify-center rounded-full bg-indigo-500/20 text-indigo-300">
            <AgentIcon className="h-4 w-4" />
          </span>
          Executando tarefa…
        </div>
      )}

      {error && (
        <p
          data-testid="agent-error"
          className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-300"
        >
          <AlertCircleIcon className="h-4 w-4 shrink-0" />
          {error}
        </p>
      )}

      {result && (
        <div
          data-testid="agent-result"
          className="animate-fade-in-up flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-5"
        >
          <div className="flex items-center justify-between">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
                STATUS_STYLES[result.status] ?? 'bg-white/10 text-slate-300'
              }`}
            >
              <CheckCircleIcon className="h-3.5 w-3.5" />
              {STATUS_LABELS[result.status] ?? result.status}
            </span>
            <span className="text-xs text-slate-500">{result.iterations} iteração(ões)</span>
          </div>

          {result.tool_calls.length > 0 && (
            <ul data-testid="agent-tool-log" className="flex flex-col gap-1 border-l border-white/10 pl-3 text-xs text-slate-500">
              {result.tool_calls.map((call, index) => (
                <li key={`${call.tool}-${index}`} className="font-mono">
                  → {call.tool}
                </li>
              ))}
            </ul>
          )}

          <p className="text-[15px] leading-relaxed whitespace-pre-wrap text-slate-100">{result.result}</p>
        </div>
      )}
    </div>
  )
}
