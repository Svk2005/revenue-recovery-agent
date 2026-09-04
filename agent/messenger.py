"""
Messenger layer.

Generates the actual outreach message (English or Hinglish depending on
customer preference) and "sends" it via a mocked WhatsApp/SMS send call
that stands in for Razorpay Magic / a WhatsApp Business API integration.

This is also where we deliberately let ONE realistic failure mode happen
(invalid phone number) and prove the agent catches it gracefully instead
of crashing -- per the track's explicit requirement to "show one failure
handled gracefully."
"""

TEMPLATES = {
    "send_instant_retry_link": {
        "en": "Hi {name}, your payment of ₹{value} didn't go through due to a temporary issue -- not your fault! Complete it here: {link}",
        "hi-en": "Hi {name}, aapka ₹{value} ka payment ek temporary issue ki wajah se fail ho gaya -- koi baat nahi! Yahan se complete kar lijiye: {link}",
    },
    "schedule_delayed_reminder": {
        "en": "Hi {name}, we've saved your cart (₹{value}). We'll remind you again in a bit once things settle -- or you can pay now: {link}",
        "hi-en": "Hi {name}, aapka cart (₹{value}) safe rakha hai. Thodi der baad phir yaad dila denge -- ya abhi bhi pay kar sakte hain: {link}",
    },
    "send_corrected_payment_link": {
        "en": "Hi {name}, looks like there was a small typo in your UPI ID last time. Here's a fresh, pre-filled link so it works this time: {link}",
        "hi-en": "Hi {name}, lagta hai UPI ID mein chhoti si typo ho gayi thi. Yeh raha ek naya, pre-filled link jo aasani se kaam karega: {link}",
    },
}


class SendError(Exception):
    pass


def _mock_send_whatsapp(phone: str, message: str):
    """Stand-in for a real WhatsApp Business / Razorpay Magic send call."""
    if phone == "INVALID_NUMBER" or not phone.startswith("+91-"):
        raise SendError(f"Invalid destination number: {phone!r}")
    # In a real integration this would call the WhatsApp/SMS API.
    return {"status": "sent", "channel": "whatsapp", "to": phone}


def build_message(checkout: dict, action: str) -> str:
    lang = checkout.get("language_pref", "en")
    template = TEMPLATES.get(action, TEMPLATES["send_instant_retry_link"])[lang]
    fake_link = f"https://rzp.io/recover/{checkout['checkout_id']}"
    return template.format(name=checkout["customer_name"].split()[0],
                            value=int(checkout["cart_value_inr"]),
                            link=fake_link)


def send(checkout: dict, action: str) -> dict:
    """
    Returns a result dict. Never raises -- catches send failures and
    reports them so the orchestrator can log a graceful failure instead
    of crashing the batch.
    """
    message = build_message(checkout, action)
    try:
        result = _mock_send_whatsapp(checkout["phone"], message)
        return {"outcome": "sent", "message": message, "detail": result}
    except SendError as e:
        return {"outcome": "failed_gracefully", "message": message, "detail": str(e)}
