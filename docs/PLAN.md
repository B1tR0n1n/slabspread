# SlabSpread — Build Plan

> Working name. A market-intelligence app for vaulted graded trading cards.
> One codebase, three revenue lanes:
> 1. **Trade** — find cards priced below what a vault platform will pay for them (private tool, human executes every trade).
> 2. **Publish** — public "house edge" reports on pack platforms, monetized with disclosed affiliate links and ads.
> 3. **Sell** — later, a paid tier giving others the spread alerts.

This document is the spec for Claude Code. Read it fully before writing code. Follow the phases in order; each phase has an exit test.

---

## 0. Ground rules (non-negotiable — this is what makes it legitimate)

1. **Only licensed or public data.** Use official APIs, paid data licenses, and public blockchain data. Do **not** scrape any site whose terms prohibit it, do not bypass logins, Cloudflare challenges, or rate limits, and do not use third-party scrapers of sites that forbid scraping.
   - eBay **sold** data is off-limits programmatically: the Marketplace Insights API is restricted and closed to new users, and sold listings now sit behind a login. Do not scrape them.
   - eBay **active** listings via the official Browse API are fine.
2. **No automated buying, bidding, or account automation** on any platform. The app finds and ranks opportunities; a human clicks buy. This keeps us inside platform terms and keeps a person accountable for every dollar.
3. **Respect data licenses on redistribution.** Paid price APIs usually forbid republishing their raw numbers. Public pages show *derived* analytics (edges, spreads, percentages, our own on-chain aggregates), not a mirror of a licensed price feed. Verify each license in Phase 0 and record the answer in `docs/data-licenses.md`.
4. **Content compliance.** Every public page with affiliate links carries a clear FTC-style disclosure above the fold. Pack-platform content states 18+, shows the house edge prominently, and never frames pack opening as a way to make money. Add a "not financial advice" footer sitewide.
5. **Secrets** live in environment variables / a secrets manager, never in the repo. Add a pre-commit secret scan.
6. **Records for taxes.** The trade ledger (Phase 4) is a first-class feature, not an afterthought.

---

## 1. Architecture

```
            ┌──────────────── ingestion workers (scheduled) ────────────────┐
            │  onchain_courtyard   onchain_collectorcrypt   ebay_browse      │
            │  price_api (licensed)   psa_cert   platform_odds (published)   │
            └──────────────────────────────┬────────────────────────────────┘
                                           ▼
                                Postgres (Supabase)
            cards · listings · sales · valuations · packs · odds · trades
                                           │
              ┌────────────────────────────┼─────────────────────────────┐
              ▼                            ▼                             ▼
       spread engine               pack EV auditor               lag detector
              │                            │                             │
              ▼                            ▼                             ▼
   private dashboard + alerts     public report pages (SSG)      alerts / reports
   (auth, single user first)      affiliate + disclosure
```

**Stack (default — change only with a reason logged in `docs/decisions.md`):**
- Backend: Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, httpx, Pydantic v2.
- Jobs: APScheduler to start (upgrade to a queue only if needed).
- DB: Supabase Postgres (auth for the private dashboard via Supabase Auth).
- Frontend: server-rendered pages first (Jinja2 + HTMX) — fast to build, SEO-friendly for the public reports. Charts with Chart.js.
- Deploy: Docker Compose; one container for API/web, one for workers.
- Tests: pytest; fixtures from recorded real responses (never live calls in tests).

---

## 2. Phase 0 — Verification spike (do this first, write findings, no product code)

Produce `docs/phase0-findings.md` answering each item with evidence (doc links, sample responses saved under `fixtures/`):

