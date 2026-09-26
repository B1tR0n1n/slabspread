# Owner runbook — the seven things only you can do

Each item is independent. Do them in any order; each one unlocks a specific part of the tool,
named at the end of its section. Never paste a secret into a chat; every secret goes into `.env`
locally or into the cloud environment's settings.

Evidence grade: steps 1–3 are about your own accounts and this repo. Steps 4–7 involve third-party
sites whose pages could not be opened from the build environment; their details come from Phase 0's
search-level research (`docs/research/`) and the live page is the authority where they differ.

---

## 1. Network access for the build environment

**Why:** Phase 0's evidence is search-grade and Phase 1/2's exit tests run on synthetic corpora only
because the container's egress policy denies every platform, vendor and RPC host.

**Steps**
1. In the Claude Code session, open the cloud environment menu in the title bar → **Edit**.
2. Under **Network access**, either pick a broader access level, or add these hosts to the allowed
   domains:
   - RPC: `polygon-rpc.com`, `api.mainnet-beta.solana.com`
   - Platform docs/APIs: `docs.courtyard.io`, `help.courtyard.io`, `api.courtyard.io`,
     `collectorcrypt.com`, `docs.collectorcrypt.com`, `api.collectorcrypt.com`,
     `gacha.collectorcrypt.com`, `docs.phygitals.com`, `phygitals.mintlify.app`, `api.phygitals.com`
   - Vendors: `www.psacard.com`, `api.psacard.com`, `developer.ebay.com`, `partnernetwork.ebay.com`,
     `www.pricecharting.com`, `www.sportscardspro.com`, `scrydex.com`, `justtcg.com`
   - Explorers/indexers: `polygonscan.com`, `solscan.io`, `magiceden.io`, `docs.magiceden.io`
   - Reference: `www.ftc.gov`
   Access levels are described at https://code.claude.com/docs/en/claude-code-on-the-web.
3. Start a new session (policy applies at session start) and say: *"rerun Phase 0 as a fetch pass
   and Phase 2 as a soak."*

**Unlocks:** primary-source `phase0-findings.md` with saved pages under `fixtures/phase0/`; real
50-slab captures for the Phase 1 exit test; the 48-hour Phase 2 soak; live opportunities.

---

## 1b. Optional: a Solana RPC key

The public `api.mainnet-beta.solana.com` endpoint allows ~40 requests per 10 s per method per IP and
returns 429 under the soak's load. A free Helius key (https://dev.helius.xyz, 1M credits/month)
removes that ceiling: set `SLABSPREAD_SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key=…`.
Polygon's public node has been fine at our rate.

## 2. A Postgres database (Supabase)

**Why:** tests run on SQLite; the dashboard, ledger, workers and site need a persistent DB.

**Steps**
1. https://supabase.com/dashboard → **New project**. Name `slabspread`, choose a region near you,
   set a strong DB password (save it in your password manager).
2. Project → **Settings → Database → Connection string → URI**. Copy it; it looks like
   `postgresql://postgres:[PASSWORD]@db.<ref>.supabase.co:5432/postgres`.
   For serverless hosts use the pooled (port 6543) URI instead.
3. Change the scheme to `postgresql+psycopg://` (the driver this repo installs) and put it in `.env`:
   ```
   SLABSPREAD_DATABASE_URL=postgresql+psycopg://postgres:<password>@db.<ref>.supabase.co:5432/postgres
   ```
4. Apply the schema: `alembic upgrade head`.
5. For cloud sessions, add the same variable in the environment settings (title-bar menu → Edit →
   environment variables) so workers there use it too.

**Alternatively:** say *"create a Supabase project"* and I will do steps 1–4 through the connector,
telling you where the password went.

**Unlocks:** persistent ledger, alerts, ingest history; `python -m ingest.scheduler` in the workers
container; `python -m sitegen.build` from live data.

---

## 3. Owner login

**Why:** every private route requires the owner; `auth_mode=off` is refused outside debug.

**Option A — local (fastest, no external service)**
```sh
python -m app.auth 'a long passphrase'        # prints a pbkdf2 hash
python -c "import secrets; print(secrets.token_urlsafe(48))"   # session secret
```
`.env`:
```
SLABSPREAD_AUTH_MODE=local
SLABSPREAD_OWNER_EMAIL=you@example.com
SLABSPREAD_OWNER_PASSWORD_HASH=pbkdf2_sha256$200000$...      # from the first command
SLABSPREAD_SESSION_SECRET=...                                 # from the second
```
Run `uvicorn app.main:app`, open `/login`.

