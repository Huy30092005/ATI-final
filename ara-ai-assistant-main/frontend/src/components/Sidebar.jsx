import { BookOpen, Plus, X } from 'lucide-react'
import DocumentUploader from './DocumentUploader'
import DocumentList from './DocumentList'

export default function Sidebar({ open, onClose, onNewChat, docs }) {
  return (
    <>
      {/* Lớp nền mờ khi mở sidebar trên mobile */}
      {open && <div className="fixed inset-0 z-20 bg-slate-900/40 lg:hidden" onClick={onClose} />}

      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-72 flex-col border-r border-slate-200 bg-slate-50 transition-transform lg:static lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <BookOpen className="h-4 w-4" />
          </div>
          <span className="flex-1 text-lg font-bold tracking-tight text-slate-900">ARA</span>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-500 hover:bg-slate-200 lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-3">
          <button
            type="button"
            onClick={() => {
              onNewChat()
              onClose()
            }}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" /> New research
          </button>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-3 px-3 pb-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Reference documents
          </h2>
          <DocumentUploader uploads={docs.uploads} onFiles={docs.upload} onDismiss={docs.dismissUpload} />
          <div className="min-h-0 flex-1 overflow-y-auto">
            <DocumentList
              documents={docs.documents}
              loading={docs.loading}
              error={docs.error}
              isIncluded={docs.isIncluded}
              onToggle={docs.toggleIncluded}
              onRemove={docs.remove}
            />
          </div>
        </div>
      </aside>
    </>
  )
}
