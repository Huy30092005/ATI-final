import { useCallback, useEffect, useState } from 'react'
import * as api from '../api/research'
import { uid } from '../lib/utils'

/**
 * Quản lý danh sách tài liệu tham khảo:
 * tải danh sách, upload (có tiến trình), xoá, chọn tài liệu nào được dùng làm ngữ cảnh.
 */
export function useDocuments() {
  const [documents, setDocuments] = useState([])
  const [uploads, setUploads] = useState([]) // file đang upload: { tempId, name, progress, error }
  const [excludedIds, setExcludedIds] = useState([]) // tài liệu bị bỏ tick
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api.listDocuments())
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Tải danh sách lần đầu
  useEffect(() => {
    refresh()
  }, [refresh])

  // Nếu còn tài liệu đang xử lý (chunking/embedding) -> hỏi lại server mỗi 3 giây
  const hasProcessing = documents.some((d) => d.status === 'processing')
  useEffect(() => {
    if (!hasProcessing) return undefined
    const timer = setInterval(refresh, 3000)
    return () => clearInterval(timer)
  }, [hasProcessing, refresh])

  const upload = useCallback(async (files) => {
    for (const file of files) {
      const tempId = uid()
      setUploads((list) => [...list, { tempId, name: file.name, progress: 0, error: null }])
      try {
        const doc = await api.uploadDocument(file, (progress) =>
          setUploads((list) => list.map((u) => (u.tempId === tempId ? { ...u, progress } : u))),
        )
        setDocuments((list) => [doc, ...list])
        setUploads((list) => list.filter((u) => u.tempId !== tempId))
      } catch (e) {
        setUploads((list) => list.map((u) => (u.tempId === tempId ? { ...u, error: e.message } : u)))
      }
    }
  }, [])

  const dismissUpload = useCallback((tempId) => {
    setUploads((list) => list.filter((u) => u.tempId !== tempId))
  }, [])

  const remove = useCallback(async (id) => {
    try {
      await api.deleteDocument(id)
      setDocuments((list) => list.filter((d) => d.id !== id))
      setExcludedIds((ids) => ids.filter((x) => x !== id))
    } catch (e) {
      setError(e.message)
    }
  }, [])

  const toggleIncluded = useCallback((id) => {
    setExcludedIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]))
  }, [])

  const isIncluded = useCallback((id) => !excludedIds.includes(id), [excludedIds])

  return {
    documents,
    uploads,
    loading,
    error,
    upload,
    dismissUpload,
    remove,
    toggleIncluded,
    isIncluded,
  }
}
