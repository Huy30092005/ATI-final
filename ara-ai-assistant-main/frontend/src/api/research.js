// ============================================================
//  HỢP ĐỒNG API GIỮA FRONTEND <-> BACKEND (đưa cho bạn làm backend)
//
//  GET    /api/documents          -> [Document]
//  POST   /api/documents          (multipart, field "file") -> Document
//  DELETE /api/documents/{id}     -> 204
//  POST   /api/chat               -> { message_id, answer, evidence: [Evidence] }
//  POST   /api/export             -> file nhị phân (PDF hoặc DOCX)
//
//  Document = { id, name, size, status: 'processing'|'ready'|'error', chunks }
//  Evidence = { id, source_type: 'document'|'web'|'academic', title, url,
//               authors, year, snippet, relevance (0-1), credibility (0-1) }
//  Trong "answer" (Markdown) dùng [1], [2]... để trích dẫn evidence[0], evidence[1]...
// ============================================================
import { http, USE_MOCK } from './client'
import * as mock from './mock'
import { slugify } from '../lib/utils'

export async function listDocuments() {
  if (USE_MOCK) return mock.listDocuments()
  const { data } = await http.get('/api/documents')
  return data
}

export async function uploadDocument(file, onProgress) {
  if (USE_MOCK) return mock.uploadDocument(file, onProgress)
  const form = new FormData()
  form.append('file', file)
  const { data } = await http.post('/api/documents', form, {
    onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / (e.total || file.size || 1))),
  })
  return data
}

export async function deleteDocument(id) {
  if (USE_MOCK) return mock.deleteDocument(id)
  await http.delete(`/api/documents/${id}`)
}

export async function sendMessage({ sessionId, message, documentIds, sources }) {
  if (USE_MOCK) return mock.sendMessage({ message, documentIds, sources })
  const { data } = await http.post('/api/chat', {
    session_id: sessionId,
    message,
    document_ids: documentIds,
    sources, // { documents: bool, web: bool, academic: bool }
  })
  return data
}

export async function exportAnswer({ format, title, content, evidence }) {
  if (USE_MOCK) return mock.exportAnswer({ format, title, content, evidence })
  const response = await http.post(
    '/api/export',
    { format, title, content, evidence },
    { responseType: 'blob' },
  )
  return { blob: response.data, filename: `${slugify(title)}.${format}` }
}
