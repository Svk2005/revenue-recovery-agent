"""
Policy layer -- the final safety and financial authority.

Gemini can recommend an action, but it cannot override these rules.

Rules:
1. Never message someone more than once in 24h.
2. Low-confidence cases go to human review.
3. Wait windows are respected.
4. Discounts are cost-checked.
5. AI actions are restricted to approved actions only.
"""

CONFIDENCE_GATE = 0.45
WHATSAPP_COST_INR = 0.35
MIN_CART_VALUE_FOR_DISCOUNT = 500
MAX_DISCOUNT_PCT = 10
CONTACT_CAP_24H = 1

ALLOWED_AI_ACTIONS = {
    "send_instant_retry_link",
    "send_corrected_payment_link",
    "schedule_delayed_reminder",
    "human_review",
    "skip",
}


def decide_action(checkout: dict, diagnosis: dict) -> dict:

    reason = diagnosis["failure_reason"]
    score = diagnosis["recoverability_score"]
    cart_value = checkout["cart_value_inr"]
    prior_contacts = checkout["prior_contacts_24h"]

    ai_action = diagnosis.get("ai_action")
    ai_confidence = diagnosis.get("ai_confidence", 0.0)

    # ---------------------------------------------------------
    # Gate 1: Contact frequency cap
    # ---------------------------------------------------------

    if prior_contacts >= CONTACT_CAP_24H:
        return _decision(
            "skip",
            0.0,
            score,
            "Already contacted within 24h -- policy caps outreach at 1/day."
        )

    # ---------------------------------------------------------
    # Gate 2: AI confidence gate
    # ---------------------------------------------------------

    if ai_confidence > 0 and ai_confidence < CONFIDENCE_GATE:
        return _decision(
            "human_review",
            0.0,
            score,
            f"AI confidence {ai_confidence:.2f} is below the "
            f"{CONFIDENCE_GATE} confidence gate -- routed to human review."
        )

    # ---------------------------------------------------------
    # Gate 3: Existing recoverability confidence gate
    # ---------------------------------------------------------

    if score < CONFIDENCE_GATE:
        return _decision(
            "human_review",
            0.0,
            score,
            f"Recoverability score {score:.2f} is below the "
            f"{CONFIDENCE_GATE} confidence gate -- routed to a human."
        )

    # ---------------------------------------------------------
    # Decide safe action
    # ---------------------------------------------------------

    if ai_action in ALLOWED_AI_ACTIONS:

        # AI says what to do, but policy still validates it.
        action = ai_action

    elif reason == "invalid_vpa":

        action = "send_corrected_payment_link"

    elif diagnosis["recommended_wait_hours"] > 0:

        action = "schedule_delayed_reminder"

    else:

        action = "send_instant_retry_link"

    # ---------------------------------------------------------
    # Safety rule:
    # invalid VPA must use corrected payment link
    # ---------------------------------------------------------

    if reason == "invalid_vpa":
        action = "send_corrected_payment_link"

    # ---------------------------------------------------------
    # Safety rule:
    # delayed failures must respect wait window
    # ---------------------------------------------------------

    if diagnosis["recommended_wait_hours"] > 0:
        action = "schedule_delayed_reminder"

    # ---------------------------------------------------------
    # Cost-aware discount decision
    # ---------------------------------------------------------

    discount_pct = 0

    if cart_value >= MIN_CART_VALUE_FOR_DISCOUNT and score < 0.75:

        discount_pct = min(
            MAX_DISCOUNT_PCT,
            round((1 - score) * 15)
        )

        discount_cost = cart_value * discount_pct / 100

        # Never spend more than 50% of cart value
        # on discount + messaging.
        if discount_cost + WHATSAPP_COST_INR > cart_value * 0.5:
            discount_pct = 0

    # ---------------------------------------------------------
    # Final reasoning
    # ---------------------------------------------------------

    reasoning = (
        f"{diagnosis['explanation']} "
        f"Recoverability={score:.2f}. "
        f"AI recommendation='{ai_action}'. "
        f"Policy-approved action='{action}'."
    )

    if discount_pct:
        reasoning += (
            f" {discount_pct}% incentive approved after cost check."
        )
    else:
        reasoning += " No incentive required."

    return _decision(
        action,
        discount_pct,
        score,
        reasoning
    )


def _decision(action, discount_pct, confidence, reasoning):

    return {
        "action": action,
        "discount_pct": discount_pct,
        "confidence": confidence,
        "reasoning": reasoning,
    }