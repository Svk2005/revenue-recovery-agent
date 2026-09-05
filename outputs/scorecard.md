# Recovery Batch Scorecard

- **Checkouts processed:** 40
- **Total cart value in batch:** Rs 176,255.53
- **MEASURED value recovered (confirmed payments only):** Rs 75,249.99 (42.7% of batch)
- Expected value recovered (formula estimate, for comparison): Rs 75,965.81
- Confirmed payments: 11  ·  Pending confirmation: 11

## Outcomes
- sent: 22
- skipped: 8
- routed_to_human: 6
- failed_gracefully: 4

## Failure reasons diagnosed (real Razorpay error taxonomy)
- upi_app_technical_error: 9
- invalid_vpa: 5
- insufficient_funds: 4
- otp_expired: 4
- issuer_technical_error: 3
- incorrect_otp: 3
- bank_technical_error: 3
- gateway_technical_error: 2
- card_declined: 2
- payment_session_expired: 2
- payment_collect_request_expired: 1
- payment_declined: 1
- transaction_daily_limit_exceeded: 1

## Sample: one gracefully handled failure
- `CO-402278-1001` (Pooja Singh): agent tried to send but caught an invalid contact and logged it instead of crashing the batch.