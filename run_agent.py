"""
Entry point.

Usage:
    python data/generate_data.py --n 40 --out data/checkouts.json
    python run_agent.py --in data/checkouts.json
"""
import argparse
import json

from agent.orchestrator import run_batch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default="data/checkouts.json")
    ap.add_argument("--out-csv", default="outputs/audit_trail.csv")
    ap.add_argument("--out-json", default="outputs/audit_trail.json")
    args = ap.parse_args()

    with open(args.infile) as f:
        checkouts = json.load(f)

    trail, stats = run_batch(checkouts)
    trail.to_csv(args.out_csv)
    trail.to_json(args.out_json)

    print("\n=== Revenue Recovery Agent -- Batch Summary ===")
    print(f"Total checkouts processed   : {stats['total']}")
    print(f"Total cart value in batch   : Rs {stats['total_cart_value_inr']:.2f}")
    print(f"Messages sent               : {stats['sent']}")
    print(f"Skipped (24h contact cap)   : {stats['skipped_contact_cap']}")
    print(f"Routed to human review      : {stats['human_review']}")
    print(f"Send failures (handled)     : {stats['send_failed_gracefully']}")
    print(f"Confirmed payments          : {stats['confirmed_payments']} (simulated)")
    print(f"Pending confirmation        : {stats['pending_confirmation']}")
    print(f"Expected value recovered    : Rs {stats['expected_recovered_value_inr']:.2f}  (formula estimate)")
    print(f"MEASURED value recovered    : Rs {stats['measured_recovered_value_inr']:.2f}  (confirmed payments only)")
    print(f"Batch discount cap          : Rs {stats['batch_discount_cap_inr']:.2f}")
    print(f"Total discount spent        : Rs {stats['total_discount_spent_inr']:.2f}")
    print(f"Discounts blocked by cap    : {stats['discounts_blocked_by_batch_cap']}")
    if stats["total_cart_value_inr"] > 0:
        pct = 100 * stats["measured_recovered_value_inr"] / stats["total_cart_value_inr"]
        print(f"Measured recovery rate      : {pct:.1f}%")
    print(f"\nFull audit trail written to: {args.out_csv} and {args.out_json}")


if __name__ == "__main__":
    main()
