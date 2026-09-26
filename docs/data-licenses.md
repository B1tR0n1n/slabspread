# Data licenses register

Ground rule 3: every source we ingest gets a row here **before** its ingestion worker is written. "Derived analytics" means edges, spreads, percentages, medians we compute — never a mirror of a licensed feed.

Verification: **FETCH** = primary text read · **SNIPPET** = search snippet only · **UNKNOWN**. A worker may be built only for a row whose *Status* is `approved`; `provisional` rows may be prototyped against fixtures only.

| Source | Access path | Commercial use | Raw values public? | Derived analytics public? | Attribution | Verification | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| Polygon chain (Courtyard registry `0x251b…dcAD`, orderbook events) | public RPC | yes | yes | yes | chain + contract label | FETCH (3rd-party) | **approved** | phase0 §1 |
| Courtyard tokenURI `api.courtyard.io/index/token/…` | HTTPS | ToS §14.8/§14.11; endpoint returns 403 | — | — | — | FETCH | **excluded** | phase0 fetch pass Q3 |
| Courtyard `api.courtyard.io/orderbook/*`, Algolia, pack config JSON | undocumented / page-loaded | ToS §14.8 | — | odds via owner's manual snapshot (`/admin/odds`, provenance `manual_snapshot`) | — | FETCH | **excluded from automation** | phase0 fetch pass Q3 |
| OpenSea API (collection `courtyard-nft`) | official API key | per OpenSea API terms (unread) | ? | ? | ? | UNKNOWN | **provisional** | — |
| Solana chain (CC collections, marketplace program, gacha wallets) | public RPC / DAS | yes | yes | yes | chain label | FETCH (3rd-party) | **approved** | phase0 §2 |
| Collector Crypt `api.collectorcrypt.com/marketplace`, `gacha.collectorcrypt.com/api/*` | public, documented; UA required; 300/min per IP | docs: no credential needed; ToS §4.6(viii)/(xi) bar commercial exploitation / competing service — derived analytics only, written confirmation before Phase 6 | private dashboard only | yes | link to CC | FETCH | **approved (private + derived)** — email support@collectorcrypt.com for key + written commercial confirmation | phase0 fetch pass Q1 |
| Helius DAS | API key | free tier; ToS unread | n/a (metadata) | yes | — | SNIPPET | **provisional** | research_onchain §2.3 |
| Magic Eden API (`collector_crypt` activities) | — | API terms unreachable; ToS bars scraping listings | — | — | — | FETCH (ToS) | **dropped** — not needed | phase0 fetch pass Q8 |
| Solana chain (Phygitals collections, USDC wallets) | public RPC | yes | yes | yes | chain label | FETCH (3rd-party) | **approved** (confirm addresses, Q9) | phase0 §3 |
| Phygitals `api.phygitals.com/*` | public, documented; no key for GETs | ToS §11: automation needs *written* consent; docs invite "price-comparison tooling" | no | pending | — | FETCH | **built, gated** — on after written consent (Q2) | phase0 fetch pass Q2 |
| Alt, Fanatics Collect, Card Ladder (scrape), 130point, Market Movers, Apify/Parse.bot wrappers | — | — | — | — | — | SNIPPET | **excluded** | phase0 §3, §5 |
| PSA public cert API | OAuth2 password grant | End User Agreement behind sign-in; rate limit undocumented | ? | ? | ? | FETCH (docs) / UNKNOWN (EUA) | **provisional** — Q5 | phase0 fetch pass Q5 |
| CGC / BGS / SGC cert lookup | web only | — | — | — | — | SNIPPET | **excluded** (no API) | phase0 §6 |
| eBay Browse API | production keyset via EPN application ("intended for eBay partners only") | listing info ≤ 6 h stale in display, delete when not displayed, no co-mingling in public display, no category-level averages without permission | listing data per UX rules | yes (private); public derived only with care | EPN disclosure adjacent to links; 3% collectibles | FETCH | **provisional** — production approval + design note: `conditionDescriptors` only via `getItem` | phase0 fetch pass Q6 |
| eBay Marketplace Insights / sold data | — | — | — | — | — | SNIPPET | **excluded** (plan §0) | phase0 §7 |
| PriceCharting / SportsCardsPro API | Legendary subscription | "licensed for internal use only … making it available within an application or service used by others requires a commercial license and express written permission"; 1 call/s; cache allowed, purge after | no | no (until written) | citation + link | FETCH (PC) / UNREACHABLE (SCP) | **provisional** — Q4 email | phase0 fetch pass Q4 |
| Scrydex | subscription (all tiers include graded) | §4 no resale/redistribution/"substitute backend"; §9 nothing granted by implication | ? | unaddressed | not mandated | FETCH | **provisional** — ask in writing | phase0 fetch pass Q4 |
| JustTCG | paid tier, `x-api-key` | §7.1: end-user display, derived analytics, caching, combination permitted; §7.3 no raw redistribution; free tier non-commercial | yes (display) | yes, explicit | appreciated, not required | FETCH | **approved on subscription** (Pokémon/TCG only) | phase0 fetch pass Q4 |
| Card Hedge API | subscription | ToS bars derivatives without permission | no | no (until written) | ? | SNIPPET | **provisional** (sports fallback) | phase0 §5 |
| TCGplayer API, pokemontcg.io | — | closed / deprecated | — | — | — | SNIPPET | **excluded** | phase0 §5 |

## Open license questions
Resolved in the 2026-09-26 fetch pass except Q4 (vendor written permission), Q5 (PSA EUA) and Q6 (eBay production). Tracked as Q1–Q9 in [`phase0-findings.md`](phase0-findings.md#10-open-questions--the-spike-closes-when-these-are-fetch-grade). No row moves to `approved` on snippet evidence.
