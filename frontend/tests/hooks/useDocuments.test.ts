import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useDocuments } from '../../src/hooks/useDocuments'
import * as apiClient from '../../src/api/client'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('useDocuments', () => {
  it('loads documents on mount', async () => {
    vi.spyOn(apiClient, 'listDocuments').mockResolvedValue([
      { id: '1', filename: 'a.pdf', chunks_count: 2, status: 'indexed' },
    ])

    const { result } = renderHook(() => useDocuments())

    await waitFor(() => expect(result.current.documents).toHaveLength(1))
  })

  it('rejects unsupported file extensions without calling the API', async () => {
    vi.spyOn(apiClient, 'listDocuments').mockResolvedValue([])
    const uploadSpy = vi.spyOn(apiClient, 'uploadDocument')

    const { result } = renderHook(() => useDocuments())
    await waitFor(() => expect(result.current.documents).toEqual([]))

    const badFile = new File(['x'], 'virus.exe', { type: 'application/octet-stream' })

    await act(async () => {
      await result.current.upload(badFile)
    })

    expect(uploadSpy).not.toHaveBeenCalled()
    expect(result.current.error).toMatch(/não suportado/i)
  })

  it('uploads a supported file and refreshes the list', async () => {
    vi.spyOn(apiClient, 'listDocuments')
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([{ id: '1', filename: 'a.pdf', chunks_count: 1, status: 'indexed' }])
    vi.spyOn(apiClient, 'uploadDocument').mockResolvedValue({
      id: '1',
      filename: 'a.pdf',
      chunks_count: 1,
      status: 'indexed',
    })

    const { result } = renderHook(() => useDocuments())
    await waitFor(() => expect(result.current.documents).toEqual([]))

    const goodFile = new File(['x'], 'a.pdf', { type: 'application/pdf' })
    await act(async () => {
      await result.current.upload(goodFile)
    })

    expect(result.current.documents).toHaveLength(1)
    expect(result.current.error).toBeNull()
  })

  it('sets an error when the upload request fails', async () => {
    vi.spyOn(apiClient, 'listDocuments').mockResolvedValue([])
    vi.spyOn(apiClient, 'uploadDocument').mockRejectedValue(new Error('boom'))

    const { result } = renderHook(() => useDocuments())
    await waitFor(() => expect(result.current.documents).toEqual([]))

    const file = new File(['x'], 'a.pdf', { type: 'application/pdf' })
    await act(async () => {
      await result.current.upload(file)
    })

    expect(result.current.error).toMatch(/falha/i)
  })

  it('removes a document and refreshes the list', async () => {
    vi.spyOn(apiClient, 'listDocuments')
      .mockResolvedValueOnce([{ id: '1', filename: 'a.pdf', chunks_count: 1, status: 'indexed' }])
      .mockResolvedValueOnce([])
    const deleteSpy = vi.spyOn(apiClient, 'deleteDocument').mockResolvedValue(undefined)

    const { result } = renderHook(() => useDocuments())
    await waitFor(() => expect(result.current.documents).toHaveLength(1))

    await act(async () => {
      await result.current.remove('1')
    })

    expect(deleteSpy).toHaveBeenCalledWith('1')
    expect(result.current.documents).toHaveLength(0)
  })
})