**Option B — Supabase Auth (the plan's choice)**
1. In the Supabase project from step 2: **Authentication → Providers → Email** on; **Users → Add
   user** with your email + password (disable public signups under **Authentication → Settings**).
2. **Settings → API**: copy the **Project URL** and the **anon public** key.
   **Settings → API → JWT Settings**: copy the **JWT secret** (this verifies tokens server-side).
3. `.env`:
   ```
   SLABSPREAD_AUTH_MODE=supabase
   SLABSPREAD_OWNER_EMAIL=you@example.com
   SLABSPREAD_SUPABASE_URL=https://<ref>.supabase.co
   SLABSPREAD_SUPABASE_ANON_KEY=...
   SLABSPREAD_SUPABASE_JWT_SECRET=...
   SLABSPREAD_SESSION_SECRET=...
   ```
Only a token whose email equals `SLABSPREAD_OWNER_EMAIL` is accepted, so other users in the project
cannot get in even if signups were open.

**Unlocks:** the dashboard, alerts page, ledger, match review, ingest health.

---

## 4. eBay Browse API + Partner Network (Q6)

**Why:** eBay is the external market the spread engine compares against. Sandbox keys are free;
production Buy API access is granted per application. Sold-data APIs are closed — not needed.

**Steps**
1. https://developer.ebay.com → create a developer account → **Application Keys** → create a
   **Production** keyset. Note the App ID (client id) and Cert ID (client secret).
2. Join eBay Partner Network at https://partnernetwork.ebay.com; get your **Campaign ID**
   (10 digits). Keep the approval email — the Buy API application asks for it.
3. Apply for production Buy API access: developer portal → **Application Growth Check** (the form
   under your keyset). Subject line per eBay's guidance: *"Buy API Production Access (your eBay user
   ID)"*. Include: your EPN-registered eBay user ID, a description of the app (private price-comparison
   tool; affiliate links to listings; no automated purchasing), and how you tested in sandbox.
   Approval is by business model; expect days to weeks.
4. While waiting, read and save the pages that gate our design (they were unreachable from the
   build environment): the Browse API `item_summary/search` reference (does it return
   `conditionDescriptors` and the cert number?), the API License Agreement retention clauses,
   the EPN Network Agreement §I.G (disclosure placement), and the US rate-card line for trading
   cards. Put your notes in `docs/data-licenses.md` on the eBay row.
5. When approved, `.env`:
   ```
   SLABSPREAD_EBAY_CLIENT_ID=...
   SLABSPREAD_EBAY_CLIENT_SECRET=...
   SLABSPREAD_EBAY_CAMPAIGN_ID=...
   ```
   and tell me — the `ebay_browse` worker is the one source not yet written (it was excluded until
   licensed). Categories 261328 / 183454 / 183050 and condition 2750 (Graded) are already noted.

**Unlocks:** external listings in the opportunities table; affiliate links via `itemAffiliateWebUrl`.

---

## 5. PSA cert verification API (Q5)

**Why:** validates PSA cert numbers (identity strategy 1) and fills card fields for PSA slabs.

**Steps**
1. Create a free account at https://www.psacard.com, then open https://www.psacard.com/publicapi.
2. Generate an API token. You will be asked to accept the **PSA API End User Agreement**. Before
   clicking accept, copy the full agreement text into `docs/research/psa-end-user-agreement.md`
   (this is the storage/display/redistribution license we could not read).
3. `.env`: `SLABSPREAD_PSA_TOKEN=...`
4. Test the real limits (documented 100/day; an unsourced claim of a much lower free limit exists):
   ```sh
   curl -s -H "Authorization: bearer $SLABSPREAD_PSA_TOKEN" \
     https://api.psacard.com/publicapi/cert/GetByCertNumber/66499345 | python -m json.tool
   ```
   That cert is the real Blastoise from `fixtures/real/courtyard/`. Save the response to
   `fixtures/real/psa/GetByCertNumber_66499345.json`. Note whether `TotalPopulation` is null.
5. Update the PSA row in `docs/data-licenses.md` from the agreement text, then tell me; the
   `psa_cert` worker gets written against that saved response.

**Unlocks:** `Slab.cert_verified_at`; PSA-sourced card fields; a second identity source for the
Phase 1 exit test.

---

## 6. Licensed price data — PriceCharting / SportsCardsPro (Q4)

**Why:** the only candidate pair with a per-grade ladder across Pokémon *and* sports. Their standard
terms are internal-use only; a public app needs written permission.

**Steps**
1. Read the live pages: https://www.pricecharting.com/api-documentation and
   https://www.pricecharting.com/page/terms-of-service (same for sportscardspro.com). Confirm the
   API tier's current price (sources disagreed: ~$49/mo vs ~$59/yr).
2. Email them (contact on the API page). Ask, in writing:
   - May a subscriber-facing app display **derived analytics** (spreads, percentages, rankings)
     computed from your per-grade values?
   - May the **owner's private dashboard** display raw per-grade values?
   - May we store daily snapshots to build history (the API returns current values only)?
   - What is the JSON rate limit?
   - What attribution do you require?
