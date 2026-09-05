import { useState } from 'react'
import type { AuditRow } from './types'
import { ChevronDown } from 'lucide-react'

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'sent', label: 'Sent' },
  { key: 'failed_gracefully', label: 'Handled' },
  { key: 'routed_to_human', label: 'Human' },
  { key: 'skipped', label: 'Skipped' },
] as const

const GRID_COLS = 'sm:grid-cols-[1.4fr_1fr_1.2fr_1fr_0.8fr_1fr_20px]'

function outcomeColor(outcome: string) {
  if (outcome === 'sent') return 'text-recovered'
  if (outcome === 'failed_gracefully') return 'text-failed'
  if (outcome === 'routed_to_human') return 'text-pending'
  return 'text-muted'
}

function outcomeLabel(row: AuditRow) {
  const base = row.send_outcome.replace(/_/g, ' ')
  if (row.send_outcome === 'sent' && row.payment_status) {
    return `${base} · ${row.payment_status}`
  }
  return base
}

export function AuditTable({ rows }: { rows: AuditRow[] }) {
  const [filter, setFilter] = useState<string>('all')
  const [expanded, setExpanded] = useState<string | null>(null)

  const filtered = filter === 'all' ? rows : rows.filter((r) => r.send_outcome === filter)

  return (
    <div>
      <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
        <div className="text-muted text-sm">Audit trail</div>
        <div className="flex gap-3 sm:gap-4 text-xs sm:text-sm flex-wrap">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`pb-1 border-b transition-colors ${
                filter === f.key
                  ? 'text-paper border-brass'
                  : 'text-muted border-transparent hover:text-paper'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="border-t border-line">
        {/* Column header row -- desktop only, hidden on mobile where rows stack instead */}
        <div className={`hidden sm:grid ${GRID_COLS} gap-3 py-2 text-xs text-muted border-b border-line-soft`}>
          <span>Customer</span>
          <span className="text-right">Cart value</span>
          <span>Failure reason</span>
          <span>Action</span>
          <span className="text-right">Recoverability</span>
          <span>Outcome</span>
          <span />
        </div>

        {filtered.map((row) => {
          const isOpen = expanded === row.checkout_id
          return (
            <div key={row.checkout_id} className="border-b border-line-soft">
              <button
                onClick={() => setExpanded(isOpen ? null : row.checkout_id)}
                className={`w-full grid grid-cols-1 ${GRID_COLS} gap-1 sm:gap-3 py-3 text-sm text-left sm:items-center hover:bg-surface transition-colors`}
              >
                {/* Mobile: name + value on one line */}
                <div className="flex items-center justify-between sm:contents">
                  <span className="text-paper truncate">{row.customer_name}</span>
                  <span className="font-mono tabular text-right text-paper">
                    ₹{Math.round(row.cart_value_inr).toLocaleString('en-IN')}
                  </span>
                </div>

                <span className="hidden sm:inline text-muted truncate">
                  {row.failure_reason.replace(/_/g, ' ')}
                </span>
                <span className="hidden sm:inline text-muted truncate">
                  {row.policy_action.replace(/_/g, ' ')}
                </span>
                <span className="hidden sm:inline font-mono tabular text-right text-muted">
                  {row.recoverability_score.toFixed(2)}
                </span>

                {/* Mobile: reason/action/outcome condensed onto one line */}
                <div className="flex items-center justify-between gap-2 sm:contents">
                  <span className="sm:hidden text-muted text-xs truncate">
                    {row.failure_reason.replace(/_/g, ' ')} · {row.policy_action.replace(/_/g, ' ')}
                  </span>
                  <span className={`text-xs whitespace-nowrap ${outcomeColor(row.send_outcome)}`}>
                    {outcomeLabel(row)}
                  </span>
                </div>

                <ChevronDown
                  size={14}
                  className={`hidden sm:block text-muted transition-transform justify-self-end ${isOpen ? 'rotate-180' : ''}`}
                />
              </button>

              {isOpen && (
                <div className="pb-4 pl-1 pr-2 sm:pr-6 text-sm text-muted grid gap-2 max-w-2xl">
                  <div>
                    <span className="text-paper">Diagnosis: </span>
                    {row.diagnosis_explanation}
                    <span className="text-xs ml-2">
                      (source: {row.source}, step: {row.step.replace(/_/g, ' ')})
                    </span>
                  </div>
                  <div>
                    <span className="text-paper">Policy reasoning: </span>
                    {row.policy_reasoning}
                  </div>
                  {row.message_sent && (
                    <div>
                      <span className="text-paper">Message: </span>
                      <span className="font-mono text-xs break-words">{row.message_sent}</span>
                    </div>
                  )}
                  {row.payment_link_id && (
                    <div>
                      <span className="text-paper">Payment link: </span>
                      <span className="font-mono text-xs break-all">{row.payment_link_id}</span>
                      <span className={`text-xs ml-2 ${row.payment_link_live ? 'text-recovered' : 'text-muted'}`}>
                        {row.payment_link_live ? '(live Razorpay API)' : '(mock — no API keys configured)'}
                      </span>
                    </div>
                  )}
                  {row.expected_recovered_value_inr > 0 && (
                    <div>
                      <span className="text-paper">Expected value (estimate): </span>
                      <span className="font-mono text-muted">
                        ₹{Math.round(row.expected_recovered_value_inr).toLocaleString('en-IN')}
                      </span>
                      <span className="text-paper ml-4">Measured value: </span>
                      <span className={`font-mono ${row.payment_status === 'confirmed' ? 'text-recovered' : 'text-muted'}`}>
                        ₹{Math.round(row.measured_recovered_value_inr).toLocaleString('en-IN')}
                        {row.payment_status === 'pending' && ' (pending confirmation)'}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {filtered.length === 0 && (
          <div className="py-10 text-center text-muted text-sm">
            No checkouts in this category for the current batch.
          </div>
        )}
      </div>
    </div>
  )
}