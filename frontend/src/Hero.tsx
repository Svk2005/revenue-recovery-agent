import type { BatchStats } from './types'
import { useCountUp } from './useCountUp'

function formatInr(n: number) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(n)
}

export function Hero({ stats }: { stats: BatchStats }) {
  const recovered = useCountUp(stats.recovered_value_inr)
  const rate = stats.total_cart_value_inr > 0
    ? (stats.recovered_value_inr / stats.total_cart_value_inr) * 100
    : 0

  return (
    <div className="border-b border-line pb-10 mb-10">
      <div className="flex items-baseline gap-3 mb-1">
        <span className="text-muted text-sm">Estimated value recovered</span>
      </div>
      <div className="flex items-end gap-4 flex-wrap">
        <div
          className="font-display text-brass leading-none tabular"
          style={{ fontSize: 'clamp(3rem, 8vw, 5.5rem)', fontWeight: 500 }}
        >
          ₹{formatInr(recovered)}
        </div>
        <div className="text-muted font-mono text-sm mb-2">
          {rate.toFixed(1)}% of batch
        </div>
      </div>

      <div className="flex flex-wrap gap-x-10 gap-y-3 mt-8 text-sm">
        <Stat label="Checkouts processed" value={stats.total} />
        <Stat label="Total batch value" value={`₹${formatInr(stats.total_cart_value_inr)}`} />
        <Stat label="Messages sent" value={stats.sent} accent="recovered" />
        <Stat label="Handled failures" value={stats.send_failed_gracefully} accent="failed" />
        <Stat label="Routed to human" value={stats.human_review} accent="pending" />
        <Stat label="Skipped (contact cap)" value={stats.skipped_contact_cap} />
        <Stat
          label={stats.live_payment_links_created > 0 ? "Live Razorpay links created" : "Payment links (mock mode)"}
          value={stats.live_payment_links_created}
          accent={stats.live_payment_links_created > 0 ? "recovered" : undefined}
        />
      </div>
    </div>
  )
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string
  value: string | number
  accent?: 'recovered' | 'failed' | 'pending'
}) {
  const color =
    accent === 'recovered' ? 'text-recovered' :
    accent === 'failed' ? 'text-failed' :
    accent === 'pending' ? 'text-pending' :
    'text-paper'

  return (
    <div className="flex flex-col gap-0.5">
      <span className={`font-mono tabular ${color}`}>{value}</span>
      <span className="text-muted text-xs">{label}</span>
    </div>
  )
}
