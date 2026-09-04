import { useEffect, useState } from 'react'
import type { BatchResult } from './types'
import { runBatch, getLast } from './api'
import { Hero } from './Hero'
import { OutcomeBar } from './OutcomeBar'
import { ReasonBreakdown } from './ReasonBreakdown'
import { AuditTable } from './AuditTable'

export default function App() {
  const [result, setResult] = useState<BatchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadInitial() {
    try {
      const last = await getLast()
      if (last.rows.length > 0) {
        setResult(last)
        return
      }
    } catch {
      // fall through to running a fresh batch
    }
    await handleRun()
  }

  async function handleRun() {
    setLoading(true)
    setError(null)
    try {
      const data = await runBatch(40)
      setResult(data)
    } catch (e) {
      setError(
        'Could not reach the backend. Make sure it is running: ' +
          'uvicorn backend.main:app --reload --port 8000'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadInitial()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="min-h-screen bg-ink">
      <div className="max-w-3xl mx-auto px-6 py-14">
        <header className="flex items-start justify-between mb-12 gap-4 flex-wrap">
          <div>
            <div className="text-muted text-sm mb-2">Razorpay Buildathon — Track 03</div>
            <h1 className="font-display text-paper text-3xl" style={{ fontWeight: 500 }}>
              Revenue recovery ledger
            </h1>
            <p className="text-muted text-sm mt-2 max-w-md">
              Diagnoses why each checkout failed, decides a bounded and
              cost-aware recovery action, and logs every decision.
            </p>
          </div>
          <button
            onClick={handleRun}
            disabled={loading}
            className="border border-brass text-brass px-4 py-2 text-sm hover:bg-brass hover:text-ink transition-colors disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
          >
            {loading ? 'Running batch…' : 'Run new batch'}
          </button>
        </header>

        {error && (
          <div className="border border-failed text-failed text-sm px-4 py-3 mb-10">
            {error}
          </div>
        )}

        {!result && !error && (
          <div className="text-muted text-sm py-20 text-center">Loading batch…</div>
        )}

        {result && (
          <>
            <Hero stats={result.stats} />
            <OutcomeBar stats={result.stats} />
            <ReasonBreakdown rows={result.rows} />
            <AuditTable rows={result.rows} />
          </>
        )}

        <footer className="mt-16 pt-6 border-t border-line-soft text-muted text-xs">
          Synthetic batch data · Payment sends are mocked · Built for the
          Razorpay Buildathon AI Revenue Recovery track
        </footer>
      </div>
    </div>
  )
}
