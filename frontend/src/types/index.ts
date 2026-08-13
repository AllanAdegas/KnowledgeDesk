export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  isStreaming?: boolean
}

export interface IndexedDocument {
  id: string
  filename: string
  chunks_count: number
  status?: 'indexed' | 'error'
}

export type AgentTaskStatus =
  | 'pending'
  | 'needs_clarification'
  | 'refused'
  | 'done'
  | 'max_iterations_reached'

export interface AgentToolCall {
  tool: string
}

export interface AgentTaskResult {
  job_id: string
  status: AgentTaskStatus
  result: string | null
  iterations: number
  tool_calls: AgentToolCall[]
}
