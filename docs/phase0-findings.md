# Phase 0 — Verification spike findings

**Date:** 2026-09-25 · **Status:** first pass complete; **spike not closed** (see §10).

## How to read this

Every claim carries a provenance mark:

| Mark | Meaning |
|---|---|
| **FETCH** | The page was retrieved and read. Almost always a third-party GitHub repo that recorded live probes of the platform (DefiLlama adapters, integrator code, captured fixtures) — credible, but not the platform's own words. |
| **SNIPPET** | Only a search-engine snippet of the primary page was seen. Numbers and ToS wording must be re-read before we rely on them. |
| **UNKNOWN** | Nothing found. |

Why: the build environment's egress policy denied every first-party host (courtyard.io, collectorcrypt.com, phygitals.com, psacard.com, developer.ebay.com, pricecharting.com, and ~80 more — full lists in `docs/research/`). Only `github.com` / `raw.githubusercontent.com` were reachable. Long-form per-item reports with every URL live in [`docs/research/`](research/). This file is the synthesis and the decision.

**Headline:** the on-chain lane is solid and legitimate for all three vault platforms. The off-chain lanes (platform FMV/buyback numbers, licensed prices, eBay) each hinge on a license or ToS clause that is currently only SNIPPET-grade. Phases 1–2 can begin on-chain data; nothing that touches a licensed feed or a platform's private API ships until its row in §10 flips to FETCH.

---

## 1. Courtyard (Polygon)

| Question | Answer | Mark |
|---|---|---|
| Card NFT contract | `0x251BE3A17Af4892035C37ebf5890F4a4D889dcAD` (ERC-721 "CourtyardRegistry", transparent proxy, ~288k tokens). `tokenId = hex(sha256(metadata))` ("proof of integrity"). | FETCH (DefiLlama adapter, contract source mirror) |
| Marketplace | Own orderbook, **not Seaport**: `0x5E4943373c2198625BD441Ae0629E9E7b4FB4797`; Coinflow variant `0x7fbF08A0eD3EF12565A61935Ca6339BbeCC25F48`. Settles in native USDC `0x3c499c…3359`. | FETCH (returned by `/orderbook/config`, captured fixture) |
| Sale events | `TradeExecuted(bidder, asker, nftTokenId, erc20Token, amount, tradeSignature, feeAccrued)` from trusted operators/forwarders (enumerable via registry view fns). Observed real sale tx `0x71f546e3…71c3a` (2026-06-09, 150 USDC). | FETCH |
| Pack mints | `TokenPurchasedAndMinted(mintedTo, tokenAddr, tokenId, paymentToken, paymentAmount)` from minter-role addresses; ~6% fee. Randomness: Chainlink VRF. | FETCH / SNIPPET (VRF) |
| Buybacks on-chain | **Unresolved.** DefiLlama claims to net them but its adapter has no detection logic. Proceeds are credited to the user's Courtyard USDC balance, so the buyback may be purely custodial. Three hypotheses to test with a Polygonscan session (research_onchain §1.2). | UNKNOWN |
| Token metadata | `https://api.courtyard.io/index/token/polygon/{contract}/{tokenIdHex}/metadata.json`. Attributes: Grader, **Serial = cert number**, Grade, Category, Year, Set, Title/Subject, Language, Card Number, Event (pack). No price. | FETCH (captured sample: PSA 66499345 Blastoise) |
| FMV / buyback price | **Not in tokenURI.** Live but undocumented `GET api.courtyard.io/orderbook/assets/{proofOfIntegrity}` → `fmv_estimate_usd`, `minimum_bid_threshold`, bids/asks. Buyback = 90% FMV (95% watches), derivable, not exposed. Gated by WAF + browser-TLS fingerprint; bare server requests get 403. | FETCH (3rd-party probe table 2026-08-01) |
| Secondary venues | OpenSea collection `courtyard-nft` (Seaport). Magic Eden EVM closed 2026-03-09. | FETCH / SNIPPET |
| Official API | None. No developer program, no API terms. Listings are Algolia (public key, 5k-hit ceiling). | FETCH (empty api-evangelist stub) |
| ToS | Prohibits "any robot, spider, crawler, scraper… not authorized by us" and bypassing "instructions that control automated access". 18+. | SNIPPET |
| Affiliate | User referral only (points, 6 tiers, ≥$20 pack + ID verification). Rules bar misleading statements; snippet says links are for "people you know" — may exclude public-site use. No cash affiliate. | SNIPPET |
| Pack odds | On each pack page, by FMV bucket (not per card), real-time, HTML/JS only. No JSON odds endpoint found. | SNIPPET |

