import { useRef, useState } from 'react'
import { CircleAlert, LoaderCircle, CloudUpload, X } from 'lucide-react'

const ALLOWED = /\.(pdf|txt|md)$/i
const MAX_SIZE = 20 * 1024 * 1024 // 20 MB

export default function DocumentUploader({ uploads, onFiles, onDismiss }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [notice, setNotice] = useState(null)

  const handleFiles = (fileList) => {
    const files = Array.from(fileList) // đổi sang mảng ngay, trước khi reset input
    const valid = files.filter((f) => ALLOWED.test(f.name) && f.size <= MAX_SIZE)
    const skipped = files.length - valid.length
    setNotice(skipped ? `${skipped} file skipped. Only PDF, TXT or MD up to 20 MB are accepted.` : null)
    if (valid.length) onFiles(valid)
  }

  return (
    <div className="space-y-2">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          handleFiles(e.dataTransfer.files)
        }}
        className={`flex cursor-pointer flex-col items-center gap-1 rounded-xl border-2 border-dashed px-3 py-5 text-center transition-colors ${
          dragging
            ? 'border-brand-500 bg-brand-50'
            : 'border-slate-300 hover:border-brand-500 hover:bg-slate-50'
        }`}
      >
        <CloudUpload className="h-6 w-6 text-slate-400" />
        <p className="text-sm font-medium text-slate-700">Drop files or click to upload</p>
        <p className="text-xs text-slate-500">PDF, TXT, MD · max 20 MB</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
          className="hidden"
          onChange={(e) => {
            handleFiles(e.target.files)
            e.target.value = '' // cho phép chọn lại cùng 1 file
          }}
        />
      </div>

      {notice && <p className="text-xs text-amber-600">{notice}</p>}

      {uploads.map((u) => (
        <div key={u.tempId} className="rounded-lg border border-slate-200 bg-white p-2 text-xs">
          <div className="flex items-center gap-2">
            {u.error ? (
              <CircleAlert className="h-4 w-4 shrink-0 text-red-500" />
            ) : (
              <LoaderCircle className="h-4 w-4 shrink-0 animate-spin text-brand-600" />
            )}
            <span className="min-w-0 flex-1 truncate font-medium text-slate-700">{u.name}</span>
            {u.error && (
              <button type="button" onClick={() => onDismiss(u.tempId)} aria-label="Dismiss">
                <X className="h-4 w-4 text-slate-400 hover:text-slate-700" />
              </button>
            )}
          </div>
          {u.error ? (
            <p className="mt-1 text-red-600">{u.error}</p>
          ) : (
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full rounded-full bg-brand-500 transition-all"
                style={{ width: `${u.progress}%` }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
