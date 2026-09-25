# Licensed price-data candidates for graded trading cards — verification spike

Date: 2026-09-25. Scope: Pokémon + sports, graders PSA/BGS/CGC/SGC. Goal: pick a primary licensed feed and a fallback for a market-intelligence app that publishes derived analytics (spreads, percentages) and possibly raw prices.

## How to read the verification marks

- **VERIFIED-BY-FETCH** — I fetched the primary page (or an authoritative copy) and read it.
- **SEARCH-SNIPPET-ONLY** — the claim comes from search-result snippets (often the vendor's own page text, sometimes third-party write-ups). Treat exact numbers as "probably right, confirm before signing."
- **UNKNOWN** — nothing found.

**Environment caveat:** WebFetch/curl were blocked by the egress proxy for essentially every vendor domain (list at the bottom). Only github.com / raw.githubusercontent.com were fetchable. So almost everything below is SEARCH-SNIPPET-ONLY, and the search budget (200 calls) was exhausted before a few gap-fill queries could run. The terms-of-service language in particular must be re-read from the live pages before any purchase.

---

## Per-candidate findings

### 1. PriceCharting API (pricecharting.com) — SEARCH-SNIPPET-ONLY (fetch blocked)

- URLs: https://www.pricecharting.com/api-documentation , https://www.pricecharting.com/page/terms-of-service , https://www.pricecharting.com/page/methodology , https://www.pricecharting.com/pricecharting-pro
- **Coverage:** Pokémon (EN + JP), other TCGs, video games, comics, coins; sports cards are served primarily via the sister site SportsCardsPro (same company/team, same login; PriceCharting's own category list also shows Baseball/Basketball/Football). Graders on card records: PSA, BGS (incl. Black Label), CGC (incl. Pristine), SGC, TAG, ACE.
- **Graded price fields:** Yes, per grade. Snippets: "ungraded, Grade 9, and PSA 10 prices in a single call"; the full on-page ladder is Ungraded / grades 1–9.5 / PSA 10 / BGS 10 / CGC 10 / SGC 10 (+ BGS Black Label, CGC Pristine, TAG 10, ACE 10). API JSON keys "exactly match the CSV column names"; prices are integer pennies. PriceCharting reuses video-game field names for cards (e.g. a scraper notes PSA 10 arrives under `new_price`). My recollection of the doc mapping (UNVERIFIED, confirm against the sample response): `loose-price`=Ungraded, `cib-price`=Grade 7, `new-price`=Grade 8, `graded-price`=Grade 9, `box-only-price`=Grade 9.5, `manual-only-price`=PSA 10, `bgs-10-price`=BGS 10, `condition-17-price`=CGC 10, `condition-18-price`=SGC 10. A third-party note (cardorb-web docs, VERIFIED-BY-FETCH of that repo file) says "grades 1–9 with limitations on higher grades."
- **Data basis:** Sold comps — eBay completed sales + own marketplace, run through a proprietary algorithm (recent sale, median, age-weighted average, outlier removal). API/CSV return **current values only**; no sales history, no individual sold listings (snippets; the site itself shows history but the API doesn't).
- **Update frequency:** Daily; CSV refreshed by 8am EST. Values reflect ~30–90 days of sales.
- **Cost/tiers:** API requires the paid "Legendary" tier. Conflicting numbers in snippets: "$59 for 1 year" (dltHub page snippet) vs "$49/month" (tcgapi.dev comparison + cardorb-web docs). Premium (non-API) tier is $4.99/mo or $39.99/yr. **Confirm on the subscription page.** 40-character API token per subscription.
- **Rate limits:** Not published in snippets. CSV downloads limited to one every 10 minutes (SportsCardsPro doc, same platform). UNKNOWN for JSON endpoints.
- **Commercial-use / redistribution (the important part):** ToS snippets are explicit: API and CSV data are licensed for **internal use only**. "Price data cannot be used in any software, application, or system that is accessible to third parties, including customers, clients, or the general public, without express written permission." Sharing with a third party or "making it available within an application or service used by others requires a commercial license and express written permission." So the $49–59 subscription alone does **not** license a public app. Websites may "reference the price data with a link and citation to source" (editorial-style citation, not a feed).
- **Derived analytics:** Not addressed explicitly in snippets; the blanket "cannot be used in any application accessible to third parties" would, read plainly, also cover spreads/percentages computed from their data. Needs the commercial agreement.
- **Attribution:** Under a commercial agreement they "prefer" a logo or text link-back to the specific product page; for external references, a visible hyperlink and clear citation are required.
- **Verdict:** Best graded ladder in the market (all four target graders per card) and the sports sister site shares the platform, but a public-facing app **requires a negotiated commercial license**; cost UNKNOWN.

### 2. SportsCardsPro API (sportscardspro.com) — SEARCH-SNIPPET-ONLY (fetch blocked)

- URLs: https://www.sportscardspro.com/api-documentation , https://www.sportscardspro.com/page/terms-of-service , https://www.sportscardspro.com/page/methodology , https://www.sportscardspro.com/sportscardspro-premium
- **Coverage:** Sports: baseball, basketball, football, hockey, soccer, racing, wrestling, UFC, boxing; also Pokémon and Funko. Graders: PSA, BGS, SGC (SGC 10 on every card page; other SGC grades integrated), CGC (per sister-site blog "Support for CGC and SGC graded cards", June 2024).
- **Graded price fields:** PSA 10, Grade 9.5, 9, 8, 7, ungraded, plus SGC 10 / BGS 10 / CGC 10 top grades; same CSV/JSON field convention as PriceCharting ("CSV column names match the Prices API key description names").
- **Data basis:** Sold comps — "monitors every eBay sale for sports cards," assigns to card + grade, algorithmically values each grade. API/CSV: **current values only; historic prices and historic sales not supported.**
- **Update frequency:** Daily (same pipeline as PriceCharting). SEARCH-SNIPPET-ONLY.
- **Cost:** Paid subscription required (Legendary tier for CSV/API). Exact price not surfaced; likely mirrors PriceCharting. UNKNOWN.
- **Rate limits:** CSV once per 10 minutes; JSON limits UNKNOWN.
- **Commercial-use / redistribution:** Same language as PriceCharting: "Internal business purposes … not for external display or redistribution"; "cannot be used in any software, application, or system that is accessible to third parties … without express written permission."
- **Attribution:** Same as PriceCharting (link/citation; logo or text link-back under commercial agreement).
- **Verdict:** The only candidate found with a broad, per-grade, sold-comp-based sports ladder covering all four graders and a documented API — but same internal-use-only default; needs the same commercial agreement (one negotiation could plausibly cover both sister sites).

### 3. Scrydex (scrydex.com) — SEARCH-SNIPPET-ONLY + one VERIFIED-BY-FETCH third-party note

- URLs: https://scrydex.com/pricing , https://scrydex.com/terms , https://scrydex.com/docs , https://scrydex.com/docs/getting-started/api-credits
- **Coverage:** TCG only — Pokémon (EN + JP), MTG, Lorcana, One Piece, Gundam, Riftbound. **No sports cards.** Graders in graded data: PSA, BGS, CGC, SGC, TAG, ACE (per pricing snippet and cardorb-web's notes: "PSA, CGC, BGS, TAG, SGC with low/mid/high/market; also signed, error, perfect variants").
- **Graded price fields:** Per grader and grade with low/mid/high/market; daily history via `cards/<id>/price_history` (3 credits per card); webhooks on graded price change. Graded data only on Growth ($99) and Professional ($399) plans, not Starter.
- **Data basis:** "Historical sold data across eBay and other auction houses" for graded (snippet); raw prices by condition (NM/LP/MP/HP/DM) with market/low. So graded = sold comps; raw = marketplace-derived.
- **Update frequency:** Daily history; trend windows 1–180 days. Exact refresh cadence UNKNOWN.
- **Cost/tiers:** No free tier. Starter $29/mo (5,000 credits ≈160 req/day), Growth $99/mo (50,000 credits ≈1,600/day), Professional $399/mo (250,000 credits ≈8,300/day), Enterprise custom. Overage ≈$0.006 / $0.002 per credit. 1 credit per standard request (≤100 cards/page); history 3 credits/card.
- **Rate limits:** Credit-based; no hard daily AI limits but abusive patterns reviewed (ToS snippet).
- **Commercial-use / redistribution:** ToS grants a "limited, non-exclusive, non-transferable license … for personal or business purposes." tcgapi.dev's comparison says "redistribution requires written authorization." Whether displaying raw prices in a public app is "use" vs "redistribution" is not stated in snippets — needs the ToS read.
- **Attribution:** Best-practices page recommends attribution to copyright holders (images); no evidence of a mandatory price-data attribution.
- **Verdict:** Strong Pokémon graded feed with history and all four graders, real commercial plans, but zero sports coverage.

### 4. PokemonPriceTracker (pokemonpricetracker.com) — SEARCH-SNIPPET-ONLY (fetch blocked)

- URLs: https://www.pokemonpricetracker.com/pricing , https://www.pokemonpricetracker.com/psa-pokemon-card-api , https://www.pokemonpricetracker.com/docs
- **Coverage:** Pokémon only (50,000+ cards, sealed). Graders: PSA (primary), CGC, BGS, SGC sales + population reports (gem rates).
- **Graded price fields:** Per grade — "sold prices for every PSA grade," historical sales for PSA 8/9/10 from eBay completed listings; `/api/v2/population` for PSA/BGS/CGC/SGC pops; `/api/v2/cards` bundles grading stats with TCGplayer raw prices. Business tier: daily compressed CSV snapshots of prices, eBay graded sales, and population data.
- **Data basis:** Graded = eBay sold listings; raw = TCGplayer (daily). Claims "hourly for popular cards, daily otherwise."
- **Cost/tiers:** Free 100 credits/day; API $9.99/mo 20,000 credits/day; **Business $99/mo, 200,000 credits/day, 200–500 req/min (snippets disagree), commercial license, population reports, bulk CSV.**
- **Rate limits:** As above; per-minute figure inconsistent across snippets (200 vs 500).
- **Commercial-use / redistribution:** Commercial use **only** on Business. Their own developer guide says to check "if you can cache or redistribute data" and to include "required API credits and links" — implying an attribution requirement and a redistribution limit, but I could not find the actual ToS text. UNKNOWN in detail.
- **Attribution:** Likely required ("required API credits and links") — SEARCH-SNIPPET-ONLY.
- **Verdict:** Cheapest explicitly-commercial graded Pokémon feed with true per-grade eBay sold data and pops; no sports; smaller operator (concentration/continuity risk); terms not verified.

### 5. Card Ladder (cardladder.com) — SEARCH-SNIPPET-ONLY (fetch blocked)

- URLs: https://www.cardladder.com/pricing , https://www.cardladder.com/terms
- **Coverage:** Sports + TCG + non-sports; 100M+ sales from ~14 sources (eBay, Goldin, Heritage, Fanatics Collect, etc.). Graders: PSA/BGS/SGC/CGC as sale attributes.
- **Graded data:** Per-card, per-grade sales history and indices in the app; "Alt Value with confidence ranges" surfaced via a third-party wrapper (Parse.bot), not officially.
- **Data basis:** Individual sold comps (multi-venue), plus computed indices.
- **Cost:** Consumer Pro $15/mo or $150/yr; **no public developer API**. An "enterprise API for businesses and dealers" is referenced (snippets; sales-led, pricing UNKNOWN).
- **Commercial-use / redistribution:** ToS prohibits any robot/scraper/data-mining without express written consent. Parse.bot/Apify "Card Ladder APIs" are unofficial scrapers and would violate that ToS — do not use.
- **Attribution:** UNKNOWN (enterprise contract).
- **Verdict:** Excellent sports sold-comp depth but no self-serve license. Worth an enterprise inquiry; not viable for an MVP timeline.

### 6. TCGplayer API — SEARCH-SNIPPET-ONLY

- URLs: https://developer.tcgplayer.com/ , https://docs.tcgplayer.com/docs/announcements
- Status: "We are no longer granting new API access at this time" (still present Aug 2026). No graded prices anyway (raw marketplace listings/market price). **Not viable.**

### 7. Pokémon TCG API (pokemontcg.io) — SEARCH-SNIPPET-ONLY

- URL: https://docs.pokemontcg.io/
- Deprecated; new registrations closed; existing keys work through 2027-03-01. 30 req/min for third-party apps. Prices were TCGplayer/Cardmarket raw only — **no graded data. Not viable.**

### 8. JustTCG (justtcg.com) — SEARCH-SNIPPET-ONLY + VERIFIED-BY-FETCH (GitHub SDK README, card-keepr issue #426)

- URLs: https://justtcg.com/docs , https://justtcg.com/supported-games , https://justtcg.com/blog/justtcg-vs-the-alternatives-choosing-the-right-tcg-pricing-api , https://github.com/justtcg/justtcg-js
- **Coverage:** 17 TCGs (MTG, Pokémon EN/JP, Yu-Gi-Oh!, Lorcana, One Piece, Digimon, FaB, Gundam, Star Wars Unlimited, etc.). **No sports.**
- **Graded price fields:** v2 (public beta) exposes graded cards as variants with `type: 'graded'` and a `grading` object (PSA, BGS, CGC named; SGC not mentioned). v1 has no graded data. Price fields: `price`, 7d/30d/90d averages and % changes; v2 `markets[]` per region with `periods`.
- **Data basis:** "Real sales data from major online TCG marketplaces" + partner LGS in-store sales; blended value (not TCGplayer Market Price specifically). Refresh every ~6 hours (card-keepr notes). Graded source venue not stated (UNKNOWN whether eBay sold).
- **Cost/tiers:** Free (personal, 1,000 calls/mo, 20 results/req) → $19/mo (10k) → Professional $49/mo (50k/mo, 5k/day, 100 results/req) → Enterprise $149/mo (500k/mo, 200 results/req). Numbers from tcgapi.dev + card-keepr; consistent.
- **Commercial-use / redistribution:** Best-documented terms of the group: every paid plan carries a commercial license to "display prices to your users, calculate derived analytics and valuations, cache and store price history while subscribed, and combine data with other lawful sources." Prohibited: reselling/redistributing the raw feed as a standalone feed, publishing bulk dataset exports, building a competing pricing API. Terminable for any reason.
- **Attribution:** Not surfaced as mandatory in snippets — UNKNOWN; check ToS.
- **Verdict:** Cleanest license for derived analytics, but graded is beta, SGC unclear, no sports.

### 9. Collectr (getcollectr.com) — SEARCH-SNIPPET-ONLY (fetch blocked)

- URLs: https://getcollectr.com/api , https://getcollectr.com/api-terms-and-conditions.html
- **Coverage:** TCGs (Pokémon, MTG, YGO, One Piece, Lorcana…) — 400,000+ products incl. raw, sealed, graded. Sports: not evident (UNKNOWN, likely none).
- **Graded data:** price history with `grading_company`, `grade_label`, `grade_value`, `market_price`, `graded_sub_types` (described by a Parse.bot wrapper, which is unofficial). Data basis appears to be marketplace-derived "market price" rather than individual sold comps — UNKNOWN.
- **Cost:** Official API exists but access is granted "at Collectr's sole discretion" on application; pricing not published (UNKNOWN). API terms explicitly ban scraping and obtaining Collectr-derived data from third parties (so Parse.bot/Apify wrappers are off-limits).
- **Redistribution/attribution:** UNKNOWN (api-terms page blocked).

### 10. Market Movers / Sports Card Investor — SEARCH-SNIPPET-ONLY (fetch blocked)

- URLs: https://www.marketmoversapp.com/ , https://www.marketmoversapp.com/terms-of-use
- Consumer tool ($9.99/mo+), 2M+ sports cards + TCG, multi-marketplace sold data. **No public API.** ToS allows only one screenshot repost per instance, max 3 per 24h, non-commercial, with SCI credited — i.e., explicitly hostile to redistribution. **Not viable** short of a bespoke deal.

### 11. 130point — SEARCH-SNIPPET-ONLY

- URLs: https://130point.com/ , terms: https://130point.com/130-point-mobile-application-terms-and-condition-of-use/
- Free sold-listing search over eBay, Goldin, Heritage, Fanatics/PWCC, MySlabs, Pristine (15M+ sold items). **No official API or data license**; the "130point API" on Parse.bot is an unofficial scraper. Data is per-sale (title/price/date/venue), not per-grade values — you'd have to parse grades yourself. **Not licensable as-is.**

### 12. Alt (alt.xyz) — VERIFIED-BY-FETCH (api-evangelist profile on GitHub) + snippets

- URLs: https://alt.xyz/ , https://www.alt.xyz/blog/how-alt-value-works , https://github.com/api-evangelist/alt
- "Alt Value" ML valuation for PSA/BGS/SGC (sports-heavy, some Pokémon). "As of 2026-08-02 there is no developer portal, API reference, … or self-service API." **Not available.**

### 13. Others found

- **Card Hedge API (cardhedger.com)** — SEARCH-SNIPPET-ONLY. https://ai.cardhedger.com/api-services , https://api.cardhedger.com/docs , https://www.cardhedger.com/price_api_business , https://ai.cardhedger.com/terms . Sports + Pokémon/YGO/MTG + pop culture; 3.5M+ cards; comps, price history, valuations for PSA/BGS/SGC/CGC/TAG/raw; sources eBay, Fanatics, Heritage; slab-image cert/grade detection; OpenAPI + MCP. Plans "from $49/month," 7-day trial. ToS snippet: "may not reproduce, distribute, modify, or create derivative works without express written permission" — that boilerplate, if it applies to API output, would block derived analytics without a written agreement. Attribution UNKNOWN. **Most interesting sports+Pokémon single-vendor option; needs a terms conversation.**
- **TCG Price Lookup (tcgpricelookup.com)** — SEARCH-SNIPPET-ONLY. https://tcgpricelookup.com/tcg-api . 8 TCGs (no sports); graded block for PSA/BGS/CGC/SGC/ACE/TAG grades 1–10 from eBay sold slabs, rolling 1/7/30-day averages; Free (10k req/mo, TCGplayer raw only, non-commercial) / Trader $14.99/mo (10k req/day, 1 rps, graded + eBay + history, commercial) / Business $89.99/mo (100k/day, 3 rps). Attribution: none required for server-side use; optional on Business. Explicitly lists "graded-card analytics products" as a permitted commercial use. Redistribution limits not surfaced. Young vendor.
- **CardSight AI (cardsight.ai)** — SEARCH-SNIPPET-ONLY. Sports + TCG identification + "real card sales data and graded card pricing sourced from eBay, Fanatics Collect, COMC," organized by grader (PSA/BGS/SGC/CGC) and grade, bulk 100 cards/request; free tier 750 calls/mo; paid pricing and terms UNKNOWN.
- **GemRate API (docs.gemrate.com, gemrate.com/partner)** — pops/cert/universal IDs across PSA/BGS/SGC/CGC, daily; sales trends exist on the site but the API is pop/cert-centric; partner pricing UNKNOWN. Useful as an ID/pop layer, not a price feed.
- **PSA Public API** — cert lookup only; free tier cut to ~1 call/day mid-2026; APR/price guide not in the API. Not a price feed.
- **eBay Marketplace Insights API** — the only official eBay sold-data API; closed to new applicants (partner-only). Not obtainable.
- **Fanatics Collect / Goldin / Heritage** — public sales-history pages, no licensed feed; only scrapers exist.
- **tcgapi.dev, TCGAPIs (£199–499/mo), PokéTrace, tcgfast** — raw TCG market prices; no evidence of per-grade graded data; tcgapi.dev's terms page 404s (card-keepr note). Not shortlisted.

---

## Comparison table

| Candidate | Pokémon | Sports | Graders w/ per-grade prices | Data basis | Update | Entry cost for commercial use | Rate limits | Public-app display OK? | Derived analytics OK? | Attribution | Verification |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PriceCharting | Yes | Partial (sister site) | PSA/BGS/CGC/SGC/TAG/ACE 10 + grades 1–9.5 | eBay sold comps → algorithmic value (current only) | Daily | $49/mo or $59/yr sub (conflicting) **+ negotiated commercial license** | Unpublished; CSV 1/10 min | **No without written permission** | Not addressed; assume no without license | Link/citation; logo/link under agreement | SNIPPET |
| SportsCardsPro | Yes | **Yes (all majors)** | PSA 7–10, BGS 9.5/10, SGC 10, CGC 10 | eBay sold comps → value (current only) | Daily | Legendary sub (price UNKNOWN) **+ commercial license** | CSV 1/10 min | **No without written permission** | Same as above | Same as above | SNIPPET |
| Scrydex | Yes | No | PSA/BGS/CGC/SGC/TAG/ACE, low/mid/high/market + history | eBay + auction sold data (graded) | Daily | Growth $99/mo (graded tier) | Credits: 50k/mo ≈1,600/day | Business use licensed; "redistribution needs written auth" | Likely OK (unverified) | Not mandated for prices (unverified) | SNIPPET + 3rd-party fetch |
| PokemonPriceTracker | Yes | No | PSA all grades; CGC/BGS/SGC sales + pops | eBay sold listings; TCGplayer raw | Daily (hourly for hot cards) | Business $99/mo | 200k credits/day; 200–500 rpm | Yes (Business) | Unverified; "check if you can redistribute" | "Required API credits and links" (likely) | SNIPPET |
| JustTCG | Yes | No | PSA/BGS/CGC (v2 beta); SGC unclear | Blended marketplace sales; ~6h refresh | ~6h | $19/mo (any paid plan) | 10k–500k/mo | **Yes, explicit** | **Yes, explicit** ("derived analytics and valuations") | Unverified | SNIPPET + GitHub fetch |
| TCG Price Lookup | Yes | No | PSA/BGS/CGC/SGC/ACE/TAG 1–10 | eBay sold slabs, 1/7/30d averages | Continuous | Trader $14.99/mo | 10k/day, 1 rps | Yes (commercial on Trader+) | Named as permitted use | None server-side; optional | SNIPPET |
| Card Hedge API | Yes | **Yes** | PSA/BGS/SGC/CGC/TAG comps + history | eBay/Fanatics/Heritage sold comps | Live | From $49/mo | Unpublished | Unclear — ToS bars distribution/derivatives w/o permission | Unclear | Unknown | SNIPPET |
| CardSight AI | Yes | **Yes** | PSA/BGS/SGC/CGC by grade | eBay/Fanatics/COMC sold + live | Unknown | Free 750/mo; paid UNKNOWN | Unknown | Unknown | Unknown | Unknown | SNIPPET |
| Card Ladder | Yes | Yes | Sales-level, all graders | Multi-venue sold comps | Daily | Enterprise API only (sales-led) | n/a | Only via enterprise contract; scraping banned | Contract | Contract | SNIPPET |
| Collectr | Yes | Unlikely | By grading_company/grade | Market price (basis unclear) | Unknown | Application-gated; price UNKNOWN | Credits/call | Unknown | Unknown | Unknown | SNIPPET |
| Market Movers | Yes | Yes | App only | Multi-venue sold | Daily | No API | n/a | No (3 screenshots/day non-commercial) | No | SCI credit | SNIPPET |
| 130point | Yes | Yes | Raw sold listings | eBay+auction houses | Live | No license/API | n/a | No | No | n/a | SNIPPET |
| Alt | Some | Yes | Alt Value (PSA/BGS/SGC) | ML model | Live | No API | n/a | No | No | n/a | FETCH (3rd-party) |
| TCGplayer API | Yes | No | None | Marketplace | — | Closed to new devs | — | — | — | — | SNIPPET |
| pokemontcg.io | Yes | No | None | TCGplayer/Cardmarket raw | — | Deprecated (keys die 2027-03-01) | 30 rpm | — | — | — | SNIPPET |

---

## Recommendation

The requirement set (Pokémon **and** sports, PSA/BGS/CGC/SGC, per-grade values, publishable derived analytics) is not satisfied by any single self-serve product with verified terms. Two realistic architectures:

### (a) Primary licensed feed

**PriceCharting + SportsCardsPro under one negotiated commercial license.** Rationale: it is the only pair with a complete per-grade ladder (PSA/BGS/CGC/SGC 10 plus PSA 7–9.5) across both Pokémon and every major sport, computed from eBay sold comps, delivered as daily JSON/CSV with stable field names. The blocker is contractual, not technical: the standard subscription is internal-use-only and public display requires "express written permission." Action items before committing: (1) email PriceCharting for commercial-license pricing and ask explicitly whether **derived metrics (spreads, % premiums, rankings) and raw per-grade prices** may be shown to end users; (2) confirm the actual per-grade JSON keys against the doc sample response (the field-name mapping above is from memory); (3) confirm rate limits for the JSON endpoints; (4) note the feed has no history — the app must snapshot daily to build its own time series (check the license permits storing snapshots).

If the negotiated price is unreasonable or they refuse derived-analytics display, the runner-up primary for a **Pokémon-first launch** is **Scrydex Growth ($99/mo)** (all four graders, low/mid/high/market, daily history, webhooks), with **JustTCG** as the cleaner-licensed but thinner-graded alternative. Neither covers sports.

### (b) Fallback

**Card Hedge API (from $49/mo)** as the cross-vertical fallback: it is the one self-serve API found that covers sports **and** Pokémon with PSA/BGS/SGC/CGC comps, price history and cert/slab lookup, sourced from eBay/Fanatics/Heritage sold data. Caveat: its site ToS boilerplate bars distribution and derivative works "without express written permission" — get written confirmation that API-plan customers may display prices and derived analytics. For Pokémon-only redundancy, **TCG Price Lookup Trader ($14.99/mo)** or **PokemonPriceTracker Business ($99/mo)** are cheap second sources (both eBay-sold-slab based, all four graders, commercial tiers; PPT explicitly wants attribution links).

### Things to avoid

- Any Apify / Parse.bot "API" for PriceCharting, SportsCardsPro, Card Ladder, Collectr, 130point, PSA, Fanatics, Goldin — these are scrapers and the target sites' terms prohibit them; they also void the "licensed" premise of the app.
- TCGplayer and pokemontcg.io (closed/deprecated, no graded data).
- Treating eBay Marketplace Insights as an option (partner-only).

### Honest uncertainty

- Every vendor's terms and pricing above are from search snippets; the ToS pages must be read in full (esp. PriceCharting/SportsCardsPro, Scrydex, PokemonPriceTracker, Card Hedge, JustTCG) before any of the "derived analytics OK?" cells are relied on.
- PriceCharting API price ($49/mo vs $59/yr) and PPT per-minute limit (200 vs 500) were inconsistent across sources.
- SGC support in JustTCG v2 and Card Hedge's exact plan tiers/limits are unconfirmed.
- Search budget (200 queries) was exhausted before I could re-query the PriceCharting field mapping, SportsCardsPro Legendary price, CardSight pricing, and JustTCG attribution language.

---

## Hosts I tried to fetch that were blocked (EGRESS_BLOCKED / proxy CONNECT 403)

- www.pricecharting.com
- blog.pricecharting.com
- www.sportscardspro.com
- scrydex.com
- www.pokemonpricetracker.com
- justtcg.com
- www.cardladder.com
- getcollectr.com
- www.marketmoversapp.com
- cardsight.ai
- ai.cardhedger.com
- www.cardhedger.com
- api.cardhedger.com
- docs.gemrate.com
- docs.pokemontcg.io
- developer.tcgplayer.com
- www.psacard.com
- tcgpricelookup.com
- tcgapi.dev
- tcgapis.com
- tcgfast.com
- poketrace.com
- www.scrapingbee.com
- cardgrader.ai
- context7.com
- dlthub.com
- medium.com

Fetchable: github.com and raw.githubusercontent.com (used for deansasek/pricecharting-api, justtcg/justtcg-js, api-evangelist/alt, KeeprDigital/card-keepr issue #426, bartdunweg/cardorb-web docs/prices.md).

## Sources (search results and fetched pages)

- https://www.pricecharting.com/api-documentation
- https://www.pricecharting.com/page/terms-of-service
- https://www.pricecharting.com/page/methodology
- https://www.pricecharting.com/pricecharting-pro
- https://blog.pricecharting.com/2024/06/support-for-cgc-and-sgc-graded-cards.html
- https://www.sportscardspro.com/api-documentation
- https://www.sportscardspro.com/page/terms-of-service
- https://www.sportscardspro.com/page/methodology
- https://scrydex.com/pricing , https://scrydex.com/terms , https://scrydex.com/docs
- https://github.com/bartdunweg/cardorb-web (docs/prices.md)
- https://www.pokemonpricetracker.com/pricing , https://www.pokemonpricetracker.com/psa-pokemon-card-api
- https://justtcg.com/ , https://justtcg.com/docs , https://justtcg.com/supported-games , https://github.com/justtcg/justtcg-js
- https://github.com/KeeprDigital/card-keepr/issues/426
- https://tcgapi.dev/blog/trading-card-game-apis-compared/ , https://tcgapi.dev/compare/justtcg/
- https://cardgrader.ai/blog/tcgplayer-api-alternatives
- https://www.scrapingbee.com/blog/pokemon-card-api/
- https://www.cardladder.com/pricing , https://www.cardladder.com/terms
- https://getcollectr.com/api , https://getcollectr.com/api-terms-and-conditions.html
- https://www.marketmoversapp.com/terms-of-use
- https://130point.com/130-point-mobile-application-terms-and-condition-of-use/
- https://github.com/api-evangelist/alt , https://www.alt.xyz/blog/how-alt-value-works
- https://ai.cardhedger.com/api-services , https://ai.cardhedger.com/terms , https://www.cardhedger.com/price_api_business
- https://tcgpricelookup.com/tcg-api
- https://cardsight.ai/ , https://cardsight.ai/solutions/price-data
- https://docs.gemrate.com/introduction , https://www.gemrate.com/partner
- https://www.psacard.com/publicapi , https://cardgrader.ai/blog/psa-api
- https://developer.tcgplayer.com/ , https://docs.pokemontcg.io/
- https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/Access-to-sold-completed-listing-data-what-options-do-non/m-p/35398955
