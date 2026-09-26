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

## 2026-09-26 — Public Polygon node: address-filtered, chunked eth_getLogs; batched timestamps
- **Decision:** `polygon-rpc.com` went key-only, so the default is `polygon-bor-rpc.publicnode.com`. It requires an `address` filter and blocks lists longer than ~4, so the worker resolves the registry's operator/forwarder/minter role members each run and queries in chunks of 4. Block timestamps are fetched as JSON-RPC batches of 100.
- **Reason:** first live run showed ~1 Courtyard event per block (2,723 in 2,000 blocks); per-block timestamp calls would have cost ~1,500 requests per run.
- **Alternative rejected:** a paid RPC key. Nothing here needs one yet; the public node serves 2,000-block windows in ~20 s.

## 2026-09-26 — Solana parser resolves mints from token-balance metadata
- **Decision:** plain `transfer` instructions (no inline mint) are classified by looking up the source/destination token account's mint in `pre/postTokenBalances`; Metaplex Core instructions contribute the asset address as the NFT reference.
- **Reason:** Phygitals' real buybacks are plain transfers plus a Core move; the first live run found zero flows until this was fixed. Collector Crypt's `transferChecked` path was already correct on live data.

## 2026-09-26 — Collector Crypt public API: approved for private reads and derived analytics
- **Decision:** `collectorcrypt_api_enabled` defaults on. Workers identify themselves with a User-Agent, run at ~30/min against a published 300/min limit, and send a bearer key when the owner has one.
- **Reason:** the docs site says marketplace endpoints "need no credential", publishes per-IP limits and a key-request address — the platform intentionally makes the data available (its own ToS §4.6(iii) exception). The ToS's commercial-exploitation clauses still bind the *public* and *paid* lanes, which is why raw values stay private and Phase 6's license gate remains.
- **Alternative rejected:** treating ToS §4.6(iv) as covering the documented API. It names "the Website"; the docs contradict that reading and are the more specific statement.

## 2026-09-26 — Phygitals API built but off until written consent
- **Decision:** worker exists and is tested against live shapes; `phygitals_api_enabled` defaults off.
- **Reason:** the ToS says *written* consent for automated tools; the API docs' invitation is strong but not that. One email resolves it; guessing would not.

## 2026-09-26 — Courtyard: on-chain only; odds by manual snapshot
- **Decision:** no worker touches `api.courtyard.io`. Pack odds enter through `/admin/odds`, where the owner pastes the published odds line; provenance `manual_snapshot`.
- **Reason:** ToS §14.8/§14.11 and a live 403 on the metadata endpoint. The odds line is a public statement on a public page; reading it by hand and recording it is analysis, not automated access.
- **Consequence:** Courtyard sales are keyed by token id with no card identity until a sanctioned metadata path exists (OpenSea's API under its own terms is the candidate; owner-run).

## 2026-09-26 — Game inferred from set vocabulary when a source omits it
- **Decision:** `infer_game_from_set` maps a known Pokémon set list to `pokemon`; unknown sets stay game-less and are rejected.
- **Reason:** live Phygitals listings carry only a `Title`. Rejecting every row would be useless; guessing "pokemon" for everything would be wrong for their One Piece and sports inventory.

## 2026-09-26 — eBay: identity via getItem, not search
- **Decision (for the future `ebay_browse` worker):** search with `conditionIds:{2750}` and the three card categories, then call `getItem` per candidate to read `conditionDescriptors` (grader, grade, cert). Budget calls accordingly; display nothing older than 6 hours.
- **Reason:** the Browse OpenAPI schema confirms `ItemSummary` has no descriptors.

## 2026-09-26 — Pack tier value: measured pool sample first, band midpoint second, stated EV beside
- **Decision:** `PackOdds` stores `value_mean`/`sample_n` from the platform's public prize pool and `stated_ev` from the platform. `tier_from_snapshot` prefers the measured mean; the midpoint is the fallback; the stated EV is displayed, labelled, and never used in our house edge.
- **Reason:** the first live Collector Crypt run produced a −88% "house edge" on $250 machines — the band midpoint of a wide top tier (15,000–303,001) is not a value, it's a bound. Sampling the real pool gave 3,860 for the $3,000 machine against the platform's stated 3,032 and the midpoint's 4,598. A reader must be able to see which of those a number rests on.
- **Alternative rejected:** adopting the platform's stated EV as ours. It is not reproducible; the methodology page promises reproducibility.

## 2026-09-26 — Walk the whole prize pool; label anything less as a sample and an upper bound
- **Decision:** the gacha worker pages through every tier's pool (`page`/`limit=100`, `hasMore`) and stores the count against the platform's stock; `pool_full` only when they match.
- **Reason:** the endpoint serves cards value-descending, so a 40-card sample gave a $50 pack a −97% "house edge". The full pool reproduced the platform's stated EV to 0.02% — our first independent validation of a platform number, and the strongest evidence yet that "rigor is the product" can be delivered.
- **Cost:** ≈700 requests per run at ≤2/s against a published 300/min limit; scheduled hourly.

## 2026-09-26 — The 48-hour soak is the owner's to run; the container proved 3 hours
- **Decision:** stop restarting the scheduler in the build container every three hours and record the soak as 3 h continuous + slices. The exit-test criterion transfers to the first 48 h on the owner's host.
- **Reason:** the container suspends within minutes of the session idling; ten-minute slices every three hours are not a soak, and calling them one would be false. Three continuous hours at 1.3% transient error rate, with every failure root-caused, is what the environment can honestly show.