3. If the answer allows derived analytics: subscribe, put `SLABSPREAD_PRICECHARTING_TOKEN=...` in
   `.env`, file the reply under `docs/research/pricecharting-license-reply.md`, and move the row
   in `docs/data-licenses.md` to `approved` with the exact wording.
4. If not: the Pokémon-first fallback is Scrydex Growth (https://scrydex.com/pricing) with JustTCG
   as the cleanest license; sports fallback is Card Hedge — each needs the same written check.

**Unlocks:** `licensed_mid` valuations; the `EV_external` column and FMV-divergence figure on the
public site; external comps in the lag detector.

---

## 7. Platform permissions (Q1 Collector Crypt · Q2 Phygitals · Q3 Courtyard)

**Status after the 2026-09-26 fetch pass:** Q1 resolved — Collector Crypt's documented public API is
on by default; optionally email `support@collectorcrypt.com` for a `ccsk_` key (higher limits) and, before
the paid tier, written confirmation for commercial derived use. Q2 — email `hello@phygitals.com` quoting
their API docs' "price-comparison tooling" line and ask for written consent under ToS §11; then set
`SLABSPREAD_PHYGITALS_API_ENABLED=true`. Q3 resolved — no automated path; use `/admin/odds` for odds and
see step 8 for card identity. Full quotes in `docs/phase0-findings.md` ("Fetch pass").


**Why:** on-chain data is already approved. These are about each platform's *own* API and values.

**Q1 — Collector Crypt.** Read https://collectorcrypt.com/terms-of-service (or the link in their
site footer) and https://docs.collectorcrypt.com/gacha/api + `/marketplace/api`. Two questions:
is there an anti-automation clause, and is `x-api-key` required (docs say yes; integrators found
it unenforced). If the terms permit reading the public API, set
`SLABSPREAD_COLLECTORCRYPT_API_ENABLED=true` and move the row to `approved` with the quote. If a
key is required, request one in their Discord (the docs point there) → `SLABSPREAD_CC_API_KEY`.

**Q2 — Phygitals.** Read https://docs.phygitals.com (Terms of Service under "user agreements") and
the public API page on https://phygitals.mintlify.app. Their ToS bars automation "without explicit
permission"; a documented public API is arguably that permission but it must be confirmed. Email
them (contact in the docs) asking whether reading `api.phygitals.com/api/marketplace/*` and
`/api/vm/available` on a schedule for analytics is permitted. On a yes in writing:
`SLABSPREAD_PHYGITALS_API_ENABLED=true`, file the reply, move the row.

**Q3 — Courtyard.** Read https://docs.courtyard.io/courtyard/logistics-and-legal/user-agreements/terms-of-service
in full. The FMV/buyback number lives only on a WAF-gated undocumented endpoint, so the honest
options are: (a) ask Courtyard (support in the docs) whether a partner/API path to `fmv_estimate_usd`
exists; (b) accept that Courtyard is a **sales/mint data source only** and its `exit_floor` stays
unavailable. On (a) with a yes: `SLABSPREAD_COURTYARD_METADATA_ENABLED=true` and the tokenURI
enrichment worker runs. Also, while on their docs, read the referral-program rules: the "people you
know" clause decides whether a public referral link is allowed (Q7 on affiliates).

**Unlocks:** Q1 → `platform_odds` worker, `insuredValue` floors from the API, pack edges on the
public site. Q2 → Phygitals listings and odds. Q3 → Courtyard card metadata and FMV floors.

---

## 8. Courtyard card identity via OpenSea (optional)

Courtyard's tokenURI is off-limits, so its 1,700+ daily trades are keyed by token id only. OpenSea's
API exposes the same metadata under OpenSea's own terms. Create an API key at https://docs.opensea.io
(developer account), read their API terms for caching/display, set `SLABSPREAD_OPENSEA_API_KEY`, and
tell me — I'll write the enrichment worker against your first response.

## After any of these

Tell me which one landed. Each maps to a specific next action on my side:

| Done | I then |
|---|---|
| 1 | rerun Phase 0 as a fetch pass; capture real slabs; run the Phase 2 soak |
| 2 | verify migrations on Postgres; run the scheduler against it |
| 3 | nothing — log in at `/login` |
| 4 | write `ingest/ebay_browse.py` against your first real response |
| 5 | write `ingest/psa_cert.py` against the saved response |
| 6 | write `ingest/price_api.py` for the vendor you licensed |
| 7 | flip the Phygitals gate, run its workers live, extend the exit tests |
| 8 | write `ingest/opensea_courtyard.py` for Courtyard card identity |
