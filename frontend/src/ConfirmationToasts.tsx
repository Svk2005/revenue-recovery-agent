import { useEffect, useState } from 'react'
import type { AuditRow } from './types'

interface Toast {
  id: string
  name: string
  amount: number
}

function formatInr(n: number) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(n)
}

/**
 * Watches for newly-confirmed payments in a batch and surfaces them as a
 * staggered live feed of toast notifications -- "customer came back and
 * paid" made visible, instead of sitting quietly in a table row.
 *
 * Purely presentational: reads payment_status/measured_recovered_value_inr
 * that the backend already produces (see agent/confirmation.py). No new
 * data or backend changes required.
 */
export function ConfirmationToasts({ rows, batchKey }: { rows: AuditRow[]; batchKey: string }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  useEffect(() => {
    const confirmed = rows.filter((r) => r.payment_status === 'confirmed')
    if (confirmed.length === 0) return

    const timers: number[] = []
    // Stagger toasts so they read as a live feed rather than a wall of text.
    // Cap how many we show so a large batch doesn't spam the screen.
    const toShow = confirmed.slice(0, 8)

    toShow.forEach((row, i) => {
      const showAt = 400 + i * 900
      const hideAfter = showAt + 3200
      const id = `${batchKey}-${row.checkout_id}`

      timers.push(
        window.setTimeout(() => {
          setToasts((prev) => [
            ...prev,
            { id, name: row.customer_name.split(' ')[0], amount: row.measured_recovered_value_inr },
          ])
        }, showAt)
      )
      timers.push(
        window.setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id))
        }, hideAfter)
      )
    })

    return () => timers.forEach((t) => window.clearTimeout(t))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [batchKey])

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-[calc(100vw-2rem)] sm:max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="bg-surface-raised border border-recovered/40 px-4 py-3 shadow-lg animate-[toast-in_0.25s_ease-out]"
        >
          <div className="flex items-center gap-2 text-sm">
            <span className="text-recovered">✓</span>
            <span className="text-paper">
              <span className="font-medium">{t.name}</span> just completed payment
            </span>
          </div>
          <div className="font-mono tabular text-recovered text-sm mt-1">
            ₹{formatInr(t.amount)} recovered
          </div>
        </div>
      ))}
    </div>
  )
} 