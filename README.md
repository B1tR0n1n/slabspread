# SlabSpread

Market intelligence for vaulted graded trading cards. Three lanes — Trade, Publish, Sell — one codebase. The full spec is [`docs/PLAN.md`](docs/PLAN.md); read §0 (ground rules) before anything else.

## Status
| Phase | State |
|---|---|
| 0 — verification spike | **Done.** Primary sources fetched and quoted 2026-09-26; Q1–Q3, Q7–Q9 resolved, Q4–Q6 need owner action ([`docs/phase0-findings.md`](docs/phase0-findings.md)). |
| 1 — data model + card identity | **Built.** Exit test runs on a schema-faithful corpus; re-runs on real captures once a platform host is reachable. |
| 2 — ingestion workers | **Built** for the approved on-chain paths (Polygon events, Solana USDC flows) with replay, cursors, raw capture, `/health/ingest`. 48-hour soak pending RPC access. Gated sources refuse to run until their license question closes. |
| 3 — engines | **Built.** Spread, pack EV, lag detector, backtest — pure functions with hand-computed tests; formulas in [`docs/methodology.md`](docs/methodology.md). |
| 4 — private dashboard + ledger | **Built.** Owner auth (local or Supabase), ranked opportunities with full calculations, card detail + chart, lag alerts, pack edges, email/log alerts, trade ledger with realized P&L, CSV export and calibration. |
| 5 — public site | **Built.** `python -m sitegen.build` → House Edge Index, Valuation Gap, Methodology, sitemap; disclosures, 18+ notice, not-financial-advice footer. |
| 6 — paid tier | **Built, gated.** Stripe subscriptions, per-user thresholds/niches, capped + staggered fan-out. `/subscribe` returns 503 until [`docs/launch-checklist.md`](docs/launch-checklist.md) is satisfied. |

## Non-negotiables (short form)
- Licensed or public data only. No scraping where terms forbid it; no login bypass; no eBay sold-data.
- No automated buying, bidding, or account automation, ever. A human clicks buy.
- Public pages show derived analytics, not licensed raw feeds. See [`docs/data-licenses.md`](docs/data-licenses.md).
- Disclosures on every affiliate page; 18+ on pack content; "not financial advice" sitewide.
- Secrets in env vars only; `pre-commit install` enables the secret scan.

## Run it
```sh
uv venv && uv pip install -e ".[dev,postgres]"
cp .env.example .env                      # SQLite by default
pytest                                    # hermetic; fixtures only
alembic upgrade head
python -m ingest.replay                   # load fixtures/real + fixtures/corpus
python -m ingest.scheduler                # workers on their intervals
scripts/soak.sh start | status | stop      # scheduler as a soak: own DB, PID file, explicit env
python -m app.auth 'a password'          # hash for SLABSPREAD_OWNER_PASSWORD_HASH
uvicorn app.main:app --reload             # http://127.0.0.1:8000  (dashboard; /login)
python -m sitegen.build                   # public site → public/
```

## Layout
```
app/        FastAPI + Jinja2/HTMX: dashboard, cards, lag, packs, alerts, ledger, admin/matches, health/ingest,
            auth.py (owner), services.py (DB → engines), alerts.py, ledger.py, paid.py (Stripe, gated)
engines/    pure functions: identity, spread, pack_ev, lag, backtest — every result carries its calculation
ingest/     workers: base.py (rate limit, backoff, raw store, run ledger), chains/ (evm, solana RPC + decoders),
            onchain_*.py (approved), gated.py (refuse until licensed), scheduler.py, replay.py
models/     SQLAlchemy 2 — cards, slabs, sources, listings, sales, valuations, packs, pack_odds, match_candidates
migrations/ Alembic (batch mode; SQLite for tests, Postgres in production)
sitegen/    static public site generator (aggregate.py is pure)
fixtures/   real/ captured responses · corpus/ 50-slab identity corpus · rpc/ RPC shapes (both synthetic)
docs/       PLAN, phase0-findings, data-licenses, decisions, methodology, owner-runbook (your 7 steps),
            launch-checklist, terms/privacy drafts, research/
```

## Identity in one paragraph
A listing, a token, and a price row are "the same card" when (1) they share a grader + cert number — exact; else (2) their canonical key `game|set|number|variant|grader|grade` matches after normalization (set aliases, game-word stripping, variant vocabulary); else (3) title similarity minus hard-field penalties produces a *candidate* with a confidence and an explanation, which a human accepts or rejects at `/admin/matches`. Nothing fuzzy is ever trusted automatically.
