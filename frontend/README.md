
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
a live feed of confirmed-payment notifications, and a filterable,
expandable audit trail table.

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
- **Total cart value in batch:** ₹176,255.53
- **MEASURED value recovered:** ₹75,249.99 (42.7% of batch) — confirmed payments only
- **Expected value recovered (formula estimate, for comparison):** ₹75,965.81
- **Confirmed payments:** 11 · **Pending confirmation:** 11
- **Outcomes:** 22 sent · 4 failed gracefully (handled, logged) · 8 skipped (contact cap) · 6 routed to human review

See `outputs/scorecard.md` for the full breakdown after running.

## How this maps to Razorpay's "the bar"

> "Don't just identify the problem. Show measured money recovered across a
> batch, with compliant escalation, stopping rules, and an audit trail."

- **Measured money recovered** → `measured_recovered_value_inr` is a genuinely
  distinct, simulated-outcome figure (see `agent/confirmation.py`), not the
  same formula echoed twice — it differs from `expected_recovered_value_inr`
  in every real run, exactly like a real business's actual vs. forecast
  recovery would.
- **Stopping rules** → 24h contact cap, confidence gate, per-case 50%-of-cart-value
  discount ceiling, **and** a batch-wide discount spend cap (4% of total batch
  value — see `agent/orchestrator.py`) that blocks further discounting once
  the batch-wide budget is spent, even if every individual case is within
  its own limit. The AI's recommended action is also gated: it's checked
  against an allow-list and can be overridden by a safety rule before it's
  ever executed.
- **Compliant escalation** → low-confidence cases routed to human review, not auto-actioned
- **Audit trail** → `outputs/audit_trail.csv`, one row per checkout, reasoning included
- **One failure handled gracefully** → invalid-contact send failures are caught and logged, not crashed on
- **Automated tests** → `tests/test_policy.py` and `tests/test_orchestrator.py`
  directly assert every stopping rule above actually holds (11 tests, all
  passing) — run with `pytest tests/ -v`.

## What's mocked vs. real

- Payment/checkout data is synthetic (`data/generate_data.py`) — built to
  mirror Razorpay's real error taxonomy (real `reason`/`source`/`step`
  values) rather than pull real merchant data.
- **Payment Links are real** when Razorpay test-mode API keys are
  configured (see above) — a genuine test-mode Payment Link is created
  via Razorpay's actual API, with a real `plink_...` id. Falls back to a
  clearly labelled mock link otherwise.
- **Diagnosis and messaging are LLM-generated (Gemini)** when
  `GEMINI_API_KEY` is configured — with the deterministic Razorpay-taxonomy
  logic and templates as a tested, automatic fallback if the AI call fails,
  times out, or returns something unusable.
- **Payment confirmation is simulated** (`agent/confirmation.py`) — in test
  mode nobody actually clicks through and pays a Payment Link, so a real
  webhook-based confirmation loop would always report zero recovered. This
  is explicitly labelled as a simulation everywhere it surfaces (dashboard,
  audit trail, README) rather than silently presented as real. Swapping in
  a real confirmation is a one-function change (check
  `payment_link.fetch(id)["status"] == "paid"` instead).
- WhatsApp/SMS sending is still mocked in `agent/messenger.py` — the send
  function is isolated so it can be swapped for a real WhatsApp Business
  API integration without touching diagnosis/policy logic.

## Running the tests

```bash
pip install -r backend/requirements.txt
pytest tests/ -v
```
11 tests covering the confidence gate, contact cap, per-case and batch-wide
discount ceilings, and that every checkout produces exactly one audit row.

## Next steps (if extended past the hackathon)

- Real WhatsApp Business API integration
- Real payment confirmation via Razorpay webhooks instead of simulation
- A/B test discount thresholds against actual recovery outcomes
- Structured output / function calling for the Gemini calls instead of
  prompt-and-parse, for stronger output guarantees