"""
Orchestrator: runs the full pipeline over a batch of abandoned checkouts.

    diagnose -> decide (policy) -> act (messenger) -> log (audit)

Every checkout produces exactly one audit row, regardless of whether
it was skipped, routed to human review, sent successfully, or hit a
send failure. Nothing is silently dropped.
"""
from agent.diagnose import diagnose
from agent.policy import decide_action
from agent.messenger import send
from agent.audit import AuditTrail


def run_batch(checkouts: list[dict]) -> tuple[AuditTrail, dict]:
    trail = AuditTrail()
    stats = {
        "total": len(checkouts),
        "sent": 0,
        "skipped_contact_cap": 0,
        "human_review": 0,
        "send_failed_gracefully": 0,
        "recovered_value_inr": 0.0,
        "total_cart_value_inr": 0.0,
        "live_payment_links_created": 0,
    }

    for checkout in checkouts:
        stats["total_cart_value_inr"] += checkout["cart_value_inr"]

        diagnosis = diagnose(checkout)
        decision = decide_action(checkout, diagnosis)

        row = {
            "checkout_id": checkout["checkout_id"],
            "customer_name": checkout["customer_name"],
            "cart_value_inr": checkout["cart_value_inr"],
            "failure_reason": diagnosis["failure_reason"],
            "source": diagnosis["source"],
            "step": diagnosis["step"],
            "recoverability_score": round(diagnosis["recoverability_score"], 2),
            "diagnosis_explanation": diagnosis["explanation"],
            "policy_action": decision["action"],
            "discount_pct": decision["discount_pct"],
            "policy_reasoning": decision["reasoning"],
            "send_outcome": "",
            "message_sent": "",
            "recovered_value_inr": 0,
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
                # simple recovery-value estimate = cart value * recoverability
                # score, net of any discount offered -- used for the scorecard,
                # not claimed as a guaranteed recovery.
                net_value = checkout["cart_value_inr"] * (1 - decision["discount_pct"] / 100)
                estimated_recovered = round(net_value * diagnosis["recoverability_score"], 2)
                row["recovered_value_inr"] = estimated_recovered
                stats["recovered_value_inr"] += estimated_recovered
            else:
                stats["send_failed_gracefully"] += 1

        trail.log(row)

    return trail, stats
