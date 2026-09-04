"""
Diagnosis layer -- built directly on Razorpay's real, documented payment
error schema (code / description / source / step / reason / metadata),
not an invented taxonomy.

Reference: Razorpay's error response and error-reasons documentation.
Every "reason" value below is a real, documented value Razorpay's API
returns (razorpay.com/docs/payment-gateway/rainy-day/errors/). We map
each one to a recoverability score and a plain-English explanation for
our own downstream decisioning -- Razorpay documents the error, our
diagnosis layer decides what it means for revenue recovery.

Each profile also carries the real `source` (who/what caused it:
customer, business, bank, gateway) and `step` (where in the payment
flow it happened) fields, because those are what let a downstream
system route the case correctly -- a `source: customer` failure needs
a nudge to the customer; a `source: bank` failure needs a wait-and-retry,
not an apology email.
"""

# reason -> (recoverability 0-1, source, step, explanation, wait_hours)
FAILURE_PROFILES = {
    "bank_technical_error": (
        0.80, "bank", "payment_authorization",
        "The issuing bank's core banking system hit a technical fault while processing the payment. Not the customer's fault.",
        0,
    ),
    "gateway_technical_error": (
        0.80, "gateway", "payment_authorization",
        "A technical fault occurred at the payment gateway layer. Not the customer's fault.",
        0,
    ),
    "issuer_technical_error": (
        0.78, "bank", "payment_authorization",
        "A technical fault at the card/UPI issuer interrupted authorization.",
        0,
    ),
    "upi_app_technical_error": (
        0.78, "gateway", "payment_authorization",
        "The customer's UPI app (PSP) hit a technical error mid-payment.",
        0,
    ),
    "payment_session_expired": (
        0.70, "customer", "payment_initiation",
        "The customer didn't complete the payment within the active session window.",
        0,
    ),
    "payment_collect_request_expired": (
        0.65, "customer", "payment_authentication",
        "The UPI collect request expired before the customer approved it on their app.",
        0,
    ),
    "incorrect_otp": (
        0.65, "customer", "payment_authentication",
        "The customer entered the wrong OTP during authentication.",
        0,
    ),
    "otp_expired": (
        0.65, "customer", "payment_authentication",
        "The OTP expired before the customer could enter it.",
        0,
    ),
    "invalid_vpa": (
        0.55, "customer", "payment_initiation",
        "The customer entered an invalid or unregistered UPI ID.",
        0,
    ),
    "insufficient_funds": (
        0.30, "customer", "payment_authorization",
        "The customer's account didn't have enough balance at the time of the attempt.",
        48,
    ),
    "transaction_daily_limit_exceeded": (
        0.50, "bank", "payment_authorization",
        "The customer hit their bank-imposed daily transaction limit.",
        24,
    ),
    "card_declined": (
        0.35, "bank", "payment_authorization",
        "The issuing bank declined the card without sharing a specific reason.",
        6,
    ),
    "payment_cancelled": (
        0.15, "customer", "payment_authentication",
        "The customer explicitly backed out before completing authentication.",
        12,
    ),
    "payment_declined": (
        0.20, "bank", "payment_authorization",
        "The bank or gateway declined the payment for business or risk reasons not shared with Razorpay.",
        6,
    ),
}

# Fallback for any reason value not explicitly profiled above -- keeps the
# pipeline safe if Razorpay's live API returns a reason we haven't mapped yet.
_DEFAULT_PROFILE = (0.4, "unknown", "unknown", "Unrecognised failure reason from the payment API.", 6)


def diagnose(checkout: dict) -> dict:
    """
    Expects checkout['failure_reason'] to be one of Razorpay's real,
    documented `reason` values. Also accepts optional real `source` and
    `step` fields if they were captured directly from a live API error
    response (see backend/razorpay_client.py) -- falls back to our
    profiled defaults if the checkout only carries a reason string.
    """
    reason = checkout["failure_reason"]
    recoverability, default_source, default_step, explanation, wait_hours = FAILURE_PROFILES.get(
        reason, _DEFAULT_PROFILE
    )
    return {
        "failure_reason": reason,
        "source": checkout.get("source", default_source),
        "step": checkout.get("step", default_step),
        "recoverability_score": recoverability,
        "explanation": explanation,
        "recommended_wait_hours": wait_hours,
    }
