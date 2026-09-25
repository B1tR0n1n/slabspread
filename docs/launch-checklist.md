# Paid-tier launch checklist (plan §8)

`app/paid.py::launch_gate` refuses signups until every item below is true. The flags are
deliberately separate from the code so that flipping one is a recorded decision.

| # | Condition | Where | Evidence needed |
|---|---|---|---|
| 1 | Engine predictions hold up on real trades | ledger: ≥ `SLABSPREAD_LAUNCH_MIN_CALIBRATED_TRADES` closed trades with a prediction; review the calibration panel's hit rate and mean error | `/ledger` |
| 2 | Every data license permits a commercial derived-data product | `docs/data-licenses.md` — no `provisional` row feeds a subscriber-facing number | set `SLABSPREAD_LAUNCH_LICENSES_CONFIRMED=true` |
| 3 | Terms of service and privacy policy professionally reviewed | replace `docs/terms.md` / `docs/privacy.md` | set `SLABSPREAD_LAUNCH_TERMS_REVIEWED=true` |
| 4 | Stripe configured | product + recurring price, webhook endpoint `/stripe/webhook` with events `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed` | `SLABSPREAD_STRIPE_*` |
| 5 | Fan-out limits chosen | `SLABSPREAD_FANOUT_PER_LISTING_CAP`, `SLABSPREAD_FANOUT_STAGGER_SECONDS` | defaults 5 / 90 s |
| 6 | Switch on | `SLABSPREAD_PAID_TIER_ENABLED=true` | — |
