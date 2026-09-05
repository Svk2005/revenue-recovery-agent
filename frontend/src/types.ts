export interface AuditRow {
  checkout_id: string
  customer_name: string
  cart_value_inr: number
  failure_reason: string
  source: string
  step: string
  recoverability_score: number
  diagnosis_explanation: string
  policy_action: string
  discount_pct: number
  policy_reasoning: string
  send_outcome: string
  message_sent: string
  payment_status: string
  expected_recovered_value_inr: number
  measured_recovered_value_inr: number
  payment_link_id: string
  payment_link_live: boolean
}

export interface BatchStats {
  total: number
  sent: number
  skipped_contact_cap: number
  human_review: number
  send_failed_gracefully: number
  confirmed_payments: number
  pending_confirmation: number
  expected_recovered_value_inr: number
  measured_recovered_value_inr: number
  total_cart_value_inr: number
  live_payment_links_created: number
  batch_discount_cap_inr: number
  total_discount_spent_inr: number
  discounts_blocked_by_batch_cap: number
}

export interface BatchResult {
  rows: AuditRow[]
  stats: BatchStats
}
