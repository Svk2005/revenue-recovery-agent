"""
Tests for the batch-wide discount spend cap in agent/orchestrator.py.

Per-case discount ceilings live in policy.py and are tested in
test_policy.py. This tests the separate, batch-level stopping rule:
even if every individual case's discount is within its own limit,
the orchestrator must refuse to keep handing out discounts once the
whole batch's cumulative discount spend crosses BATCH_DISCOUNT_CAP_PCT
of the batch's total cart value.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.orchestrator import run_batch, BATCH_DISCOUNT_CAP_PCT


def make_batch(n=30, cart_value_inr=5000):
    """
    A batch specifically constructed to try to trigger a lot of
    discounting: recoverability just above the confidence gate (so
    discounts get offered) but below 0.75 (the threshold in policy.py
    below which a discount is considered).
    """
    return [
        {
            "checkout_id": f"CO-TEST-{i}",
            "customer_name": f"Test User {i}",
            "phone": f"+91-90000000{i:02d}",
            "cart_value_inr": cart_value_inr,
            "failure_reason": "transaction_daily_limit_exceeded",  # recoverability 0.50
            "source": "bank",
            "step": "payment_authorization",
            "language_pref": "en",
            "abandoned_at": "2026-01-01T00:00:00",
            "prior_contacts_24h": 0,
            "payment_method": "UPI",
        }
        for i in range(n)
    ]


def test_batch_discount_cap_is_never_exceeded():
    checkouts = make_batch(n=30, cart_value_inr=5000)
    trail, stats = run_batch(checkouts)
    # allow a tiny float-rounding tolerance
    assert stats["total_discount_spent_inr"] <= stats["batch_discount_cap_inr"] + 0.01


def test_batch_discount_cap_blocks_some_discounts_under_heavy_load():
    # With 30 identical high-discount-eligible cases, the batch cap
    # (4% of total cart value) should be tight enough that at least
    # some individual discounts get blocked once the cap is reached.
    checkouts = make_batch(n=30, cart_value_inr=5000)
    trail, stats = run_batch(checkouts)
    assert stats["discounts_blocked_by_batch_cap"] >= 1


def test_batch_cap_scales_with_batch_value():
    checkouts = make_batch(n=10, cart_value_inr=1000)
    trail, stats = run_batch(checkouts)
    expected_cap = round(stats["total_cart_value_inr"] * BATCH_DISCOUNT_CAP_PCT, 2)
    assert stats["batch_discount_cap_inr"] == expected_cap


def test_every_checkout_produces_exactly_one_audit_row():
    checkouts = make_batch(n=15)
    trail, stats = run_batch(checkouts)
    assert len(trail.rows) == len(checkouts)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
