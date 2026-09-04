import type { BatchStats } from './types'

export function OutcomeBar({ stats }: { stats: BatchStats }) {
  const segments = [
    { label: 'Sent', value: stats.sent, color: 'bg-recovered' },
    { label: 'Handled failure', value: stats.send_failed_gracefully, color: 'bg-failed' },
    { label: 'Human review', value: stats.human_review, color: 'bg-pending' },
    { label: 'Skipped', value: stats.skipped_contact_cap, color: 'bg-line' },
  ]
  const total = segments.reduce((s, seg) => s + seg.value, 0) || 1

  return (
    <div className="mb-10">
      <div className="text-muted text-sm mb-3">How the batch was handled</div>
      <div className="flex w-full h-2 rounded-sm overflow-hidden">
        {segments.map((seg) => (
          <div
            key={seg.label}
            className={seg.color}
            style={{ width: `${(seg.value / total) * 100}%` }}
            title={`${seg.label}: ${seg.value}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-2 mt-3 text-xs">
        {segments.map((seg) => (
          <div key={seg.label} className="flex items-center gap-2">
            <span className={`w-2 h-2 ${seg.color}`} />
            <span className="text-muted">{seg.label}</span>
            <span className="font-mono text-paper tabular">{seg.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
