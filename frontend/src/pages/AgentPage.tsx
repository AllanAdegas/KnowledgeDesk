import { useState, type FormEvent } from 'react'
import { AgentTaskPanel } from '../components/AgentTaskPanel'
import { AgentIcon, SendIcon } from '../components/icons'
import { useAgent } from '../hooks/useAgent'

export function AgentPage() {
  const { result, isRunning, error, runTask } = useAgent()
  const [taskValue, setTaskValue] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault()
    if (!taskValue.trim() || isRunning) return
    void runTask(taskValue)
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-2xl px-6 py-10">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 text-indigo-300">
            <AgentIcon className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-100">Agente</h1>
            <p className="text-sm text-slate-500">Descreva uma tarefa e acompanhe a execução.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mb-6 flex flex-col gap-3">
          <textarea
            data-testid="task-input"
            value={taskValue}
            onChange={(event) => setTaskValue(event.target.value)}
            placeholder="Descreva a tarefa, ex: 'liste todos os documentos sobre RH'"
            rows={3}
            className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-[15px] text-slate-100 placeholder:text-slate-600 focus:border-indigo-400/50 focus:outline-none"
          />
          <button
            data-testid="run-task"
            type="submit"
            disabled={isRunning || !taskValue.trim()}
            className="inline-flex w-fit items-center gap-2 self-start rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 px-4 py-2 text-sm font-medium text-white transition-opacity disabled:opacity-30"
          >
            <SendIcon className="h-3.5 w-3.5" />
            Executar
          </button>
        </form>

        <AgentTaskPanel result={result} isRunning={isRunning} error={error} />
      </div>
    </div>
  )
}
