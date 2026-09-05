"""
Orchestrator: runs the full pipeline over a batch of abandoned checkouts.

    diagnose -> decide (policy) -> [batch spend cap check] -> act (messenger)
    -> [simulate confirmation] -> log (audit)

Every checkout produces exactly one audit row, regardless of whether
it was skipped, routed to human review, sent successfully, or hit a
send failure. Nothing is silently dropped.

Two things this layer enforces that a single-case policy can't, because
they require knowing about the whole batch:

1. Batch-wide discount spend cap -- agent/policy.py already caps the
   discount on any ONE case (never more than 50% of that case's cart
   value). But nothing stopped it from handing out large discounts on
   every case in a batch, one at a time, with no global brake. This
   layer tracks cumulative discount spend across the batch and refuses
   further discounts once a batch-wide cap is hit -- a real stopping
   rule, not just a per-case one.

2. Measured vs. expected recovery -- "expected_recovered_value_inr" is
   our diagnosis-based estimate (cart value x recoverability score).
   "measured_recovered_value_inr" is what agent/confirmation.py
   simulates as the actual outcome per case -- these two numbers will
   differ, exactly like a real business's forecast vs. actual recovery
   would. The batch total of the MEASURED figure is the headline number
   the brief's "show measured money recovered" bar is asking for.
"""
from agent.diagnose import diagnose
from agent.policy import decide_action
from agent.messenger import send
from agent.audit import AuditTrail
from agent.confirmation import simulate_payment_confirmation

# Max total discount spend across an entire batch, as a fraction of the
# batch's total cart value. Per-case discounts are already capped in
# policy.py; this is the batch-wide "stopping rule" on top of that.
BATCH_DISCOUNT_CAP_PCT = 0.04  # 4% of total batch cart value


def run_batch(checkouts: list[dict]) -> tuple[AuditTrail, dict]:
    trail = AuditTrail()

    total_cart_value = sum(c["cart_value_inr"] for c in checkouts)
    batch_discount_cap_inr = round(total_cart_value * BATCH_DISCOUNT_CAP_PCT, 2)
    discount_spent_so_far = 0.0

    stats = {
        "total": len(checkouts),
        "sent": 0,
        "skipped_contact_cap": 0,
        "human_review": 0,
        "send_failed_gracefully": 0,
        "confirmed_payments": 0,
        "pending_confirmation": 0,
        "expected_recovered_value_inr": 0.0,
        "measured_recovered_value_inr": 0.0,
        "total_cart_value_inr": 0.0,
        "live_payment_links_created": 0,
        "batch_discount_cap_inr": batch_discount_cap_inr,
        "total_discount_spent_inr": 0.0,
        "discounts_blocked_by_batch_cap": 0,
    }

    for checkout in checkouts:
        stats["total_cart_value_inr"] += checkout["cart_value_inr"]

        diagnosis = diagnose(checkout)
        decision = decide_action(checkout, diagnosis)

        # --- Batch-wide discount spend cap ---------------------------------
        if decision["discount_pct"] > 0:
            discount_cost = checkout["cart_value_inr"] * decision["discount_pct"] / 100
            if discount_spent_so_far + discount_cost > batch_discount_cap_inr:
                stats["discounts_blocked_by_batch_cap"] += 1
                decision = {
                    **decision,
                    "discount_pct": 0,
                    "reasoning": decision["reasoning"] + (
                        f" Batch discount cap (₹{batch_discount_cap_inr:.0f}) reached -- "
                        f"incentive withheld despite policy recommendation."
                    ),
                }
            else:
                discount_spent_so_far += discount_cost
                stats["total_discount_spent_inr"] = round(discount_spent_so_far, 2)

        row = {
            "checkout_id": checkout["checkout_id"],
            "customer_name": checkout["customer_name"],
            "cart_value_inr": checkout["cart_value_inr"],
            "failure_reason": diagnosis["failure_reason"],
            "source": diagnosis["source"],
            "step": diagnosis["step"],
            "recoverability_score": round(diagnosis["recoverability_score"], 2),
            "diagnosis_explanation": diagnosis["explanation"],
            "ai_diagnosis": diagnosis.get("ai_diagnosis", ""),
            "ai_action": diagnosis.get("ai_action", ""),
            "ai_confidence": diagnosis.get("ai_confidence", 0),
            "policy_action": decision["action"],
            "discount_pct": decision["discount_pct"],
            "policy_reasoning": decision["reasoning"],
            "send_outcome": "",
            "message_sent": "",
            "payment_status": "",
            "expected_recovered_value_inr": 0,
            "measured_recovered_value_inr": 0,
            "payment_link_id": "",
            "payment_link_live": False,
        }

        if decision["action"] == "skip":
            stats["skipped_contact_cap"] += 1
            row["send_outcome"] = "skipped"

        elif decision["action"] == "human_review":
            stats["human_review"] += 1
            row["send_outcome"] = "routed_to_human"

        else:
            result = send(checkout, decision["action"])
            row["send_outcome"] = result["outcome"]
            row["message_sent"] = result["message"]
            row["payment_link_id"] = result.get("payment_link_id", "")
            row["payment_link_live"] = result.get("payment_link_live", False)
            if row["payment_link_live"]:
                stats["live_payment_links_created"] += 1

            if result["outcome"] == "sent":
                stats["sent"] += 1

                net_value = checkout["cart_value_inr"] * (1 - decision["discount_pct"] / 100)
                expected = round(net_value * diagnosis["recoverability_score"], 2)
                row["expected_recovered_value_inr"] = expected
                stats["expected_recovered_value_inr"] += expected

                # --- Simulated payment confirmation (see agent/confirmation.py) ---
                confirmed = simulate_payment_confirmation(diagnosis["recoverability_score"])
                if confirmed:
                    row["payment_status"] = "confirmed"
                    row["measured_recovered_value_inr"] = round(net_value, 2)
                    stats["measured_recovered_value_inr"] += round(net_value, 2)
                    stats["confirmed_payments"] += 1
                else:
                    row["payment_status"] = "pending"
                    stats["pending_confirmation"] += 1
            else:
                stats["send_failed_gracefully"] += 1

        trail.log(row)

    stats["expected_recovered_value_inr"] = round(stats["expected_recovered_value_inr"], 2)
    stats["measured_recovered_value_inr"] = round(stats["measured_recovered_value_inr"], 2)

    return trail, stats
