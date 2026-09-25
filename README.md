# SlabSpread

Market intelligence for vaulted graded trading cards. Three lanes — Trade, Publish, Sell — one codebase. The full spec is [`docs/PLAN.md`](docs/PLAN.md); read §0 (ground rules) before anything else.

## Status
| Phase | State |
|---|---|
| 0 — verification spike | First pass done; **reopened** for primary-source verification (Q1–Q9 in [`docs/phase0-findings.md`](docs/phase0-findings.md)). |
| 1 — data model + card identity | **Built.** Exit test runs on a schema-faithful corpus; re-runs on real captures once a platform host is reachable. |
| 2 — ingestion workers | **Built** for the approved on-chain paths (Polygon events, Solana USDC flows) with replay, cursors, raw capture, `/health/ingest`. 48-hour soak pending RPC access. Gated sources refuse to run until their license question closes. |
| 3+ | Not started. |

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
python -m ingest.scheduler                # workers on their intervals (needs RPC access)
uvicorn app.main:app --reload             # http://127.0.0.1:8000/admin/matches
```

## Layout
```
app/        FastAPI + Jinja2/HTMX. Phase 1: /admin/matches (fuzzy-candidate review)
engines/    pure functions. identity.py: cert → canonical key → fuzzy candidates
ingest/     workers: base.py (rate limit, backoff, raw store, run ledger), chains/ (evm, solana RPC + decoders),
            onchain_*.py (approved), gated.py (refuse until licensed), scheduler.py, replay.py
models/     SQLAlchemy 2 — cards, slabs, sources, listings, sales, valuations, packs, pack_odds, match_candidates
migrations/ Alembic (batch mode; SQLite for tests, Postgres in production)
fixtures/   real/ captured responses · corpus/ labeled 50-slab identity corpus (synthetic)
docs/       PLAN, phase0-findings, data-licenses, decisions, research/
```

## Identity in one paragraph
A listing, a token, and a price row are "the same card" when (1) they share a grader + cert number — exact; else (2) their canonical key `game|set|number|variant|grader|grade` matches after normalization (set aliases, game-word stripping, variant vocabulary); else (3) title similarity minus hard-field penalties produces a *candidate* with a confidence and an explanation, which a human accepts or rejects at `/admin/matches`. Nothing fuzzy is ever trusted automatically.