1. **Courtyard (Polygon):** contract address(es), how sales/transfers appear on-chain, what token metadata contains (card name, set, grader, grade, **cert number**?), whether platform "fair market value" and buyback price are exposed anywhere officially. Any public API or terms on data use.
2. **Collector Crypt (Solana):** same questions; how marketplace sales and buybacks appear on-chain; whether Magic Eden or a Solana indexer (e.g. Helius) gives sale history through official APIs.
3. **Phygitals** and any other vault platform: same questions; mark as "later" if no clean data path.
4. **Published pack odds:** where each platform publishes odds and pack contents, in what format, and whether terms allow reading and analyzing them.
5. **Licensed price data:** compare candidates (PriceCharting / SportsCardsPro API, Scrydex, PokemonPriceTracker business tier, others). For each: coverage (Pokémon, sports, graders), graded-price fields, update frequency, cost, commercial-use and redistribution terms.
6. **PSA public cert API:** token process, rate limits, storage/display terms.
7. **eBay Browse API:** application process, rate limits, filters for graded slabs, affiliate (eBay Partner Network) link rules.
8. **Affiliate/referral programs** for each pack platform: existence, payout, content rules.

**Exit test:** every item answered or explicitly marked "no legitimate path — excluded." Scope for Phases 1–5 is adjusted to what survived.

---

## 3. Phase 1 — Data model and card identity

The hard problem is knowing that a listing on eBay, a token on Courtyard, and a row in a price API are **the same card at the same grade**. Solve it early.

**Identity strategy (in priority order):**
1. **Cert number** (grader + cert) — exact match for a specific slab. Validate via PSA cert API where applicable.
2. **Canonical card key** — `(game, set, number, variant, grader, grade)` normalized.
3. **Fuzzy match** on titles — only produces *candidate* matches, stored with a confidence score, never auto-trusted above a threshold set in config.

**Core tables (sketch — refine in migrations):**
- `cards` — canonical card key fields, display name, image ref.
- `slabs` — grader, cert_number, grade, `card_id`.
- `sources` — platform registry (courtyard, collector_crypt, ebay, price_api…).
- `listings` — source, slab/card ref, ask price, currency, url, first_seen, last_seen, status.
- `sales` — source, slab/card ref, price, timestamp, tx hash or source id.
- `valuations` — source, card ref, value type (`platform_fmv`, `buyback`, `licensed_mid`, `onchain_median`), value, as_of.
- `packs`, `pack_odds` — platform, tier, price, published odds buckets, as_of.
- `match_candidates` — pairs + confidence + human verdict.
- `trades` — see Phase 4.

**Exit test:** ingest fixtures for 50 real slabs across two sources; ≥95% correct identity on cert-bearing items; fuzzy candidates reviewable in a simple admin page.

---

## 4. Phase 2 — Ingestion workers

One module per source under `ingest/`, each implementing:
```
fetch() -> raw records      # official API / RPC only
normalize(raw) -> models    # to the tables above
upsert(models)              # idempotent
```
- Rate limiting and backoff per source, configured, not hard-coded.
- Raw responses stored (compressed) for replay and debugging.
- Each worker logs: records fetched, inserted, updated, rejected, and why.
- A `/health/ingest` page shows last successful run and error rate per source.

**Exit test:** all Phase-0-approved sources run on schedule for 48 hours without manual intervention; replaying stored raw data reproduces the same DB state.

---

## 5. Phase 3 — The three engines

### 5a. Spread engine (Trade lane)
For each active external listing matched to a vault platform card:

```
all_in_cost   = ask + shipping + sales_tax_est + vault_intake_cost + (grading_cost if raw)
exit_floor    = platform_buyback_value            # the guaranteed exit
exit_market   = conservative platform resale value (e.g. median of recent on-chain sales, minus fees)
floor_margin  = exit_floor  - all_in_cost
market_margin = exit_market - all_in_cost
```
- Rank by `floor_margin` first (downside-protected deals), then `market_margin`.
- **Liquidity filter:** require N recent sales (configurable) before trusting `exit_market`.
- **Staleness filter:** discard if any input is older than its configured max age.
- Every opportunity shows its full calculation, inputs, and timestamps — no black-box scores.

