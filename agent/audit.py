"""
Audit trail. Every decision the agent makes gets one row here:
input -> diagnosis -> policy decision -> action taken -> outcome.

This is the "every money action explainable, bounded and gated" +
"show the audit trail" requirement from the brief, made non-optional
by writing to this log inline in the orchestrator (not reconstructed
after the fact).
"""
import csv
import json

FIELDS = [
    "checkout_id", "customer_name", "cart_value_inr", "failure_reason",
    "recoverability_score", "diagnosis_explanation",
    "policy_action", "discount_pct", "policy_reasoning",
    "send_outcome", "message_sent", "recovered_value_inr",
]


class AuditTrail:
    def __init__(self):
        self.rows = []

    def log(self, row: dict):
        self.rows.append(row)

    def to_csv(self, path: str):
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for r in self.rows:
                writer.writerow({k: r.get(k, "") for k in FIELDS})

    def to_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.rows, f, indent=2)
