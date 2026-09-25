# Decisions log

One entry per non-obvious choice: decision, reason, alternative rejected. Newest at the bottom.

## 2026-09-25 — Phase 0 findings are research-graded, not fetch-graded, on first pass
- **Decision:** `phase0-findings.md` records every claim with a verification mark (`VERIFIED-BY-FETCH`, `SEARCH-SNIPPET-ONLY`, `UNKNOWN`) and the spike is not considered closed until every item that gates a source is `VERIFIED-BY-FETCH` with a saved fixture.
- **Reason:** the build environment's network policy denies direct fetches to most vendor domains (eBay developer docs, Courtyard docs, PSA), so first-pass evidence is search-derived. Marking provenance keeps the ground-rule-3 license check honest instead of silently downgrading it.
- **Alternative rejected:** treating search snippets as sufficient. Licensing and ToS language is exactly where a paraphrase can be wrong in a way that matters.

## 2026-09-25 — gitleaks + detect-private-key as the pre-commit secret scan
- **Decision:** `.pre-commit-config.yaml` with gitleaks and `detect-private-key`.
- **Reason:** ground rule 5 requires a scan; gitleaks is the widely used default with no service dependency.
- **Alternative rejected:** a hosted secret scanner only (GitHub's). Useful, but it fires after the push, not before.

## 2026-09-25 — Courtyard FMV/buyback has no ingestion path until Q3 resolves
- **Decision:** the spread engine treats Courtyard `exit_floor` as unavailable; Collector Crypt is the first platform for the Trade lane.
- **Reason:** the only source of Courtyard FMV is an undocumented endpoint behind a WAF and a ToS anti-automation clause. Ground rule 1 forbids bypassing either. CC exposes `insuredValue` and buyback % through advertised public APIs and on-chain data.
- **Alternative rejected:** browser-fingerprint spoofing or third-party scrapers (Apify). Both are exactly what the ToS names.

## 2026-09-25 — Every "house edge" number names its valuation oracle
- **Decision:** the pack EV auditor and every public report carry the oracle (platform buyback value, platform FMV, external licensed comp, on-chain median) as a first-class field, never an unlabelled "value".
- **Reason:** CC and Arena Club buy back against their *own* valuations; a house edge computed against them measures something different from one computed against external comps. Conflating the two would make the methodology page false.
- **Alternative rejected:** a single blended "fair value". Simpler to display, impossible to reproduce.

## 2026-09-25 — Affiliate revenue is treated as speculative
- **Decision:** the Publish lane is planned around ads and the eventual paid tier; affiliate links are added per platform only after that platform's referral rules are read in full.
- **Reason:** Phase 0 found no cash affiliate program at any vault platform; Courtyard's rules may forbid public referral links; CC pays in points.
- **Alternative rejected:** assuming the plan's original affiliate model holds.

## 2026-09-25 — Raw research reports are kept in `docs/research/`
- **Decision:** the four per-topic research reports are committed verbatim alongside the synthesis.
- **Reason:** they carry every URL and provenance mark; the synthesis would otherwise be unauditable, and the §10 second pass needs the blocked-host lists.
- **Alternative rejected:** synthesis only. Loses the evidence trail the plan explicitly asks for.

## 2026-09-25 — Variant is part of the canonical key; asymmetric variant info yields a candidate
- **Decision:** `canonical_key` includes a variant slot drawn from a fixed vocabulary (`holo`, `full art`, `1st edition`…). A record with no variant token does not canonically equal one with a token; the pair surfaces as a fuzzy candidate for a human.
- **Reason:** Collector Crypt rows carry no variant field; Courtyard puts variants in untyped attributes. Treating "Blastoise" and "Blastoise – Holo" as the same card would be right for Base Set and wrong for sets that print both. The cost of a false merge (a wrong spread) is higher than the cost of a review click.
- **Alternative rejected:** dropping variant from the key. Simpler, more recall, silently wrong on holo/non-holo sets.

## 2026-09-25 — Python 3.11 floor, 3.12 in the container image
- **Decision:** `requires-python >= 3.11`; Dockerfile uses 3.12.
- **Reason:** the plan says 3.12; the build environment has 3.11 and the code needs nothing newer. Pinning to 3.12 would make the test suite unrunnable here for no gain.
- **Alternative rejected:** installing 3.12 in the environment. Extra moving part for zero code difference.

## 2026-09-25 — Tests run on SQLite; production on Postgres via `SLABSPREAD_DATABASE_URL`
- **Decision:** the test suite uses an in-memory SQLite engine; migrations are written with `render_as_batch=True` so they apply to both.
- **Reason:** the plan requires tests to be hermetic. The one Supabase project on the account (`cortex`) belongs to another system and is not touched; SlabSpread gets its own project when Phase 2 ingestion needs persistence.
- **Alternative rejected:** Postgres-in-Docker for tests. Correct but slower, and nothing in Phase 1 uses Postgres-only features.

## 2026-09-25 — The public-site generator will be `sitegen/`, not `site/`
- **Decision:** the plan's `site/` directory is renamed `sitegen/` when Phase 5 creates it.
- **Reason:** a top-level Python package called `site` shadows the standard-library `site` module that the interpreter imports at startup. It would break every Python process run from the repo root.
- **Alternative rejected:** keeping `site/` as a non-package directory. Too easy for someone to add an `__init__.py` later.

## 2026-09-25 — Own the chain clients; no web3.py / solana-py
- **Decision:** `ingest/chains/` holds ~200 lines of JSON-RPC + ABI decoding for exactly the events and transaction shapes we consume. `pycryptodome` supplies keccak.
- **Reason:** the surface is tiny (getLogs, getTransaction, two event ABIs, jsonParsed token transfers) and the SDKs pull in large dependency trees that are hard to audit for a tool handling money decisions. Encoders live beside the decoders so fixtures are self-consistent.
- **Alternative rejected:** web3.py + solana-py. Would be the right call if we needed signing or many contract ABIs; we need neither, and ground rule 2 forbids signing anyway.

## 2026-09-25 — `onchain_events` is an immutable ledger; `sales` derives from it
- **Decision:** every decoded chain event lands in `onchain_events` keyed by (chain, tx, log index). `sales` rows are derived from trade events; pack purchases and buybacks stay as event kinds.
- **Reason:** the plan's replay exit test needs a deterministic ground truth. Deriving from a ledger makes "replay reproduces the same state" provable, and keeps buyback/pack flows (which are not card sales) out of the sales table.
- **Alternative rejected:** writing sales directly from logs. Fewer tables, but re-deriving after a decoder fix would mean re-fetching the chain.

## 2026-09-25 — Gated sources run as workers that record `skipped`
- **Decision:** sources with an open license question have a worker that raises `SourceNotApproved` and logs a skipped run, rather than being absent.
- **Reason:** `/health/ingest` then shows *why* a source is idle, with the question number. An absent worker is indistinguishable from a forgotten one.
- **Alternative rejected:** commented-out schedule entries.

## 2026-09-25 — House edge is computed against buyback, with platform_edge alongside
- **Decision:** `house_edge = 1 − EV_buyback / price`; `platform_edge` (against the platform's own values) is reported next to it, and `EV_external` carries its probability coverage.
- **Reason:** buyback is the only exit a pack buyer is guaranteed; the platform's value is a claim. Reporting all three with their oracles lets a reader see the gap instead of trusting one number.
- **Alternative rejected:** a single "true EV" blending sources. Not reproducible by a stranger, which is the Phase 5 exit test.

## 2026-09-25 — Staleness rejects; it never extrapolates
- **Decision:** `compute_spread` returns a `Rejection` with the offending timestamp when any input is older than its configured max age. The backtest applies the same rule.
- **Reason:** a stale floor is the most likely way to buy a card the platform no longer wants. Carrying the last value forward would hide exactly the risk the engine exists to expose. The backtest fixture had to be made realistic (daily floor observations) rather than the rule relaxed.
- **Alternative rejected:** decaying confidence weights. More output, less auditability.

## 2026-09-25 — Sort key treats a missing floor as −∞
- **Decision:** an opportunity without a floor never outranks one with a floor, whatever its market margin.
- **Reason:** the plan ranks by downside protection first; a market-only deal has no protection.

## 2026-09-25 — Owner auth: pluggable local / Supabase, never "off" outside debug
- **Decision:** `app/auth.py` verifies either a local pbkdf2 hash or a Supabase Auth JWT (HS256, project secret, owner email enforced). `auth_mode=off` is refused unless `SLABSPREAD_DEBUG=1`.
- **Reason:** the plan names Supabase Auth, but provisioning a Supabase project is the owner's billable decision; local mode makes the dashboard usable on day one and the test suite hermetic. Refusing `off` in production closes the obvious footgun.
- **Alternative rejected:** Supabase-only. Would block Phase 4's exit test on infrastructure.

## 2026-09-25 — The paid tier's launch conditions are enforced in code, not in a doc
- **Decision:** `launch_gate()` checks the calibrated-trade count from the ledger, the license and legal-review flags, and Stripe config; `/subscribe` returns 503 with the missing items until all pass.
- **Reason:** plan §8 gates the Sell lane on evidence. A checklist in a document can be skipped; a 503 cannot.
- **Alternative rejected:** a single `paid_tier_enabled` flag. Too easy to flip without the evidence.

## 2026-09-25 — Fan-out rotates deterministically per listing
- **Decision:** `engines/fanout.py` picks at most `per_listing_cap` eligible subscribers starting at an offset hashed from the listing key, staggered by a fixed delay.
- **Reason:** plan §8 asks that subscribers not all be pointed at one listing. A hash offset spreads different listings across the subscriber base without needing state, and makes the assignment reproducible for support questions.
- **Alternative rejected:** random selection. Not reproducible; a subscriber who complains "I never get alerts" cannot be answered.
