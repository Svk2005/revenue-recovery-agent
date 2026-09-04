import type { BatchResult } from './types'

export async function runBatch(n: number = 40): Promise<BatchResult> {
  const res = await fetch(`/api/run?n=${n}`, { method: 'POST' })
  if (!res.ok) throw new Error(`Run failed: ${res.status}`)
  return res.json()
}

export async function getLast(): Promise<BatchResult> {
  const res = await fetch('/api/last')
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`)
  return res.json()
}
