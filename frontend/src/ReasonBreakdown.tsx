import type { AuditRow } from './types'

function labelize(reason: string) {
  return reason
    .split('_')
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(' ')
}

export function ReasonBreakdown({ rows }: { rows: AuditRow[] }) {
  const counts = new Map<string, number>()
  for (const r of rows) {
    counts.set(r.failure_reason, (counts.get(r.failure_reason) ?? 0) + 1)
  }
  const entries = [...counts.entries()].sort((a, b) => b[1] - a[1])
  const max = Math.max(...entries.map(([, c]) => c), 1)

  return (
    <div className="mb-10">
      <div className="text-muted text-sm mb-3">Failure reasons diagnosed</div>
      <div className="flex flex-col gap-2">
        {entries.map(([reason, count]) => (
          <div key={reason} className="flex items-center gap-3 text-sm">
            <span className="w-44 shrink-0 text-paper">{labelize(reason)}</span>
            <div className="flex-1 h-1.5 bg-line-soft relative">
              <div
                className="h-full bg-brass-dim absolute left-0 top-0"
                style={{ width: `${(count / max) * 100}%` }}
              />
            </div>
            <span className="font-mono text-muted tabular w-6 text-right">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
