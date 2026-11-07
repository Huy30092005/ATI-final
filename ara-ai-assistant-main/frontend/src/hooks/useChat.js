import { useCallback, useState } from 'react'
import * as api from '../api/research'
import { uid } from '../lib/utils'

/**
 * Quản lý hội thoại.
 * message = { id, role: 'user' | 'assistant', content, evidence?, isError? }
 */
export function useChat() {
  const [sessionId, setSessionId] = useState(uid)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  const send = useCallback(
    async (text, { documentIds, sources }) => {
      setMessages((list) => [...list, { id: uid(), role: 'user', content: text }])
      setIsLoading(true)
      try {
        const res = await api.sendMessage({ sessionId, message: text, documentIds, sources })
        setMessages((list) => [
          ...list,
          { id: res.message_id ?? uid(), role: 'assistant', content: res.answer, evidence: res.evidence ?? [] },
        ])
      } catch (e) {
        setMessages((list) => [
          ...list,
          { id: uid(), role: 'assistant', content: e.message, evidence: [], isError: true },
        ])
      } finally {
        setIsLoading(false)
      }
    },
    [sessionId],
  )

  const reset = useCallback(() => {
    setMessages([])
    setSessionId(uid()) // session mới -> backend (memory) bắt đầu lịch sử mới
  }, [])

  return { messages, isLoading, send, reset }
}
