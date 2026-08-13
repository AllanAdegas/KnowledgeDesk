import { useState, type FormEvent } from 'react'
import { AgentTaskPanel } from '../components/AgentTaskPanel'
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
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-4 text-xl font-semibold">Agente</h1>

      <form onSubmit={handleSubmit} className="mb-6 flex flex-col gap-3">
        <textarea
          data-testid="task-input"
          value={taskValue}
          onChange={(event) => setTaskValue(event.target.value)}
          placeholder="Descreva a tarefa, ex: 'liste todos os documentos sobre RH'"
          rows={3}
          className="rounded border border-gray-300 px-3 py-2"
        />
        <button
          data-testid="run-task"
          type="submit"
          disabled={isRunning || !taskValue.trim()}
          className="self-start rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
        >
          Executar
        </button>
      </form>

      <AgentTaskPanel result={result} isRunning={isRunning} error={error} />
    </div>
  )
}
