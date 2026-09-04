"""
Generates a synthetic batch of abandoned UPI/card checkouts for the
Razorpay Revenue Recovery Agent to process.

Every failure_reason value here is a REAL, documented Razorpay error
`reason` (see razorpay.com/docs/payment-gateway/rainy-day/errors/) --
not an invented category. source/step are the matching real fields
Razorpay's API returns alongside each reason. This lets the rest of
the pipeline (agent/diagnose.py) work against Razorpay's authentic
error taxonomy even when running on synthetic checkout data.

Run: python data/generate_data.py --n 40 --out data/checkouts.json
"""
import argparse
import json
import random
import time
from datetime import datetime, timedelta

FIRST_NAMES = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Ananya", "Karan",
               "Ishita", "Rahul", "Meera", "Arjun", "Divya", "Nikhil", "Pooja",
               "Sanjay", "Kavya", "Amit", "Neha", "Rajesh", "Simran"]
LAST_NAMES = ["Sharma", "Verma", "Iyer", "Reddy", "Nair", "Gupta", "Singh",
              "Patel", "Kulkarni", "Das", "Mehta", "Rao", "Joshi", "Kapoor"]

# (reason, source, step) -- all three are real values from Razorpay's
# documented error schema, matched to the profiles in agent/diagnose.py.
RAZORPAY_FAILURE_REASONS = [
    ("bank_technical_error", "bank", "payment_authorization"),
    ("gateway_technical_error", "gateway", "payment_authorization"),
    ("issuer_technical_error", "bank", "payment_authorization"),
    ("upi_app_technical_error", "gateway", "payment_authorization"),
    ("payment_session_expired", "customer", "payment_initiation"),
    ("payment_collect_request_expired", "customer", "payment_authentication"),
    ("incorrect_otp", "customer", "payment_authentication"),
    ("otp_expired", "customer", "payment_authentication"),
    ("invalid_vpa", "customer", "payment_initiation"),
    ("insufficient_funds", "customer", "payment_authorization"),
    ("transaction_daily_limit_exceeded", "bank", "payment_authorization"),
    ("card_declined", "bank", "payment_authorization"),
    ("payment_cancelled", "customer", "payment_authentication"),
    ("payment_declined", "bank", "payment_authorization"),
]

LANGUAGE_PREF = ["en", "hi-en"]  # hi-en = Hinglish


def new_run_id() -> str:
    """
    A short, unique-per-run id (based on current time) used to prefix
    checkout_id values. Without this, repeated runs would generate the
    same CO-1000, CO-1001... ids every time, which collide with
    Razorpay's Payment Links `reference_id` field on a second attempt
    (each reference_id must be unique) and silently fall back to a
    mock link. This keeps every run's checkouts genuinely unique.
    """
    return format(int(time.time() * 1000) % 1_000_000, "06d")


def random_time_recent(max_hours_ago=72):
    return (datetime.now() - timedelta(hours=random.uniform(0.5, max_hours_ago))).isoformat()


def make_checkout(idx, run_id: str = ""):
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    cart_value = round(random.choice([149, 299, 499, 899, 1299, 2499, 4999, 9999, 14999]) *
                        random.uniform(0.9, 1.1), 2)
    reason, source, step = random.choice(RAZORPAY_FAILURE_REASONS)
    lang = random.choice(LANGUAGE_PREF)

    # ~15% of records have a broken contact -> forces the agent to hit
    # a real failure it must handle gracefully instead of crashing.
    has_valid_contact = random.random() > 0.15
    phone = f"+91-{random.randint(6000000000, 9999999999)}" if has_valid_contact else "INVALID_NUMBER"

    # how many times we've already tried this customer in the last 24h
    # (feeds the "don't over-contact" policy rule)
    prior_contacts_24h = random.choices([0, 0, 0, 1, 2], weights=[60, 15, 10, 10, 5])[0]

    checkout_id = f"CO-{run_id}-{1000 + idx}" if run_id else f"CO-{1000 + idx}"

    return {
        "checkout_id": checkout_id,
        "customer_name": name,
        "phone": phone,
        "cart_value_inr": cart_value,
        "failure_reason": reason,
        "source": source,
        "step": step,
        "language_pref": lang,
        "abandoned_at": random_time_recent(),
        "prior_contacts_24h": prior_contacts_24h,
        "payment_method": random.choice(["UPI", "UPI", "UPI", "Card"]),  # skew UPI, matches track focus
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--out", type=str, default="data/checkouts.json")
    ap.add_argument("--seed", type=int, default=None,
                     help="Optional: fix the random seed for reproducible output.")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    run_id = new_run_id()
    records = [make_checkout(i, run_id=run_id) for i in range(args.n)]
    with open(args.out, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} synthetic checkouts to {args.out} (run_id={run_id})")


if __name__ == "__main__":
    main()
