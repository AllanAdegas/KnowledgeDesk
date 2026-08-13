import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  apiClient,
  createChatSession,
  deleteDocument,
  getAgentTask,
  getChatHistory,
  listDocuments,
  streamChatMessage,
  submitAgentTask,
  uploadDocument,
} from '../../src/api/client'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('createChatSession', () => {
  it('returns the session id from the response', async () => {
    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: { session_id: 'abc-123' } })

    const sessionId = await createChatSession()

    expect(sessionId).toBe('abc-123')
  })
})

describe('getChatHistory', () => {
  it('returns the history array', async () => {
    const history = [{ role: 'user', content: 'oi' }]
    vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: history })

    const result = await getChatHistory('session-1')

    expect(result).toEqual(history)
  })
})

describe('uploadDocument', () => {
  it('posts the file as form data and returns the indexed document', async () => {
    const document = { id: '1', filename: 'a.pdf', chunks_count: 3, status: 'indexed' as const }
    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: document })

    const file = new File(['conteúdo'], 'a.pdf', { type: 'application/pdf' })
    const result = await uploadDocument(file)

    expect(result).toEqual(document)
  })
})

describe('listDocuments', () => {
  it('returns the documents array', async () => {
    vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: [] })

    const result = await listDocuments()

    expect(result).toEqual([])
  })
})

describe('deleteDocument', () => {
  it('calls delete on the correct endpoint', async () => {
    const deleteSpy = vi.spyOn(apiClient, 'delete').mockResolvedValueOnce({ data: {} })

    await deleteDocument('doc-1')

    expect(deleteSpy).toHaveBeenCalledWith('/api/documents/doc-1')
  })
})

describe('submitAgentTask', () => {
  it('returns the job id', async () => {
    vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: { job_id: 'job-1' } })

    const jobId = await submitAgentTask('liste os documentos')

    expect(jobId).toBe('job-1')
  })
})

describe('getAgentTask', () => {
  it('returns the task result', async () => {
    const taskResult = {
      job_id: 'job-1',
      status: 'done' as const,
      result: 'ok',
      iterations: 1,
      tool_calls: [],
    }
    vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: taskResult })

    const result = await getAgentTask('job-1')

    expect(result).toEqual(taskResult)
  })
})

describe('streamChatMessage', () => {
  function makeStreamResponse(frames: string[]): Response {
    const encoder = new TextEncoder()
    let index = 0
    const stream = new ReadableStream<Uint8Array>({
      pull(controller) {
        if (index < frames.length) {
          controller.enqueue(encoder.encode(frames[index]))
          index += 1
        } else {
          controller.close()
        }
      },
    })
    return new Response(stream, { status: 200 })
  }

  it('invokes onToken for each token frame and onDone for the terminal frame', async () => {
    const frames = [
      'data: {"type": "token", "content": "Olá"}\n\n',
      'data: {"type": "token", "content": " mundo"}\n\n',
      'data: {"type": "done", "session_id": "s1"}\n\n',
    ]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(makeStreamResponse(frames)))

    const onToken = vi.fn()
    const onDone = vi.fn()

    await streamChatMessage('s1', 'oi', false, onToken, onDone)

    expect(onToken).toHaveBeenNthCalledWith(1, 'Olá')
    expect(onToken).toHaveBeenNthCalledWith(2, ' mundo')
    expect(onDone).toHaveBeenCalledTimes(1)

    vi.unstubAllGlobals()
  })

  it('throws when the response is not ok', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 500, body: null } as Response),
    )

    await expect(streamChatMessage('s1', 'oi', false, vi.fn(), vi.fn())).rejects.toThrow()

    vi.unstubAllGlobals()
  })
})
