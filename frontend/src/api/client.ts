import axios from 'axios'
import type { AgentTaskResult, IndexedDocument } from '../types'

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

export interface CreateSessionResponse {
  session_id: string
}

export async function createChatSession(): Promise<string> {
  const response = await apiClient.post<CreateSessionResponse>('/api/chat/session')
  return response.data.session_id
}

export interface HistoryEntry {
  role: 'user' | 'assistant'
  content: string
}

export async function getChatHistory(sessionId: string): Promise<HistoryEntry[]> {
  const response = await apiClient.get<HistoryEntry[]>(`/api/chat/history/${sessionId}`)
  return response.data
}

/**
 * Send a chat message and stream the SSE response, invoking `onToken` for
 * each token frame and `onDone` when the terminal event arrives.
 *
 * Uses `fetch` + a `ReadableStream` reader instead of `EventSource` because
 * the chat endpoint is a POST request (EventSource only supports GET).
 */
export async function streamChatMessage(
  sessionId: string,
  message: string,
  ragEnabled: boolean,
  onToken: (content: string) => void,
  onDone: () => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chat/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message, rag_enabled: ragEnabled }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed with status ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''

    for (const frame of frames) {
      const dataLine = frame.split('\n').find((line) => line.startsWith('data: '))
      if (!dataLine) continue

      const payload = JSON.parse(dataLine.slice('data: '.length)) as {
        type: 'token' | 'done'
        content?: string
        session_id?: string
      }

      if (payload.type === 'token' && payload.content) {
        onToken(payload.content)
      } else if (payload.type === 'done') {
        onDone()
      }
    }
  }
}

export async function uploadDocument(file: File): Promise<IndexedDocument> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post<IndexedDocument>('/api/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function listDocuments(): Promise<IndexedDocument[]> {
  const response = await apiClient.get<IndexedDocument[]>('/api/documents')
  return response.data
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/api/documents/${id}`)
}

export interface SubmitAgentTaskResponse {
  job_id: string
}

export async function submitAgentTask(task: string): Promise<string> {
  const response = await apiClient.post<SubmitAgentTaskResponse>('/api/agent/task', { task })
  return response.data.job_id
}

export async function getAgentTask(jobId: string): Promise<AgentTaskResult> {
  const response = await apiClient.get<AgentTaskResult>(`/api/agent/task/${jobId}`)
  return response.data
}
