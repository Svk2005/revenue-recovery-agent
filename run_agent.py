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
    print(f"Total checkouts processed : {stats['total']}")
    print(f"Total cart value in batch : Rs {stats['total_cart_value_inr']:.2f}")
    print(f"Messages sent             : {stats['sent']}")
    print(f"Skipped (24h contact cap) : {stats['skipped_contact_cap']}")
    print(f"Routed to human review    : {stats['human_review']}")
    print(f"Send failures (handled)   : {stats['send_failed_gracefully']}")
    print(f"Estimated value recovered : Rs {stats['recovered_value_inr']:.2f}")
    if stats["total_cart_value_inr"] > 0:
        pct = 100 * stats["recovered_value_inr"] / stats["total_cart_value_inr"]
        print(f"Recovery rate (est.)      : {pct:.1f}%")
    print(f"\nFull audit trail written to: {args.out_csv} and {args.out_json}")


if __name__ == "__main__":
    main()
