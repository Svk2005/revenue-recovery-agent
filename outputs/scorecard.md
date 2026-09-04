# Recovery Batch Scorecard

- **Checkouts processed:** 40
- **Total cart value in batch:** Rs 125,530.87
- **Estimated value recovered:** Rs 28,746.69 (22.9% of batch)

## Outcomes
- sent: 21
- failed_gracefully: 8
- skipped: 7
- routed_to_human: 4

## Failure reasons diagnosed
- wrong_vpa_entered: 9
- daily_limit_exceeded: 7
- bank_server_timeout: 6
- upi_app_crash: 5
- user_cancelled_mid_flow: 4
- network_drop: 4
- otp_not_received: 3
- insufficient_balance: 2

## Sample: one gracefully handled failure
- `CO-1009` (Rajesh Singh): agent tried to send but caught an invalid contact and logged it instead of crashing the batch.