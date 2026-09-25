# Data licenses register

Ground rule 3: every source we ingest gets a row here **before** its ingestion worker is written. "Derived analytics" means edges, spreads, percentages, medians we compute — never a mirror of a licensed feed.

Verification: **FETCH** = primary text read · **SNIPPET** = search snippet only · **UNKNOWN**. A worker may be built only for a row whose *Status* is `approved`; `provisional` rows may be prototyped against fixtures only.

| Source | Access path | Commercial use | Raw values public? | Derived analytics public? | Attribution | Verification | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| Polygon chain (Courtyard registry `0x251b…dcAD`, orderbook events) | public RPC | yes | yes | yes | chain + contract label | FETCH (3rd-party) | **approved** | phase0 §1 |
| Courtyard tokenURI `api.courtyard.io/index/token/…/metadata.json` | HTTPS, referenced by on-chain tokenURI | reading a tokenURI is ordinary NFT consumption; ToS anti-automation clause is SNIPPET | image/name only | yes | — | SNIPPET | **provisional** — resolve Q3; rate-limit politely | phase0 §1 |
| Courtyard `api.courtyard.io/orderbook/*`, Algolia index | undocumented, WAF-gated | — | — | — | — | SNIPPET (ToS) | **excluded** (ground rule 1) | phase0 §1 |
| OpenSea API (collection `courtyard-nft`) | official API key | per OpenSea API terms (unread) | ? | ? | ? | UNKNOWN | **provisional** | — |
| Solana chain (CC collections, marketplace program, gacha wallets) | public RPC / DAS | yes | yes | yes | chain label | FETCH (3rd-party) | **approved** | phase0 §2 |
| Collector Crypt `api.collectorcrypt.com/marketplace`, `gacha.collectorcrypt.com/api/*` | public, documented | advertised "open"; ToS unread | private dashboard only until Q1 | yes | link to CC | UNKNOWN (ToS) | **provisional** — Q1 | phase0 §2 |
| Helius DAS | API key | free tier; ToS unread | n/a (metadata) | yes | — | SNIPPET | **provisional** | research_onchain §2.3 |
| Magic Eden API (`collector_crypt` activities) | public, 120 QPM | snippet says "commercial use prohibited" — must read | no | ? | ME asks for attribution | SNIPPET | **provisional** — Q8; wind-down risk | research_onchain §2.3 |
| Solana chain (Phygitals collections, USDC wallets) | public RPC | yes | yes | yes | chain label | FETCH (3rd-party) | **approved** (confirm addresses, Q9) | phase0 §3 |
| Phygitals `api.phygitals.com/*` | public, documented on Mintlify | ToS: no automation "without explicit permission" | no | pending | — | SNIPPET | **excluded until written permission** — Q2 | phase0 §3 |
| Alt, Fanatics Collect, Card Ladder (scrape), 130point, Market Movers, Apify/Parse.bot wrappers | — | — | — | — | — | SNIPPET | **excluded** | phase0 §3, §5 |
| PSA public cert API | bearer token | End User Agreement unread | ? | ? | ? | UNKNOWN | **provisional** — Q5 | phase0 §6 |
| CGC / BGS / SGC cert lookup | web only | — | — | — | — | SNIPPET | **excluded** (no API) | phase0 §6 |
| eBay Browse API | production keyset (application pending) | yes under API License Agreement | listing data per UX rules; delete within 30 d when no longer needed; no seller PII | yes | EPN disclosure near links | SNIPPET | **provisional** — Q6 + production approval | phase0 §7 |
| eBay Marketplace Insights / sold data | — | — | — | — | — | SNIPPET | **excluded** (plan §0) | phase0 §7 |
| PriceCharting / SportsCardsPro API | subscription + commercial license | internal-use by default; public app needs written permission | no (until license says so) | no (until license says so) | link/logo under agreement | SNIPPET | **provisional** — Q4 | phase0 §5 |
| Scrydex | subscription (Growth+) | business use licensed | ? | likely, unverified | not mandated | SNIPPET | **provisional** (Pokémon fallback) | phase0 §5 |
| JustTCG | subscription | yes, explicit | yes (display) | yes, explicit | ? | SNIPPET + FETCH | **provisional** (cleanest terms) | phase0 §5 |
| Card Hedge API | subscription | ToS bars derivatives without permission | no | no (until written) | ? | SNIPPET | **provisional** (sports fallback) | phase0 §5 |
| TCGplayer API, pokemontcg.io | — | closed / deprecated | — | — | — | SNIPPET | **excluded** | phase0 §5 |

## Open license questions
Tracked as Q1–Q9 in [`phase0-findings.md`](phase0-findings.md#10-open-questions--the-spike-closes-when-these-are-fetch-grade). No row moves to `approved` on snippet evidence.
