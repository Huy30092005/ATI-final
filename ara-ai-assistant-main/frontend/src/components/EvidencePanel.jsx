import { useEffect } from 'react'
import { Library, X } from 'lucide-react'
import SourceCard from './SourceCard'
import { SOURCE_TYPES } from '../lib/sourceTypes'

export default function EvidencePanel({ open, onClose, message, highlight }) {
  const evidence = message?.evidence ?? []

  // Khi bấm [n] trong câu trả lời -> cuộn tới thẻ nguồn tương ứng
  useEffect(() => {
    if (!highlight) return
    document.getElementById(`source-${highlight.n}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [highlight])

  const counts = evidence.reduce((acc, e) => {
    acc[e.source_type] = (acc[e.source_type] ?? 0) + 1
    return acc
  }, {})

  return (
    <>
      {open && <div className="fixed inset-0 z-20 bg-slate-900/40 xl:hidden" onClick={onClose} />}

      <aside
        className={`fixed inset-y-0 right-0 z-30 flex w-full max-w-sm flex-col border-l border-slate-200 bg-slate-50 transition-transform xl:static xl:w-96 xl:max-w-none xl:translate-x-0 ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
          <Library className="h-5 w-5 text-brand-600" />
          <h2 className="flex-1 text-sm font-semibold text-slate-900">Evidence</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-500 hover:bg-slate-200 xl:hidden"
            aria-label="Close evidence panel"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {evidence.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
            <Library className="mb-2 h-8 w-8 text-slate-300" />
            <p className="text-sm text-slate-500">
              Ranked sources behind each answer will appear here. Click a [1] marker in an answer to jump
              to its source.
            </p>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap gap-1.5 border-b border-slate-200 px-4 py-2">
              {Object.entries(counts).map(([type, n]) => (
                <span
                  key={type}
                  className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${SOURCE_TYPES[type]?.badge ?? 'bg-slate-100 text-slate-600'}`}
                >
                  {n} {SOURCE_TYPES[type]?.label ?? type}
                </span>
              ))}
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {evidence.map((source, i) => (
                <SourceCard
                  key={source.id ?? i}
                  index={i + 1}
                  source={source}
                  highlighted={highlight?.n === i + 1 && highlight?.messageId === message.id}
                />
              ))}
            </div>
          </>
        )}
      </aside>
    </>
  )
}
