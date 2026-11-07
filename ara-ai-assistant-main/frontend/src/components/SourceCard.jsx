import { ExternalLink } from 'lucide-react'
import { getSourceType } from '../lib/sourceTypes'

function ScoreBar({ label, value = 0 }) {
  const percent = Math.round(Math.min(Math.max(value, 0), 1) * 100)
  return (
    <div className="flex items-center gap-2">
      <span className="w-16 shrink-0 text-[11px] text-slate-500">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full rounded-full bg-brand-500" style={{ width: `${percent}%` }} />
      </div>
      <span className="w-8 text-right text-[11px] tabular-nums text-slate-500">{percent}%</span>
    </div>
  )
}

export default function SourceCard({ index, source, highlighted }) {
  const { label, Icon, badge } = getSourceType(source.source_type)

  return (
    <article
      id={`source-${index}`}
      className={`rounded-xl border bg-white p-3 transition-shadow ${
        highlighted ? 'border-brand-500 ring-2 ring-brand-200' : 'border-slate-200'
      }`}
    >
      <div className="flex items-start gap-2">
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-brand-100 text-xs font-bold text-brand-700">
          {index}
        </span>
        <div className="min-w-0 flex-1">
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${badge}`}
          >
            <Icon className="h-3 w-3" /> {label}
          </span>

          {source.url ? (
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="mt-1 flex items-start gap-1 text-sm font-semibold text-slate-900 hover:text-brand-600"
            >
              <span className="min-w-0 flex-1">{source.title}</span>
              <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            </a>
          ) : (
            <h3 className="mt-1 text-sm font-semibold text-slate-900">{source.title}</h3>
          )}

          {(source.authors || source.year) && (
            <p className="mt-0.5 text-xs text-slate-500">
              {[source.authors, source.year].filter(Boolean).join(' · ')}
            </p>
          )}
        </div>
      </div>

      {source.snippet && <p className="mt-2 line-clamp-4 text-xs leading-relaxed text-slate-600">{source.snippet}</p>}

      <div className="mt-3 space-y-1">
        <ScoreBar label="Relevance" value={source.relevance} />
        <ScoreBar label="Credibility" value={source.credibility} />
      </div>
    </article>
  )
}
