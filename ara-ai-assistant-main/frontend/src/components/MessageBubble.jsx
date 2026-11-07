import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Check, CircleAlert, Copy, Library, Sparkles } from 'lucide-react'

// "... đã được chứng minh [2]" -> "... [2](#cite-2)" để biến thành nút bấm được
// (?!\() tránh đụng vào link Markdown có sẵn dạng [1](https://...)
const addCitationLinks = (text) => text.replace(/\[(\d{1,2})\](?!\()/g, '[$1](#cite-$1)')

export default function MessageBubble({ message, isActive, onCite, onShowEvidence }) {
  const [copied, setCopied] = useState(false)

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-brand-600 px-4 py-2.5 text-sm text-white">
          {message.content}
        </div>
      </div>
    )
  }

  const evidenceCount = message.evidence?.length ?? 0

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* trình duyệt chặn clipboard -> bỏ qua */
    }
  }

  const components = {
    a({ href, children }) {
      if (href?.startsWith('#cite-')) {
        const n = Number(href.slice('#cite-'.length))
        return (
          <button
            type="button"
            onClick={() => onCite(message.id, n)}
            className="mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-md bg-brand-100 px-1 align-text-top text-xs font-semibold text-brand-700 hover:bg-brand-200"
            title={`Show source ${n}`}
          >
            {children}
          </button>
        )
      }
      return (
        <a href={href} target="_blank" rel="noreferrer">
          {children}
        </a>
      )
    },
  }

  return (
    <div className="flex gap-3">
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          message.isError ? 'bg-red-100 text-red-600' : 'bg-brand-100 text-brand-700'
        }`}
      >
        {message.isError ? <CircleAlert className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
      </div>

      <div className="min-w-0 flex-1">
        {message.isError ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {message.content}
          </p>
        ) : (
          <div
            className={`rounded-2xl rounded-tl-md border bg-white px-4 py-3 text-sm text-slate-800 ${
              isActive ? 'border-brand-200 shadow-sm' : 'border-slate-200'
            }`}
          >
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
                {addCitationLinks(message.content)}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {!message.isError && (
          <div className="mt-1.5 flex items-center gap-1 text-xs text-slate-500">
            {evidenceCount > 0 && (
              <button
                type="button"
                onClick={() => onShowEvidence(message.id)}
                className="flex items-center gap-1 rounded-md px-2 py-1 hover:bg-slate-200"
              >
                <Library className="h-3.5 w-3.5" />
                {evidenceCount} {evidenceCount === 1 ? 'source' : 'sources'}
              </button>
            )}
            <button
              type="button"
              onClick={copy}
              className="flex items-center gap-1 rounded-md px-2 py-1 hover:bg-slate-200"
            >
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
