import { useEffect, useRef } from 'react'
import { BookOpen, Sparkles } from 'lucide-react'
import MessageBubble from './MessageBubble'

const SUGGESTIONS = [
  'Summarize the key findings of my uploaded papers',
  'What are the latest approaches to retrieval-augmented generation?',
  'Compare transformer and RNN architectures for text classification',
]

function EmptyState({ onSuggest }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-white">
        <BookOpen className="h-7 w-7" />
      </div>
      <h2 className="text-xl font-semibold text-slate-900">What would you like to research?</h2>
      <p className="mt-1 max-w-md text-sm text-slate-500">
        ARA searches your documents, the web and academic databases, ranks the evidence, then writes a
        cited answer.
      </p>
      <div className="mt-6 flex w-full max-w-md flex-col gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSuggest(s)}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-left text-sm text-slate-700 transition-colors hover:border-brand-500 hover:bg-brand-50"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
        <Sparkles className="h-4 w-4" />
      </div>
      <div className="flex items-center gap-1.5 rounded-2xl border border-slate-200 bg-white px-4 py-3">
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
        <span className="ml-2 text-xs text-slate-500">Searching and ranking evidence…</span>
      </div>
    </div>
  )
}

export default function ChatWindow({ messages, isLoading, activeId, onSuggest, onCite, onShowEvidence }) {
  const bottomRef = useRef(null)

  // Tự cuộn xuống cuối khi có tin nhắn mới
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (messages.length === 0 && !isLoading) return <EmptyState onSuggest={onSuggest} />

  return (
    <div className="h-full overflow-y-auto px-4 py-6">
      <div className="mx-auto max-w-3xl space-y-6">
        {messages.map((m) => (
          <MessageBubble
            key={m.id}
            message={m}
            isActive={m.id === activeId}
            onCite={onCite}
            onShowEvidence={onShowEvidence}
          />
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
