"""
Diagnosis layer.

Most "abandoned checkout" demos treat every failure the same
("payment failed -> send reminder"). This module actually reasons
about *why* a UPI/card payment failed and how recoverable it is,
because the right recovery action is completely different for
"bank server timeout" (just retry) vs "insufficient balance"
(needs a delay + maybe a smaller basket) vs "user cancelled"
(low odds, don't spam them).
"""

# reason -> (recoverability 0-1, human explanation, suggested wait before retry hrs)
FAILURE_PROFILES = {
    "bank_server_timeout":     (0.85, "Payment rail (NPCI/bank) timed out mid-transaction. Not the customer's fault.", 0),
    "upi_app_crash":           (0.80, "Customer's UPI app crashed before confirming. Likely still wants to buy.", 0),
    "network_drop":            (0.80, "Connectivity dropped during payment. Likely still wants to buy.", 0),
    "otp_not_received":        (0.70, "OTP/SMS delivery was delayed. Customer probably still intends to pay.", 1),
    "wrong_vpa_entered":       (0.55, "Customer mistyped their UPI ID. Needs a corrected/guided payment link, not a plain reminder.", 0),
    "daily_limit_exceeded":    (0.50, "Bank-imposed daily UPI limit was hit. Won't succeed until limit resets.", 24),
    "insufficient_balance":    (0.30, "Customer likely doesn't have funds right now.", 48),
    "user_cancelled_mid_flow": (0.15, "Customer actively backed out. Low odds a reminder changes their mind.", 12),
}


def diagnose(checkout: dict) -> dict:
    reason = checkout["failure_reason"]
    recoverability, explanation, wait_hours = FAILURE_PROFILES.get(
        reason, (0.4, "Unrecognised failure reason.", 6)
    )
    return {
        "failure_reason": reason,
        "recoverability_score": recoverability,
        "explanation": explanation,
        "recommended_wait_hours": wait_hours,
    }
