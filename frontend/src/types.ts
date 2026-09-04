export interface AuditRow {
  checkout_id: string
  customer_name: string
  cart_value_inr: number
  failure_reason: string
  recoverability_score: number
  diagnosis_explanation: string
  policy_action: string
  discount_pct: number
  policy_reasoning: string
  send_outcome: string
  message_sent: string
  recovered_value_inr: number
}

export interface BatchStats {
  total: number
  sent: number
  skipped_contact_cap: number
  human_review: number
  send_failed_gracefully: number
  recovered_value_inr: number
  total_cart_value_inr: number
}

export interface BatchResult {
  rows: AuditRow[]
  stats: BatchStats
}
