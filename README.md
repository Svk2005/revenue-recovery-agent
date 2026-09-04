# Revenue Recovery Agent — Razorpay Buildathon (Track 03: AI Revenue Recovery)

**One-liner:** An agent that looks at a batch of abandoned UPI/card checkouts,
diagnoses *why* each one actually failed, decides a bounded and cost-aware
recovery action, executes it, and proves it worked with a full audit trail —
including one failure it handled gracefully instead of crashing.

## Why this isn't just "detect abandonment → send reminder"

Most abandoned-checkout bots treat every failure the same. This agent
doesn't:

1. **Failure-specific diagnosis** — `bank_server_timeout`, `insufficient_balance`,
   `wrong_vpa_entered`, `daily_limit_exceeded`, etc. are each diagnosed
   differently, because the right recovery action is different for each
   (instant retry vs. corrected link vs. wait-and-retry vs. don't bother).
2. **Cost-aware policy layer** — never spends more (discount + messaging cost)
   recovering a sale than the sale is worth. Explicit, auditable rules, not a
   black box.
3. **Confidence gate** — low-confidence cases are routed to human review
   instead of the agent guessing.
4. **Contact-frequency cap** — never messages the same customer more than
   once in 24h.
5. **Hinglish-aware messaging** — customers with a Hinglish preference get a
   natural Hinglish nudge, not a stiff translated one.
6. **A real, logged, gracefully handled failure** — ~15% of the synthetic
   batch has an invalid phone number on purpose, and the agent catches that
   send failure, logs it, and moves on instead of crashing.

## Architecture

```
data/generate_data.py   → synthetic batch of abandoned checkouts
agent/diagnose.py       → why did this payment actually fail?
agent/policy.py         → bounded, gated, cost-aware decision logic
agent/messenger.py      → builds + "sends" the recovery message (Hinglish/English)
agent/audit.py          → every decision logged, nothing silently dropped
agent/orchestrator.py   → ties it all together, one audit row per checkout
run_agent.py            → CLI entrypoint
report.py               → generates the scorecard below
```

## Run it

```bash
python data/generate_data.py --n 40 --out data/checkouts.json
python run_agent.py --in data/checkouts.json
python report.py
```

Outputs land in `outputs/`:
- `audit_trail.csv` / `audit_trail.json` — full explainable trail, one row per checkout
- `scorecard.md` — batch-level summary

## Sample result (40-checkout synthetic batch)

- **Checkouts processed:** 40
- **Total cart value in batch:** ₹125,530.87
- **Estimated value recovered:** ₹28,746.69 (~22.9% of batch)
- **Outcomes:** 21 sent · 8 failed gracefully (handled, logged) · 7 skipped (contact cap) · 4 routed to human review

See `outputs/scorecard.md` for the full breakdown after running.

## How this maps to Razorpay's "the bar"

> "Don't just identify the problem. Show measured money recovered across a
> batch, with compliant escalation, stopping rules, and an audit trail."

- **Measured money recovered** → `recovered_value_inr` per row + batch total in the scorecard
- **Stopping rules** → 24h contact cap, confidence gate, 50%-of-cart-value discount ceiling
- **Compliant escalation** → low-confidence cases routed to human review, not auto-actioned
- **Audit trail** → `outputs/audit_trail.csv`, one row per checkout, reasoning included
- **One failure handled gracefully** → invalid-contact send failures are caught and logged, not crashed on

## What's mocked vs. real

- Payment/checkout data is synthetic (`data/generate_data.py`) — built to
  mirror realistic UPI failure modes rather than pull real merchant data.
- WhatsApp/SMS sending is mocked in `agent/messenger.py` — the send function
  is isolated so it can be swapped for a real WhatsApp Business API or
  Razorpay Magic integration without touching diagnosis/policy logic.
- Message text uses templates; swapping in an LLM call (e.g. Claude) for
  more natural, context-aware copy is a natural next step and the codebase
  is structured so that's a one-file change (`agent/messenger.py`).

## Next steps (if extended past the hackathon)

- Real payment-link generation via Razorpay's test-mode Payment Links API
- Real WhatsApp Business API integration
- Replace template messages with an LLM call for more natural copy
- A/B test discount thresholds against actual recovery outcomes
