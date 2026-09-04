"""
Thin wrapper around Razorpay's real Payment Links API
(https://razorpay.com/docs/payments/payment-links/).

If real RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET are configured (via .env),
this creates an actual test-mode Payment Link -- a real `plink_...` id
and a genuinely clickable checkout URL on Razorpay's sandbox.

If no credentials are configured, or the API call fails for any reason
(network, invalid keys, rate limit, etc.), this falls back to a clearly
labelled mock link so the rest of the pipeline keeps working -- the
agent's job is revenue recovery logic, not being a demo that crashes
because a key wasn't set.
"""
import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

_client = None
if _KEY_ID and _KEY_SECRET and _KEY_ID != "rzp_test_xxxxxxxxxxxx":
    _client = razorpay.Client(auth=(_KEY_ID, _KEY_SECRET))


def is_live() -> bool:
    """Whether we have real Razorpay credentials configured."""
    return _client is not None


def create_recovery_link(checkout: dict) -> dict:
    """
    Creates a real Razorpay test-mode Payment Link for a recovery attempt.

    Returns:
        {
          "live": bool,               # True if this hit the real API
          "id": str,                  # plink_... (real) or MOCK-... (fallback)
          "short_url": str,           # real clickable rzp.io link, or a mock one
          "status": str,              # real status from Razorpay, or "mocked"
        }
    """
    if _client is None:
        return _mock_link(checkout)

    amount_paise = int(round(checkout["cart_value_inr"] * 100))
    try:
        link = _client.payment_link.create({
            "amount": amount_paise,
            "currency": "INR",
            "description": f"Complete your purchase - {checkout['checkout_id']}",
            "customer": {
                "name": checkout["customer_name"],
                # Test-mode Payment Links don't actually deliver notifications
                # to arbitrary synthetic contacts, so we omit contact/email
                # here to avoid Razorpay attempting real delivery.
            },
            "notify": {"sms": False, "email": False},
            "reference_id": checkout["checkout_id"],
            "callback_method": "get",
        })
        return {
            "live": True,
            "id": link["id"],
            "short_url": link["short_url"],
            "status": link.get("status", "created"),
        }
    except Exception as e:  # noqa: BLE001 -- deliberately broad: any API/network
        # failure here should degrade to the mock, not crash the batch.
        return _mock_link(checkout, error=str(e))


def _mock_link(checkout: dict, error: str | None = None) -> dict:
    return {
        "live": False,
        "id": f"MOCK-{checkout['checkout_id']}",
        "short_url": f"https://rzp.io/recover/{checkout['checkout_id']}",
        "status": "mocked" if not error else f"mock_fallback ({error[:80]})",
    }
