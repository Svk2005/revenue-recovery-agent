"""
AI-powered diagnosis layer.

Gemini analyzes the checkout first and provides an AI diagnosis.

If Gemini is unavailable or returns invalid data, we safely fall back
to Razorpay-based deterministic diagnosis.

The deterministic profiles below are based on Razorpay's documented
payment error taxonomy and act as the safety fallback.
"""

from agent.ai_agent import diagnose_with_ai


# reason -> (recoverability 0-1, source, step, explanation, wait_hours)

FAILURE_PROFILES = {
    "bank_technical_error": (
        0.80,
        "bank",
        "payment_authorization",
        "The issuing bank's core banking system hit a technical fault while processing the payment. Not the customer's fault.",
        0,
    ),

    "gateway_technical_error": (
        0.80,
        "gateway",
        "payment_authorization",
        "A technical fault occurred at the payment gateway layer. Not the customer's fault.",
        0,
    ),

    "issuer_technical_error": (
        0.78,
        "bank",
        "payment_authorization",
        "A technical fault at the card/UPI issuer interrupted authorization.",
        0,
    ),

    "upi_app_technical_error": (
        0.78,
        "gateway",
        "payment_authorization",
        "The customer's UPI app (PSP) hit a technical error mid-payment.",
        0,
    ),

    "payment_session_expired": (
        0.70,
        "customer",
        "payment_initiation",
        "The customer didn't complete the payment within the active session window.",
        0,
    ),

    "payment_collect_request_expired": (
        0.65,
        "customer",
        "payment_authentication",
        "The UPI collect request expired before the customer approved it on their app.",
        0,
    ),

    "incorrect_otp": (
        0.65,
        "customer",
        "payment_authentication",
        "The customer entered the wrong OTP during authentication.",
        0,
    ),

    "otp_expired": (
        0.65,
        "customer",
        "payment_authentication",
        "The OTP expired before the customer could enter it.",
        0,
    ),

    "invalid_vpa": (
        0.55,
        "customer",
        "payment_initiation",
        "The customer entered an invalid or unregistered UPI ID.",
        0,
    ),

    "insufficient_funds": (
        0.30,
        "customer",
        "payment_authorization",
        "The customer's account didn't have enough balance at the time of the attempt.",
        48,
    ),

    "transaction_daily_limit_exceeded": (
        0.50,
        "bank",
        "payment_authorization",
        "The customer hit their bank-imposed daily transaction limit.",
        24,
    ),

    "card_declined": (
        0.35,
        "bank",
        "payment_authorization",
        "The issuing bank declined the card without sharing a specific reason.",
        6,
    ),

    "payment_cancelled": (
        0.15,
        "customer",
        "payment_authentication",
        "The customer explicitly backed out before completing authentication.",
        12,
    ),

    "payment_declined": (
        0.20,
        "bank",
        "payment_authorization",
        "The bank or gateway declined the payment for business or risk reasons not shared with Razorpay.",
        6,
    ),
}


# Safe fallback for unknown Razorpay reasons

_DEFAULT_PROFILE = (
    0.4,
    "unknown",
    "unknown",
    "Unrecognised failure reason from the payment API.",
    6,
)


def diagnose(checkout: dict) -> dict:
    """
    Uses Gemini to diagnose the checkout.

    If Gemini fails or is unavailable, the system falls back
    to deterministic Razorpay-based diagnosis.
    """

    reason = checkout["failure_reason"]

    # ---------------------------------------------------------
    # 1. Try AI diagnosis
    # ---------------------------------------------------------

    try:
        ai_result = diagnose_with_ai(checkout)

        # AI explicitly says it is unavailable
        if not ai_result.get("available", True):
            raise RuntimeError("AI unavailable")

        # Only accept AI output when it contains the required fields
        if (
            isinstance(ai_result, dict)
            and "diagnosis" in ai_result
            and "confidence" in ai_result
            and "action" in ai_result
        ):
            return {
                "failure_reason": reason,

                "source": checkout.get("source", "ai"),

                "step": checkout.get(
                    "step",
                    "ai_diagnosis"
                ),

                "recoverability_score": float(
                    0.8
                    if ai_result.get("recoverable", False)
                    else 0.2
                ),

                "explanation": ai_result.get(
                    "reason",
                    ai_result.get(
                        "diagnosis",
                        "AI diagnosis completed."
                    ),
                ),

                "recommended_wait_hours": 0,

                # AI information for dashboard/audit
                "ai_diagnosis": ai_result.get("diagnosis"),

                "ai_action": ai_result.get("action"),

                "ai_confidence": float(
                    ai_result.get("confidence", 0)
                ),
            }

    except Exception:
        # If Gemini fails, continue to deterministic fallback.
        pass

    # ---------------------------------------------------------
    # 2. Deterministic Razorpay fallback
    # ---------------------------------------------------------

    (
        recoverability,
        default_source,
        default_step,
        explanation,
        wait_hours,
    ) = FAILURE_PROFILES.get(
        reason,
        _DEFAULT_PROFILE
    )

    return {
        "failure_reason": reason,

        "source": checkout.get(
            "source",
            default_source
        ),

        "step": checkout.get(
            "step",
            default_step
        ),

        "recoverability_score": recoverability,

        "explanation": explanation,

        "recommended_wait_hours": wait_hours,

        # AI was unavailable, so policy must ignore AI recommendation.
        "ai_diagnosis": (
            "AI temporarily unavailable — "
            "deterministic Razorpay diagnosis used"
        ),

        # Empty means there was NO AI recommendation.
        "ai_action": "",

        "ai_confidence": 0.0,
    }