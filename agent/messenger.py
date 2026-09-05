"""
AI-powered Messenger layer.

Gemini generates a personalized customer message.
If Gemini fails, the existing deterministic templates are used.

Razorpay Payment Links and graceful send-failure handling remain unchanged.
"""

import os
from google import genai

from agent.razorpay_client import create_recovery_link


# Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.5-flash"


TEMPLATES = {
    "send_instant_retry_link": {
        "en": "Hi {name}, your payment of ₹{value} didn't go through due to a temporary issue. Complete it here: {link}",
        "hi-en": "Hi {name}, aapka ₹{value} ka payment temporary issue ki wajah se fail ho gaya. Yahan se complete kar lijiye: {link}",
    },

    "schedule_delayed_reminder": {
        "en": "Hi {name}, we've saved your cart (₹{value}). You can complete your payment here: {link}",
        "hi-en": "Hi {name}, aapka cart (₹{value}) safe rakha hai. Aap yahan se payment complete kar sakte hain: {link}",
    },

    "send_corrected_payment_link": {
        "en": "Hi {name}, there was a small issue with your UPI ID last time. Here's a fresh payment link: {link}",
        "hi-en": "Hi {name}, lagta hai UPI ID mein chhoti si problem thi. Yeh raha ek naya payment link: {link}",
    },
}


class SendError(Exception):
    pass


def _mock_send_whatsapp(phone: str, message: str):
    """Stand-in for a real WhatsApp Business API send call."""

    if phone == "INVALID_NUMBER" or not phone.startswith("+91-"):
        raise SendError(f"Invalid destination number: {phone!r}")

    return {
        "status": "sent",
        "channel": "whatsapp",
        "to": phone,
    }


def _fallback_message(checkout: dict, action: str, link_info: dict) -> str:
    """Use deterministic template if Gemini is unavailable."""

    lang = checkout.get("language_pref", "en")

    template = TEMPLATES.get(
        action,
        TEMPLATES["send_instant_retry_link"]
    ).get(
        lang,
        TEMPLATES["send_instant_retry_link"]["en"]
    )

    return template.format(
        name=checkout["customer_name"].split()[0],
        value=int(checkout["cart_value_inr"]),
        link=link_info["short_url"],
    )


def build_message(checkout: dict, action: str, link_info: dict) -> str:
    """
    Ask Gemini to create a short personalized recovery message.

    Falls back to deterministic templates if Gemini fails.
    """

    name = checkout["customer_name"].split()[0]
    value = int(checkout["cart_value_inr"])
    language = checkout.get("language_pref", "en")
    reason = checkout.get("failure_reason", "payment failure")

    prompt = f"""
You are a payment recovery messaging agent.

Create a short, friendly customer payment recovery message.

Customer name: {name}
Cart value: ₹{value}
Language preference: {language}
Payment problem: {reason}
Recovery action: {action}
Payment link: {link_info["short_url"]}

Rules:
- Keep it under 45 words.
- Be polite and helpful.
- Do not blame the customer.
- Do not claim the payment definitely failed because of a specific cause
  unless that cause is provided.
- Include the payment link exactly as provided.
- Do not invent discounts.
- Do not invent deadlines.
- If language preference is "hi-en", use natural Hinglish.
- Return ONLY the message text.
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        message = response.text.strip()

        if not message:
            raise ValueError("Gemini returned an empty message")

        return message

    except Exception:
        return _fallback_message(
            checkout,
            action,
            link_info
        )


def send(checkout: dict, action: str) -> dict:
    """
    Sends the recovery message.

    Never raises -- send failures are returned to the orchestrator
    so they can be logged as graceful failures.
    """

    link_info = create_recovery_link(checkout)

    message = build_message(
        checkout,
        action,
        link_info
    )

    try:

        result = _mock_send_whatsapp(
            checkout["phone"],
            message
        )

        return {
            "outcome": "sent",
            "message": message,
            "detail": result,
            "payment_link_id": link_info["id"],
            "payment_link_live": link_info["live"],
        }

    except SendError as e:

        return {
            "outcome": "failed_gracefully",
            "message": message,
            "detail": str(e),
            "payment_link_id": link_info["id"],
            "payment_link_live": link_info["live"],
        }