**Verdict.** On-chain: **approved** (events + tokenURI, cert number present). `api.courtyard.io` and Algolia: **excluded** under ground rule 1 — the ToS clause plus the WAF are exactly "instructions that control automated access". OpenSea API: legitimate secondary route under OpenSea's terms (to be read). FMV/buyback for the spread engine therefore has **no legitimate machine path today**; §10 Q3.

## 2. Collector Crypt (Solana)

| Question | Answer | Mark |
|---|---|---|
| Collections | Metaplex Core `CCryptUfeFSZ3Fgc9FLeKrhLVAP67FSqi1GuVoj9CRac` (~62k, current) and legacy pNFT `CCryptWBYktukHDQ2vHGtVcmtjXxYzvw8XNVY64YN2Yf` (~63k). Core assets carry PermanentTransfer/BurnDelegate = CC. | FETCH (Tangem README, integrator code) |
| Programs | Marketplace V2 `CcmRKTuZCGJBWQwMHvDYApBRvSZNHqGJXkznqpDTSQUr` (Anchor, 52 ix, on-chain IDL); Swap `CCSwaptc…UENC`; VRF `ccvrfu3f…tdgQ` (MIT, RFC 9381). | FETCH (IDL dump) |
| Sale detection | **No Anchor events in the IDL.** Decode `buy_*` / `accept_offer_*` instructions + USDC transfers to seller/treasury. Also sells on Magic Eden (`collector_crypt`) and OpenSea OS2 Solana. | FETCH |
| Gacha purchases | No program. Memo `<slug>-<uuid>:open` (co-signed by `GachaNgyXTU3zFogQ8Z5jR2BLXs8215X2AtEH18VxJq3`) + USDC to treasury ATA `D9CEog…zQZk`. Old sink `Gachaz…ksc9z`; fiat rail `96DULv…wW9s`. | FETCH (DefiLlama, Tangem) |
| Gacha buybacks | USDC outflow from gacha sink to non-team wallet + NFT returned via delegate. 85/90/93% of insured value by tier, 72 h window, 40k USDC cap. | FETCH |
| Token metadata | Grading company, grade, **Grading ID = cert number**, set, category, year, `insuredValue`. Images `nft.collectorcrypt.com`. | FETCH |
| Platform value | `insuredValue` is the buyback basis; served in `GET api.collectorcrypt.com/marketplace` (no auth, 30 s CDN cache, ≤100/page, 429 on abuse) and in DAS metadata. No sold-history endpoint. | FETCH |
| Official API | docs.collectorcrypt.com: Marketplace API, Gacha API (`/api/machines`, `/api/stock`, `/api/vrf/verify`, `/api/pack/status`…), Vault API. Docs say `x-api-key`; two integrators found it unenforced mid-2026. CC tweeted "Our APIs are open". | FETCH (doc mirrors) / SNIPPET (tweet) |
| Sale history via indexers | Magic Eden `GET /v2/collections/collector_crypt/activities?type=buyNow` (120 QPM free, ME venue only, API being wound down). Helius DAS for assets (free 1M credits; DAS 2 rps free). Whether Helius parses CC's program as `NFT_SALE`: UNKNOWN. | FETCH / SNIPPET |
| ToS | Main ToS unreachable. TON-testnet ToS bans bots; unclear if it applies. No anti-scraping clause found for main site. US/UK/China restricted for $CARDS and (per reports) gacha. 18+. | UNKNOWN |
| Affiliate | Referral → Gacha Points (% of referee's points; % unpublished) → packs. No cash program. Partner-level `x-api-key` memo tagging exists. | SNIPPET |
| Pack odds | **Machine-readable**: `/api/machines` → per-tier odds (e.g. 1/4/15/80%), `tierRanges`, stock, `ev`, `instantBuyback`. Per-card odds derivable (tier weight ÷ cards in tier). VRF proofs verifiable. | FETCH (doc mirrors) |

**Verdict.** On-chain: **approved**. Public APIs: **provisionally approved** — openly advertised, no anti-scraping clause found, DefiLlama/Bitquery precedent — pending the actual ToS text and the `x-api-key` question (§10 Q1). Best buyback-floor data of the three platforms.

## 3. Phygitals and other platforms

| Platform | Chain / data path | Cert in metadata | Odds | ToS | Verdict |
|---|---|---|---|---|---|
| **Phygitals** | Solana. Core collection `phygZDQZJZVHvJGYPGoKPYUtXw7mstSYtTtcuh8LJcC` (~47k), cNFT `BSG6Dy…2xAM` (~80k) — FETCH (3rd-party, unconfirmed by docs). Packs/buybacks = USDC to/from `62Q9ee…S8dS` (also `buyback_wallet` in their JSON); buyback leg not memo-tagged. Secondary = Tensor (~86%) + Magic Eden. Public REST `api.phygitals.com` documented on Mintlify: `/api/marketplace/marketplace-listings`, `/api/vm/available?includeRepacks=true` (packs, `rarity_distribution`, `ev`, `buyback_percent`, `mint_price`). 60 s edge cache, 429s. | `Grade` trait only; cert UNKNOWN | JSON, per value tier; EV published; commit-reveal fairness (not VRF) | Anti-automation "without explicit permission" — SNIPPET | On-chain **approved**. API **excluded until written permission** (§10 Q2). Referral: 1% of referees' buybacks as site credit. |
| Beezie | Base → Solana (Q2 2026); unofficial key-less API with cert/serial in metadata; per-tier odds | yes (3rd-party) | web | UNKNOWN | **Later** |
| Jupiter Gacha | Front-end over CC/Phygitals inventory | n/a | per tier | n/a | Covered via CC/Phygitals |
| Arena Club | Off-chain; per-card hit rates; no API | n/a | web, per card | UNKNOWN | **Later** |
| Drip Shop Live | Off-chain; odds per listing | n/a | web | UNKNOWN | **Later** |
| Alt | No developer program; private GraphQL only | — | — | — | **No legitimate path** |
| Fanatics Collect | ToS bans scraping and "similar or competitive digital property" | — | — | SNIPPET | **No legitimate path** (affiliate program via Impact exists) |
| "Collectible Exchange", "Vaulted" | No platforms found by those names | — | — | — | UNKNOWN / dropped |

## 4. Published pack odds — summary

| Platform | Where | Format | Granularity | Readable under ToS? |
|---|---|---|---|---|
| Courtyard | pack page | HTML/JS | FMV bucket | Dated manual reads only |
| Collector Crypt | `/api/machines` + machine page | JSON + on-chain VRF | rarity tier (per-card derivable) | Yes, provisionally |
| Phygitals | `/api/vm/available` + pack page | JSON | value tier + EV | Needs permission |
| Arena Club / Beezie / Drip / Jupiter | web | HTML | per card / per tier | UNKNOWN |

Precedent aggregators exist (PullValue, RipIndex, PackSpy, ccstats) — mostly affiliate-driven review sites. Regulatory: no US federal/state odds-disclosure law as of Sep 2026; FTC acts case-by-case (2024 warning letters on age-gating/odds; 2025 Cognosphere settlement). Belgium bans, Netherlands/Germany/Korea/Japan/China regulate. All three platforms are 18+. **Report design rule:** separate *published tier odds*, *observed odds*, *EV under buyback*, and *EV under external FMV* — CC and Arena Club buy back against their own valuations, so "house edge" depends on which oracle is named.

## 5. Licensed price data

Full 15-vendor table in `research_price_apis.md`. Condensed:

| Vendor | Pokémon | Sports | Per-grade PSA/BGS/CGC/SGC | Basis | Entry cost | Public display / derived analytics | Mark |
|---|---|---|---|---|---|---|---|
| PriceCharting + SportsCardsPro | ✓ | ✓ (SCP) | ✓ full ladder | eBay sold → value, current only, no history | ~$49/mo or $59/yr (conflicting) + **negotiated commercial license** | ToS: internal use only; "cannot be used in any software… accessible to third parties… without express written permission" | SNIPPET |
| Scrydex | ✓ | ✗ | ✓ low/mid/high/market + daily history | eBay + auction sold | Growth $99/mo | Business use licensed; redistribution needs written auth; derived analytics unaddressed | SNIPPET |
| JustTCG | ✓ | ✗ | PSA/BGS/CGC (v2 beta); SGC unclear | blended marketplace | $19/mo | **Explicitly licenses display + derived analytics + caching**; bans raw redistribution | SNIPPET + FETCH (SDK README) |
| PokemonPriceTracker | ✓ | ✗ | PSA all grades; others + pops | eBay sold | Business $99/mo | Commercial on Business; attribution links required; ToS text not found | SNIPPET |
| TCG Price Lookup | ✓ | ✗ | all six graders 1–10 | eBay sold slabs | Trader $14.99/mo | Names "graded-card analytics products" as permitted | SNIPPET |
| Card Hedge API | ✓ | ✓ | PSA/BGS/SGC/CGC/TAG + history | eBay/Fanatics/Heritage | from $49/mo | ToS bars distribution/derivatives without permission | SNIPPET |
| Card Ladder | ✓ | ✓ | sales-level | 14 venues | enterprise only | contract; scraping banned | SNIPPET |
| TCGplayer API, pokemontcg.io | — | — | none | — | closed / deprecated | — | **excluded** |
| Alt, 130point, Market Movers, Collectr | — | — | — | — | no self-serve license | — | **excluded** |

**Recommendation.** Primary: **PriceCharting + SportsCardsPro under one negotiated commercial license** — the only pair with a complete per-grade ladder across Pokémon *and* sports. Blocker is contractual, not technical. Pokémon-first fallback if that fails: **Scrydex Growth**, with **JustTCG** as the cleanest license. Sports fallback: **Card Hedge**, pending written confirmation on derived analytics. Never: Apify/Parse.bot wrappers of any of these (they are scrapers).

**Design constraint confirmed:** every candidate forbids republishing raw values by default. Public pages show derived numbers only (ground rule 3). The private dashboard may show raw values under whichever license we sign.

## 6. PSA public cert API

| Item | Finding | Mark |
|---|---|---|
| Token | Free psacard.com account → `/publicapi` → bearer token, non-expiring. "PSA API End User Agreement" accepted at generation; **text not obtained**. | FETCH (3rd-party doc) |
| Endpoints | `GET api.psacard.com/publicapi/cert/GetByCertNumber/{cert}`, `GetImagesByCertNumber`, `GetByCertNumberForFileAppend`. | FETCH |
| Response | `{PSACert:{CertNumber, SpecID, CardNumber, YearIssued, Brand, Variety, Subject, Category, CardGrade, TotalPopulation, PopulationHigher, LabelType, …}, IsValidRequest, ServerMessage}`. HTTP 200 even for invalid certs. **Population fields return null on the public API.** No set field (compose from Year+Brand+Variety). | FETCH |
| Rate limit | Documented 100 calls/day (429 above). One unsourced claim of a mid-2026 cut to ~1/day for free tokens. **Test empirically.** | FETCH / UNKNOWN |
| Storage/display terms | UNKNOWN — read the End User Agreement before caching. | UNKNOWN |
| CGC / BGS / SGC | Web lookup only; no official APIs. Third-party wrappers are scrapers → excluded. | SNIPPET |

## 7. eBay Browse API and EPN

| Item | Finding | Mark |
|---|---|---|
| Access | Sandbox keyset free; **production Buy API is gated**: apply via Application Growth Check, needs EPN-registered eBay user ID and sandbox test notes; approval by business model. Sandbox search returns mock/empty data. | SNIPPET |
| Rate limit | 5,000 calls/day per app by default; raise via Growth Check. `item_summary/search` ≤10,000 items per query. | SNIPPET / FETCH (spec mirror) |
| Graded filters | Categories 261328 (sports singles), 183454 (CCG singles), 183050 (non-sport). Condition 2750 = Graded; descriptors 27501 Professional Grader, 27502 Grade, 27503 Certification Number (optional). `getItem` returns `conditionDescriptors`. Whether `item_summary/search` returns them or cert: **UNKNOWN**; community reports imprecise grade filtering via `aspect_filter`. | SNIPPET |
| Sold data | Marketplace Insights: "restricted and not open to new users". `findCompletedItems` decommissioned Feb 2025. **Confirmed out of scope.** | SNIPPET |
| EPN | Header `X-EBAY-C-ENDUSERCTX: affiliateCampaignId=…` → `itemAffiliateWebUrl` (must use it to earn). 24 h cookie; trading cards ~3% (DE rate card; US unread). Network Agreement §I.G: disclosure must sit **near the links**, not only on a legal page. | FETCH (spec) / SNIPPET |
| License | API License Agreement: destroy eBay data within 30 days once no longer needed; delete PII promptly; display per Buy API UX rules. No hard cache TTL found. | SNIPPET |

**Verdict.** Approved in principle; **blocked on production approval** (an application step the owner must do). Design for short-lived listing cache, no seller PII, a documented deletion path.

## 8. Affiliate / referral programs

| Platform | Program | Payout | Content rules | Public-site use? |
|---|---|---|---|---|
| Courtyard | user referral | points → pack credit | no misleading claims; "people you know" | **doubtful** — confirm |
| Collector Crypt | user referral | Gacha Points (% unpublished) | none found | UNKNOWN |
| Phygitals | Refer & Earn | 1% of referees' buybacks, site credit only | rates live in-app, changeable | plausible |
| Fanatics Collect | affiliate via Impact | % of purchases, monthly | standard | yes, but data path excluded |
| Whatnot | creator affiliate | 1–10% | standard | yes |

FTC: material connections (including credits and points) must be disclosed clearly, near the claim, same medium (16 CFR 255, 2023 rev.). "EV +X%" copy is an implied earnings claim under the Oct-2021 Notice of Penalty Offenses — substantiate it and show spread, fees, variance. A "not financial advice" line is not a safe harbor. Chance-based products: accurate odds, age-gating (2019 loot-box workshop; 2025 Cognosphere).

**Verdict.** Affiliate revenue for the Publish lane is **thinner than the plan assumed**: only Phygitals pays an ongoing share (as credit), and Courtyard's terms may forbid public referral links. Treat affiliate income as speculative; ads and the paid tier carry the lane.

---

## 9. Scope adjustment for Phases 1–5

| Plan element | Change |
|---|---|
| Ingest sources (Phase 2) | **Start with:** Polygon events + tokenURI (Courtyard); Solana instruction decoding + DAS + `api.collectorcrypt.com` (CC); Solana USDC flows (Phygitals). **Gated:** eBay Browse (production approval), licensed price API (contract), PSA (agreement text), Phygitals API (permission), Magic Eden (terms + wind-down risk). |
| Spread engine (5a) | `exit_floor` is computable **only for Collector Crypt** today (`insuredValue × buyback %`). Courtyard FMV has no legitimate machine path; treat Courtyard `exit_floor` as unavailable until §10 Q3 resolves. Phygitals: buyback % is in their JSON but the API is pending permission. |
| Pack EV auditor (5b) | CC first (JSON odds + VRF). Phygitals second. Courtyard via dated manual snapshots stored as fixtures, until an odds JSON is found. |
| Identity (Phase 1) | Cert numbers confirmed in Courtyard (`Serial`) and CC (`Grading ID`) metadata — strategy 1 works for both. Phygitals cert unknown → fuzzy/canonical-key only. PSA API validates PSA certs; other graders unvalidatable programmatically. |
| Publish lane | Affiliate income downgraded to speculative. Methodology page must name the valuation oracle behind every "house edge" number. |
| Ground rule 1 additions | Explicitly excluded: `api.courtyard.io`, Algolia, Alt GraphQL, Fanatics, all Apify/Parse.bot wrappers, third-party cert scrapers for CGC/BGS/SGC. |

## 10. Open questions — the spike closes when these are FETCH-grade

| # | Question | Gates | How to resolve |
|---|---|---|---|
| Q1 | Collector Crypt main ToS: any anti-automation clause? Is `x-api-key` required for gacha/marketplace reads? API ToS? | CC API ingestion | Read `collectorcrypt.com/terms-of-service`, `docs.collectorcrypt.com/{gacha,marketplace}/api` |
| Q2 | Does Phygitals' public Mintlify API constitute "explicit permission"? Cert field? | Phygitals API | Read ToS + API page; email for written permission |
| Q3 | Courtyard FMV/buyback: any sanctioned path (partner API, OpenSea metadata, on-chain)? Buyback on-chain signature? | Courtyard `exit_floor` | Read full ToS; Polygonscan session on a known buyback; ask Courtyard |
| Q4 | PriceCharting/SportsCardsPro commercial-license price and whether derived metrics + raw per-grade values may be shown; confirm JSON field→grade mapping; snapshot storage allowed? | Primary price feed | Email PriceCharting; read live API docs + ToS |
| Q5 | PSA End User Agreement text; real rate limit; population fields | PSA ingestion | Generate token; save agreement; probe |
| Q6 | eBay: does `item_summary/search` return `conditionDescriptors`/cert? Exact aspect_filter syntax; EPN US rate card + §I.G; license retention clauses | eBay ingestion + EPN | Read live docs; apply for production |
| Q7 | Courtyard referral rules — public-site links allowed? CC referral written terms? | Publish lane affiliate links | Read rules pages |
| Q8 | Magic Eden API terms ("commercial use prohibited"?) and 2026 wind-down scope for Solana | CC sale history fallback | Read `magiceden.io/legal-policies/api-terms` |
| Q9 | Confirm Phygitals collection addresses on Solscan / docs | Phygitals on-chain | Solscan |

**To unblock from this environment:** allow these hosts in the environment's network policy — `docs.courtyard.io`, `help.courtyard.io`, `collectorcrypt.com`, `docs.collectorcrypt.com`, `docs.phygitals.com`, `phygitals.mintlify.app`, `www.psacard.com`, `developer.ebay.com`, `partnernetwork.ebay.com`, `www.pricecharting.com`, `www.sportscardspro.com`, `scrydex.com`, `justtcg.com`, `magiceden.io`, `docs.magiceden.io`, `polygonscan.com`, `solscan.io`, `www.ftc.gov`. Then a second pass saves primary pages and sample responses under `fixtures/phase0/`.

## Exit test status

> every item answered or explicitly marked "no legitimate path — excluded"

All eight items are answered at the level the environment allowed, and exclusions are explicit. **Not met** in spirit: the plan asks for evidence with saved sample responses, and `fixtures/phase0/` is empty because no primary host was reachable. Phase 1 may start on the on-chain path; the spike is reopened for the §10 pass.

---

# Fetch pass — 2026-09-26

Network access was granted and the spike re-run against primary sources. Three researchers fetched
~100 pages and API responses; every page is saved verbatim under `fixtures/phase0/<host>/` with
URL and timestamp, and the full reports are in `docs/research/fetch_*.md`. Marks below are now
**FETCH** unless stated. Live RPC runs are also in: see "Live chain results".

## Open questions — resolved

| # | Question | Answer | Evidence |
|---|---|---|---|
| **Q1** | Collector Crypt ToS / API key | **Approved for documented public reads.** The ToS (arweave PDF, rev. 2026-06-09) §4.6(iv) bars "any robot, spider, or other automatic device … to access the Website", and (viii)/(xi) bar commercial exploitation and building a competing service; it never mentions the API. The docs site separately states "Marketplace endpoints need no credential", publishes per-IP rate limits (300/min), requires a `User-Agent`, and tells third parties how to request a key (`support@collectorcrypt.com`). `GET /marketplace` rows carry `gradingID` (cert). `x-api-key` is required only on gacha `/api/v1/machines` and `/api/v1/stock`; `/api/machines` answers without one. | `fixtures/phase0/arweave.net/…`, `docs.collectorcrypt.com/{marketplace-api,gacha-api}.md`, `api.collectorcrypt.com/marketplace-step5.json`, `gacha.collectorcrypt.com/api-machines.json` |
| **Q2** | Phygitals API permission | **Built, gated off.** ToS §11: "Using bots, scripts, or automated tools to interact with the Service without Phygitals' prior written consent" is prohibited; the API docs say pack/marketplace GETs "do not require a key" and list "Bots, scripts, custom tooling" and "price-comparison tooling" as intended uses. The docs are an invitation; the ToS names *written* consent. Worker runs only after `SLABSPREAD_PHYGITALS_API_ENABLED` — owner emails `hello@phygitals.com`. Listings carry no cert; metadata is often just `Title`. | `docs.phygitals.com/terms-of-service.md`, `phygitals.mintlify.app/public-api*.md`, `api.phygitals.com/*.json` |
| **Q3** | Courtyard FMV / metadata path | **No legitimate automated path — excluded.** ToS §14.8 bars "any robot, spider, crawler, scraper, script … not authorized by us"; §14.11 bars bypassing automated-access controls; one plain request to the tokenURI returned **403**. No developer or partner page exists (`llms.txt` index checked). Courtyard is an **on-chain sales/mint source only**. Odds are published as an FMV-bucket line in each pack's public config JSON; they enter via the owner's manual snapshot form (`/admin/odds`), never a worker. | `docs.courtyard.io/terms-of-service.md`, `api.courtyard.io/token-metadata.md`, `api.courtyard.io/configs-vending-machine-*.md` |
| **Q4** | PriceCharting license | **Confirmed internal-use only; commercial license needed.** "The API and CSV data are licensed for internal use only. Sharing our price data with a third party, or making it available within an application or service used by others, requires a commercial license and express written permission." Rate: 1 call/s. Field→grade map recorded (manual-only-price = PSA 10, etc.). SportsCardsPro: Cloudflare-blocked, unverified. Scrydex terms grant nothing by implication. **JustTCG** §7.1 explicitly permits end-user display, derived analytics and caching on paid tiers — the cleanest license found. | `www.pricecharting.com/*.md`, `scrydex.com/*.md`, `justtcg.com/*.md` |
| **Q5** | PSA agreement / limits | **Partly.** OAuth2 password grant; endpoints and fields confirmed from `swagger.json` (`TotalPopulation`, `PopulationHigher` present). Rate limit **not documented anywhere public**; the End User Agreement is behind the sign-in (`app.collectors.com`). Owner action stands. | `api.psacard.com/publicapi-swagger-json.md`, `www.psacard.com/*.md` |
| **Q6** | eBay Browse details | **Design change.** `item_summary/search` does **not** return `conditionDescriptors`; only `getItem` does (for the three card categories). Graded filter is `filter=conditionIds:{2750}`; descriptor IDs recorded (PSA=275010, Grade 10=275020…). Production Buy API is "intended for eBay partners only", applied for through EPN, no guarantee. License: displayed listing info ≤ 6 h old, other content ≤ 24 h, delete when no longer displayed, no co-mingling with non-eBay content in public display, no derived category-level averages without written permission. EPN: disclosure "unavoidable … as close to the promotional contents as possible"; collectibles 3%, $550 cap. | `www.developer.ebay.com/*.md` (the `developer.` host 403s; `www.` serves the same pages), `partnernetwork.ebay.com/*.md` |
| **Q7** | Referral rules | **Courtyard: public affiliate links not allowed** — "only for personal and non-commercial purposes … only with people you know". Phygitals' guideline page is a near-clone. Collector Crypt: no referral terms reachable. Affiliate income for the Publish lane: **none from vault platforms.** | `docs.courtyard.io/referral-program-rules.md` |
| **Q8** | Magic Eden API terms | **Unreachable** (Cloudflare challenge). ToS PDF: scraping listings without consent is a material breach; API users must follow separate API terms. Not needed: on-chain + CC API cover sale history. **Dropped.** | `magiceden.io/terms-of-service.md` |
| **Q9** | Phygitals collection addresses | Confirmed indirectly: live listings carry `collection_address` `BSG6Dy…` and Core assets move in the same transactions as the buyback USDC. | live worker run |

## Live chain results (first runs, 2026-09-26)

| Worker | Result |
|---|---|
| `onchain_courtyard` | 2,723 events from 2,000 blocks (~50 min): 1,728 `TradeExecuted` (median $23.86, max $12,267), 1,015 mints ($15/$25/$50). All USDC. Incremental run: 20 events in 1.4 s. Required: address-filtered `eth_getLogs` in chunks of 4 (registry role members), batched timestamps. |
| `onchain_collectorcrypt` | 19 flows from 40 signatures: pack purchases $25–$100 with `cc-`/`slabz-`/`jupiter-` memos, buybacks with `:buyback`. Decoder correct on first run. |
| `onchain_phygitals` | 6 buybacks with Core asset refs after fixing plain-`transfer` mint resolution; 34/40 signatures at the wallet are failed transactions (bot traffic), correctly skipped. |
| `cc_marketplace` (API) | 100 live rows; ≥ 50 cert-bearing (`gradingID`), one promo without set or cert refused. |
| `cc_gacha_odds` (API) | 87 machines; full prize pools walked for 68 (≈700 requests, 15 min at ≤2/s). Our uniform-draw EV over the full pool matches the platform's stated EV at a median ratio of **1.0000** (min 0.966 on incomplete walks). **House edge (buyback basis): quartiles 5.2% / 6.1% / 8.1%, worst ≈13.5% on $25 machines.** Machines with no inventory are excluded. |

## Soak (Phase 2 exit test, 48 h) — running in slices

The scheduler soak started 2026-09-26 01:20 UTC on the final code. Through hour 3: 150 runs, one
error (the head-race fixed at 02:10), zero lock errors after the run-row fix, 17,215 on-chain events,
498 listings, 83 packs with two hourly odds snapshots. The build container is suspended when the
session idles and background processes do not survive it (the scheduler was found stopped at 04:18
with a clean log and restarted with a fresh process table). Cursors are persisted, so chain coverage
is continuous across restarts; the three-hourly check-ins restart the scheduler. A continuous 48-hour
run without those gaps needs the owner's host: `docker compose --profile workers up`.

## Scope after the fetch pass

- **Trade lane:** Collector Crypt is fully served (floors from `insuredValue × instantBuyback`, cert identity, sales/buybacks on-chain). Courtyard contributes sales and mint volume keyed by token id, no floors. Phygitals joins when written consent lands.
- **Publish lane:** House Edge Index has an automated source (CC) and a manual one (Courtyard); Phygitals gated. Affiliate links: none from vault platforms; eBay EPN only if production access is granted.
- **Exit tests:** Phase 1 now runs on 100 real Collector Crypt slabs (single source with certs; the second cert-bearing source awaits PSA/eBay). Phase 2's replay test holds on live payloads; the 48-hour soak is running.
