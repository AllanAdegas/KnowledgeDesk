import { useCallback, useEffect, useRef, useState } from 'react'
import { getAgentTask, submitAgentTask } from '../api/client'
import type { AgentTaskResult } from '../types'

interface UseAgentResult {
  result: AgentTaskResult | null
  isRunning: boolean
  error: string | null
  runTask: (task: string) => Promise<void>
}

const POLL_INTERVAL_MS = 500
const MAX_POLL_ATTEMPTS = 60

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Submits a task to the agent endpoint and polls until it settles. */
export function useAgent(): UseAgentResult {
  const [result, setResult] = useState<AgentTaskResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isMountedRef = useRef(true)

  useEffect(() => {
    // Reset on every (re)mount, not just at ref-init: React 18 StrictMode's
    // dev-mode mount -> cleanup -> remount cycle would otherwise leave this
    // stuck at false after the simulated unmount, silently dropping every
    // subsequent setResult/setIsRunning call in runTask.
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
    }
  }, [])

  const runTask = useCallback(async (task: string) => {
    const trimmed = task.trim()
    if (!trimmed) return

    setIsRunning(true)
    setError(null)
    setResult(null)

    try {
      const jobId = await submitAgentTask(trimmed)

      for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
        const taskResult = await getAgentTask(jobId)
        if (!isMountedRef.current) return

        if (taskResult.status !== 'pending') {
          setResult(taskResult)
          return
        }

        await sleep(POLL_INTERVAL_MS)
      }

      setError('A tarefa não foi concluída a tempo.')
    } catch {
      setError('Falha ao executar a tarefa do agente.')
    } finally {
      if (isMountedRef.current) setIsRunning(false)
    }
  }, [])

  return { result, isRunning, error, runTask }
}
