import { useState } from 'react'
import { ChevronDown, Download, FileText, LoaderCircle } from 'lucide-react'

const FORMATS = [
  { key: 'pdf', label: 'PDF document' },
  { key: 'docx', label: 'Word document' },
]

export default function ExportMenu({ disabled, onExport }) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)

  const run = async (format) => {
    setBusy(format)
    setError(null)
    try {
      await onExport(format)
      setOpen(false)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Download className="h-4 w-4" />
        <span className="hidden sm:inline">Export</span>
        <ChevronDown className="h-4 w-4" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-1 w-56 rounded-xl border border-slate-200 bg-white p-1 shadow-lg">
            {FORMATS.map(({ key, label }) => (
              <button
                key={key}
                type="button"
                disabled={busy !== null}
                onClick={() => run(key)}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 disabled:opacity-60"
              >
                {busy === key ? (
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4 text-slate-400" />
                )}
                {label}
              </button>
            ))}
            {error && <p className="px-3 py-2 text-xs text-red-600">{error}</p>}
          </div>
        </>
      )}
    </div>
  )
}
