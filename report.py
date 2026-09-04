"""
Generates a short markdown scorecard from outputs/audit_trail.json --
useful to paste straight into the hackathon submission / demo.

Usage: python report.py
"""
import json
from collections import Counter

with open("outputs/audit_trail.json") as f:
    rows = json.load(f)

total = len(rows)
total_value = sum(float(r["cart_value_inr"]) for r in rows)
recovered = sum(float(r["recovered_value_inr"] or 0) for r in rows)
outcomes = Counter(r["send_outcome"] for r in rows)
reasons = Counter(r["failure_reason"] for r in rows)

lines = []
lines.append("# Recovery Batch Scorecard\n")
lines.append(f"- **Checkouts processed:** {total}")
lines.append(f"- **Total cart value in batch:** Rs {total_value:,.2f}")
lines.append(f"- **Estimated value recovered:** Rs {recovered:,.2f} "
             f"({100*recovered/total_value:.1f}% of batch)")
lines.append("")
lines.append("## Outcomes")
for outcome, count in outcomes.most_common():
    lines.append(f"- {outcome}: {count}")
lines.append("")
lines.append("## Failure reasons diagnosed")
for reason, count in reasons.most_common():
    lines.append(f"- {reason}: {count}")
lines.append("")
lines.append("## Sample: one gracefully handled failure")
for r in rows:
    if r["send_outcome"] == "failed_gracefully":
        lines.append(f"- `{r['checkout_id']}` ({r['customer_name']}): "
                      f"agent tried to send but caught an invalid contact and "
                      f"logged it instead of crashing the batch.")
        break

report = "\n".join(lines)
with open("outputs/scorecard.md", "w") as f:
    f.write(report)
print(report)
