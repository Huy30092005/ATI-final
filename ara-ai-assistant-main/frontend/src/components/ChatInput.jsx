import { useRef, useState } from 'react'
import { ArrowUp, FileText, Globe, GraduationCap } from 'lucide-react'

const SOURCE_TOGGLES = [
  { key: 'documents', label: 'My documents', Icon: FileText },
  { key: 'web', label: 'Web', Icon: Globe },
  { key: 'academic', label: 'Academic', Icon: GraduationCap },
]

export default function ChatInput({ onSend, disabled, sources, onToggleSource, contextDocCount }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  const submit = () => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleChange = (e) => {
    setValue(e.target.value)
    // Tự giãn chiều cao theo nội dung (tối đa 200px)
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
  }

  const handleKeyDown = (e) => {
    // isComposing: tránh gửi nhầm khi đang gõ tiếng Việt (Telex/VNI)
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t border-slate-200 bg-white px-4 py-3">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-2xl border border-slate-300 bg-white p-2 shadow-sm focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-200">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder="Ask a research question…"
            className="max-h-[200px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-slate-400"
          />
          <button
            type="button"
            onClick={submit}
            disabled={disabled || !value.trim()}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            aria-label="Send"
          >
            <ArrowUp className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500">Search in:</span>
          {SOURCE_TOGGLES.map(({ key, label, Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => onToggleSource(key)}
              aria-pressed={sources[key]}
              className={`flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
                sources[key]
                  ? 'border-brand-500 bg-brand-50 text-brand-700'
                  : 'border-slate-300 text-slate-500 hover:bg-slate-100'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
              {key === 'documents' && sources.documents && ` (${contextDocCount})`}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
