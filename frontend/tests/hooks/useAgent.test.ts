import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useAgent } from '../../src/hooks/useAgent'
import * as apiClient from '../../src/api/client'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('useAgent', () => {
  it('submits a task and stores the result once it settles', async () => {
    vi.spyOn(apiClient, 'submitAgentTask').mockResolvedValue('job-1')
    vi.spyOn(apiClient, 'getAgentTask').mockResolvedValue({
      job_id: 'job-1',
      status: 'done',
      result: 'lista de documentos',
      iterations: 1,
      tool_calls: [{ tool: 'list' }],
    })

    const { result } = renderHook(() => useAgent())

    await act(async () => {
      await result.current.runTask('liste os documentos')
    })

    expect(result.current.result?.status).toBe('done')
    expect(result.current.isRunning).toBe(false)
  })

  it('polls again while status is pending', async () => {
    vi.spyOn(apiClient, 'submitAgentTask').mockResolvedValue('job-1')
    const getTaskSpy = vi
      .spyOn(apiClient, 'getAgentTask')
      .mockResolvedValueOnce({
        job_id: 'job-1',
        status: 'pending',
        result: null,
        iterations: 0,
        tool_calls: [],
      })
      .mockResolvedValueOnce({
        job_id: 'job-1',
        status: 'done',
        result: 'ok',
        iterations: 1,
        tool_calls: [],
      })

    const { result } = renderHook(() => useAgent())

    await act(async () => {
      await result.current.runTask('liste os documentos')
    })

    expect(getTaskSpy).toHaveBeenCalledTimes(2)
    expect(result.current.result?.status).toBe('done')
  })

  it('sets an error when submission fails', async () => {
    vi.spyOn(apiClient, 'submitAgentTask').mockRejectedValue(new Error('boom'))

    const { result } = renderHook(() => useAgent())

    await act(async () => {
      await result.current.runTask('tarefa qualquer')
    })

    await waitFor(() => expect(result.current.error).not.toBeNull())
  })

  it('ignores blank tasks', async () => {
    const submitSpy = vi.spyOn(apiClient, 'submitAgentTask')

    const { result } = renderHook(() => useAgent())

    await act(async () => {
      await result.current.runTask('   ')
    })

    expect(submitSpy).not.toHaveBeenCalled()
  })
})
