import { CircleAlert, CircleCheck, FileText, LoaderCircle, Trash2 } from 'lucide-react'
import { formatBytes } from '../lib/utils'

function StatusBadge({ status }) {
  if (status === 'processing') {
    return (
      <span className="flex items-center gap-1 text-amber-600">
        <LoaderCircle className="h-3 w-3 animate-spin" /> Processing
      </span>
    )
  }
  if (status === 'error') {
    return (
      <span className="flex items-center gap-1 text-red-600">
        <CircleAlert className="h-3 w-3" /> Failed
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1 text-emerald-600">
      <CircleCheck className="h-3 w-3" /> Ready
    </span>
  )
}

export default function DocumentList({ documents, loading, error, isIncluded, onToggle, onRemove }) {
  if (loading) return <p className="text-sm text-slate-500">Loading documents…</p>

  return (
    <div className="space-y-2">
      {error && <p className="rounded-lg bg-red-50 p-2 text-xs text-red-600">{error}</p>}

      {documents.length === 0 && !error && (
        <p className="py-4 text-center text-sm text-slate-500">
          No documents yet. Upload papers to ground the answers.
        </p>
      )}

      {documents.map((doc) => (
        <div
          key={doc.id}
          className="flex items-start gap-2 rounded-lg border border-slate-200 bg-white p-2.5"
        >
          <input
            type="checkbox"
            checked={isIncluded(doc.id)}
            disabled={doc.status !== 'ready'}
            onChange={() => onToggle(doc.id)}
            className="mt-1 h-4 w-4 accent-indigo-600"
            aria-label={`Use ${doc.name} as context`}
          />
          <FileText className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-800" title={doc.name}>
              {doc.name}
            </p>
            <div className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-slate-500">
              <span>{formatBytes(doc.size)}</span>
              {doc.status === 'ready' && <span>{doc.chunks} chunks</span>}
              <StatusBadge status={doc.status} />
            </div>
          </div>
          <button
            type="button"
            onClick={() => window.confirm(`Delete "${doc.name}"?`) && onRemove(doc.id)}
            className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
            aria-label={`Delete ${doc.name}`}
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  )
}
