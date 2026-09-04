# Revenue Recovery Agent — Razorpay Buildathon (Track 03: AI Revenue Recovery)

**One-liner:** An agent that looks at a batch of abandoned UPI/card checkouts,
diagnoses *why* each one actually failed, decides a bounded and cost-aware
recovery action, executes it, and proves it worked with a full audit trail —
including one failure it handled gracefully instead of crashing.

## Why this isn't just "detect abandonment → send reminder"

Most abandoned-checkout bots treat every failure the same. This agent
doesn't:

1. **Diagnosis built on Razorpay's real error taxonomy, not invented
   categories.** Every `failure_reason` value (`bank_technical_error`,
   `insufficient_funds`, `invalid_vpa`, `payment_cancelled`, etc.) is a
   real, documented Razorpay error `reason`, paired with the real
   `source` (customer/bank/gateway) and `step` fields their API actually
   returns. See [Razorpay's error reasons docs](https://razorpay.com/docs/payment-gateway/rainy-day/errors/error-reasons/).
   The right recovery action is different for each — instant retry vs.
   corrected link vs. wait-and-retry vs. don't bother.
2. **Real Payment Links, not fake URLs.** If Razorpay test-mode API keys
   are configured, `agent/razorpay_client.py` calls Razorpay's real
   [Payment Links API](https://razorpay.com/docs/payments/payment-links/)
   and gets back a genuine `plink_...` id and a clickable, payable
   test-mode checkout link — not a string we made up. Falls back to a
   clearly labelled mock link if no credentials are configured, so the
   pipeline never breaks.
3. **Cost-aware policy layer** — never spends more (discount + messaging cost)
   recovering a sale than the sale is worth. Explicit, auditable rules, not a
   black box.
4. **Confidence gate** — low-confidence cases are routed to human review
   instead of the agent guessing.
5. **Contact-frequency cap** — never messages the same customer more than
   once in 24h.
6. **Hinglish-aware messaging** — customers with a Hinglish preference get a
   natural Hinglish nudge, not a stiff translated one.
7. **A real, logged, gracefully handled failure** — ~15% of the synthetic
   batch has an invalid phone number on purpose, and the agent catches that
   send failure, logs it, and moves on instead of crashing.

## Connecting real Razorpay test-mode API keys (optional but recommended)

1. Get free test-mode keys: dashboard.razorpay.com → **Settings → API Keys
   → Generate Test Key** (personal PAN is fine if you're not a registered
   business — the signup form explicitly allows this).
2. Copy `.env.example` to `.env` in the project root:
   ```bash
   cp .env.example .env
   ```
3. Fill in your `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `.env`.
   This file is git-ignored — it never gets committed.
4. Run the backend as normal. The dashboard's "Live Razorpay links
   created" stat will show a non-zero count, and each audit row's
   payment link will be marked `(live Razorpay API)` instead of `(mock)`.

Without keys configured, everything still runs — it just falls back to
mock links, clearly labelled as such in the audit trail.

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

backend/main.py         → FastAPI wrapper exposing the same pipeline as
                           POST /api/run and GET /api/last
frontend/               → React + Vite + TypeScript + Tailwind dashboard
                           (ledger-style UI, live against the backend)
```

## Run it

### Option A — Web dashboard (recommended for demo)

Two terminals, run from the project root.

**Terminal 1 — backend (FastAPI):**
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — frontend (React + Vite):**
```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`). Click **Run new
batch** to generate a fresh synthetic batch and watch the agent process it
live — recovered-value figure, outcome breakdown, failure-reason breakdown,
and a filterable, expandable audit trail table.

The frontend dev server proxies `/api/*` to the backend on port 8000
(configured in `frontend/vite.config.ts`), so both need to be running.

### Option B — Command line only

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
  mirror Razorpay's real error taxonomy (real `reason`/`source`/`step`
  values) rather than pull real merchant data.
- **Payment Links are real** when Razorpay test-mode API keys are
  configured (see above) — a genuine test-mode Payment Link is created
  via Razorpay's actual API, with a real `plink_...` id. Falls back to a
  clearly labelled mock link otherwise.
- WhatsApp/SMS sending is still mocked in `agent/messenger.py` — the send
  function is isolated so it can be swapped for a real WhatsApp Business
  API integration without touching diagnosis/policy logic.
- Message text uses templates; swapping in an LLM call (e.g. Claude) for
  more natural, context-aware copy is a natural next step and the codebase
  is structured so that's a one-file change (`agent/messenger.py`).

## Next steps (if extended past the hackathon)

- Real WhatsApp Business API integration
- Replace template messages with an LLM call for more natural copy
- A/B test discount thresholds against actual recovery outcomes