### 5b. Pack EV auditor (Publish lane)
For each pack tier with published odds:
```
EV_platform = Σ p_i × platform_value_i
EV_buyback  = Σ p_i × buyback_value_i
EV_external = Σ p_i × external_value_i        # licensed/on-chain comps, where available
house_edge  = 1 − EV_buyback / pack_price
```
- Track over time; chart the edge per tier per platform.
- Flag when a platform's stated "fair value" diverges from external comps.

### 5c. Lag detector (Trade + Publish)
- Compare the trend of real sales (on-chain + licensed) to the trend of platform valuations per card.
- Alert when real prices fall X% while platform value is flat for Y hours (both configurable).
- Report output is informational; the human decides whether any action is appropriate and within platform terms.

**Exit test:** unit tests with hand-computed expected values for each formula; backtest the spread engine on stored history and report how many flagged deals would have met their floor margin.

---

## 6. Phase 4 — Private dashboard + trade ledger

- Auth: single owner account (Supabase Auth). No public signup yet.
- Views: ranked opportunities, card detail (all sources side by side, price chart), lag alerts, pack edge table.
- Alerts: email or push when `floor_margin` ≥ threshold. Alerts link to the listing; nothing is bought automatically.
- **Trade ledger:** record buy (price, fees, date, source), vault intake, sale/buyback (price, fees, date). Compute realized P&L per trade and per month; CSV export for taxes. Compare each trade's realized result against what the engine predicted — this is how the model gets calibrated.
- UI: apply the owner's existing house style if available; otherwise clean, dense, dark-mode-first.

**Exit test:** owner can go from alert → manual purchase → ledger entry → realized P&L in under two minutes of UI time.

---

## 7. Phase 5 — Public site (Publish lane)

- Static-generated pages (rebuilt on schedule):
  - **House Edge Index** — per platform, per tier, over time, with methodology page.
  - **Valuation gap reports** — where platform values sit versus external comps, in aggregate.
  - **Methodology** — every formula, every data source, every limitation. Rigor is the product.
- Affiliate links only where programs exist and terms allow; disclosure banner on every such page; 18+ notice on pack content; "not financial advice" footer.
- Show derived numbers only, per the data-license rules in §0.
- Basic analytics (privacy-respecting), sitemap, OpenGraph cards for sharing.

**Exit test:** a stranger can read the House Edge Index and reproduce one tier's number from the methodology page.

---

## 8. Phase 6 — Paid tier (Sell lane) — only after Phases 1–5 prove out

Gate this on evidence: the ledger shows the engine's predictions hold up over a meaningful number of real trades.
- Public signup, Stripe subscriptions, per-user alert thresholds and niches.
- Confirm every data license permits a commercial derived-data product before launch; upgrade licenses if needed.
- Terms of service and privacy policy reviewed by a professional before charging anyone.
- Rate-limit alert fan-out so subscribers aren't all pointed at the same single listing (it would erase the edge and create a bad experience) — e.g. stagger or cap per-listing alerts.

---

## 9. Repo layout

```
slabspread/
  app/            # FastAPI app, routes, templates
  engines/        # spread.py, pack_ev.py, lag.py  (pure functions, heavily tested)
  ingest/         # one module per source
  models/         # SQLAlchemy models
  migrations/     # Alembic
  site/           # static site generator for public pages
  fixtures/       # recorded real API responses for tests
  tests/
  docs/           # phase0-findings.md, data-licenses.md, decisions.md, methodology.md
  docker-compose.yml
  .env.example
```

---

## 10. Working agreement for Claude Code

- Work phase by phase. At the end of each phase, stop and summarize: what was built, test results, open questions, and anything in §0 that constrained the work.
- Keep engines as pure functions with no I/O so they're easy to test and audit.
- When a data source's terms are unclear, **exclude it and log the question** rather than guessing.
- Log every non-obvious design choice in `docs/decisions.md` (one short entry: decision, reason, alternative rejected).
- Never add a feature that places orders, bids, or logs into third-party accounts on the owner's behalf.
