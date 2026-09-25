# SlabSpread

Market intelligence for vaulted graded trading cards. Three lanes — Trade, Publish, Sell — one codebase. The full spec is [`docs/PLAN.md`](docs/PLAN.md); read §0 (ground rules) before anything else.

## Status
**Phase 0 — verification spike, first pass done; reopened for primary-source verification (Q1–Q9).** No product code yet. See [`docs/phase0-findings.md`](docs/phase0-findings.md).

## Non-negotiables (short form)
- Licensed or public data only. No scraping where terms forbid it; no login bypass; no eBay sold-data.
- No automated buying, bidding, or account automation, ever. A human clicks buy.
- Public pages show derived analytics, not licensed raw feeds. See [`docs/data-licenses.md`](docs/data-licenses.md).
- Disclosures on every affiliate page; 18+ on pack content; "not financial advice" sitewide.
- Secrets in env vars only; `pre-commit install` enables the secret scan.

## Docs
- `docs/PLAN.md` — the spec
- `docs/phase0-findings.md` — evidence per data source
- `docs/data-licenses.md` — what each source lets us do
- `docs/decisions.md` — why things are the way they are
