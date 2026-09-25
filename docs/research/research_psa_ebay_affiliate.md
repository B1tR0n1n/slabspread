# Verification spike: PSA cert API, eBay Browse API / EPN, pack-platform affiliate programs

Date: 2026-09-25. Method: WebSearch (snippets) + WebFetch where the egress proxy allowed it. Evidence labels:
- **VERIFIED-BY-FETCH** = page body actually retrieved and read (only a handful of hosts were reachable).
- **SEARCH-SNIPPET-ONLY** = claim comes from a search-engine snippet / summary of the page; primary page NOT fetched.
- **UNKNOWN** = could not confirm either way.

Overall caveat: almost every primary source (psacard.com, api.psacard.com, developer.ebay.com, partnernetwork.ebay.com, community.ebay.com, docs.courtyard.io, docs.phygitals.com, docs.collectorcrypt.com, ftc.gov, ecfr.gov, federalregister.gov) was blocked by the egress proxy. Treat everything below as "highly likely but needs a 10-minute manual confirmation in a browser before it goes into a spec."

---

## 1. PSA public cert verification API

### 1.1 Getting a token
- Free psacard.com account -> https://www.psacard.com/publicapi -> generate an access token. Bearer-token auth (`Authorization: bearer <token>`), no OAuth. Tokens do not expire but can be regenerated from the PSA site.
  - Sources: https://www.psacard.com/publicapi/documentation (SEARCH-SNIPPET-ONLY, host blocked); https://github.com/maccann-24/sports-card-research/blob/master/02-PSA-API.md (VERIFIED-BY-FETCH via raw.githubusercontent.com); https://forums.collectors.com/discussion/1123788/psa-api (SEARCH-SNIPPET-ONLY).
- The docs page references a "PSA API End User Agreement" that you accept when generating the token. Text of the agreement NOT obtained. Sources: https://github.com/brad-newman/fetch-psa-api (VERIFIED-BY-FETCH, README says "PSA API End User Agreement"); search snippet of https://www.psacard.com/publicapi/documentation (SEARCH-SNIPPET-ONLY).

### 1.2 Endpoints (base `https://api.psacard.com/publicapi`)
- `GET /cert/GetByCertNumber/{certNumber}` — primary cert lookup.
- `GET /cert/GetImagesByCertNumber/{certNumber}` — front/back images (images only exist for items graded after ~Oct 2021 per brad-newman README).
- `GET /cert/GetByCertNumberForFileAppend/{certNumber}` — variant for bulk/file use.
- Swagger UI: https://api.psacard.com/publicapi/swagger/ui/index (blocked; SEARCH-SNIPPET-ONLY).
- Also listed at https://apis.io/apis/collectors/collectors-psa-public-api-methods-api/ (SEARCH-SNIPPET-ONLY).
- Sources: maccann-24 research doc (VERIFIED-BY-FETCH); https://www.psacard.com/publicapi/documentation (SEARCH-SNIPPET-ONLY).

### 1.3 Response fields
Response envelope: `{ "PSACert": {...}, "IsValidRequest": bool, "ServerMessage": string }`. Note HTTP 200 is returned even for invalid certs; check `IsValidRequest`. (VERIFIED-BY-FETCH from maccann-24 doc; also SEARCH-SNIPPET-ONLY from https://cardgrader.ai/blog/psa-api and https://tcgapis.com/psa-checker.)

`PSACert` fields (from the doc's sample JSON, SEARCH-SNIPPET-ONLY / secondary): `CertNumber`, `SpecID` (mentioned in snippets), `SpecNumber`?, `CardNumber`, `YearIssued`, `Brand`, `Variety`, `Subject`, `Category`, `CardGrade`, `AutographGrade`, `TotalPopulation`, `PopulationHigher`, `SpecAttr`, `LabelType`, `CardAttributes`, `ImageURL`, `IsFlagship`. There is also a separate `DNACert` object for autograph/DNA items (VERIFIED-BY-FETCH, brad-newman README: "only parses the PSACert object, not the DNACert object").

**Important:** multiple secondary sources say `TotalPopulation` / `PopulationHigher` come back **null** in public-API responses — i.e., the public API does NOT give you pop data despite the field names (VERIFIED-BY-FETCH in maccann-24 doc: "Population fields ... return as null in all public API responses"; echoed by cardgrader.ai snippet). Treat pop as UNAVAILABLE from this API until you test with a real token. There's no "set" field per se — set is a composite of `YearIssued` + `Brand` + `Variety` (+ `Category`). No pricing data.

### 1.4 Rate limits — CONFLICTING evidence
- Long-standing documented free-tier limit: **100 calls/day**, HTTP 429 when exceeded, no rate-limit headers. Sources: maccann-24 doc (VERIFIED-BY-FETCH, dated as current as of Aug 2026 per search snippet); https://forums.collectors.com/discussion/1123788/psa-api (SEARCH-SNIPPET-ONLY); https://cardgrader.ai/blog/psa-api (SEARCH-SNIPPET-ONLY).
- One search-engine summary (from the query "PSA publicapi ... daily call limit") stated: "As of mid-2026, PSA reduced their public API to approximately 1 call per day for both anonymous and free registered tokens, so cert/specID lookups now require a paid PSA API plan," with paid plans via collectors-apis@collectors.com. I could NOT find a primary source or a second independent source for this; a follow-up search specifically for "1 call per day" found nothing. **Status: UNKNOWN / unconfirmed.** Must be tested empirically with a fresh token before designing around 100/day.
- Paid/enterprise tier: "contact PSA (collectors-apis@collectors.com), pricing undisclosed" (maccann-24, VERIFIED-BY-FETCH; the email itself was redacted in the fetched markdown, so the exact address is SEARCH-SNIPPET-ONLY).

### 1.5 Terms on storing / displaying / redistributing
- UNKNOWN in detail. cardgrader.ai snippet: "the terms govern how you may store and display the data — read them before caching aggressively" (SEARCH-SNIPPET-ONLY). The actual End User Agreement text was not retrievable. Action item: log in, generate a token, and copy the agreement text into the repo docs before building a cache layer.

### 1.6 Other graders (CGC / BGS / SGC)
- **CGC Cards:** public web lookup only (https://www.cgccards.com/certlookup/). CGC forum threads from developers asking for an API exist (https://boards.cgccomics.com/topic/541624-api-for-accessing-card-and-image-data-from-cert-number/ , https://boards.cgccomics.com/topic/529622-personal-app-developer-looking-for-api-access-understanding/) with no evidence of an official public API (SEARCH-SNIPPET-ONLY; boards host blocked so staff replies not read). CGC does have an *affiliate* program page (https://www.cgccards.com/affiliates/, SEARCH-SNIPPET-ONLY) — unrelated to data access.
- **BGS / Beckett:** web lookup only (https://www.beckett.com/grading/card-lookup). No official API found; only third-party scrapers (e.g., Apify "Beckett BGS Pop Report & Price Guide" actor). SEARCH-SNIPPET-ONLY.
- **SGC:** web lookup only (https://www.gosgc.com/cert-code-lookup; 7-digit or XXXXXXX-XXX codes) plus the SGC mobile app. No official API found. SEARCH-SNIPPET-ONLY.
- Third parties (cardgrade.io, checkcoa.com, tcgapis.com, parse.bot, Apify actors) wrap these lookups by scraping; using them is a ToS/robustness risk, not an official channel.

---

## 2. eBay Browse API + Marketplace Insights + EPN + license terms

### 2.1 Application / keyset / production access
- Anyone with an eBay developer account gets a sandbox keyset and can call Buy APIs (incl. Browse) in **sandbox**. **Production** use of the Buy APIs is restricted: you must meet eligibility, get approval, and sign eBay's contracts; you apply through an **Application Growth Check** with subject line like "Buy API Production Access (eBay user ID)", including your **EPN-registered eBay user ID**, sandbox test instructions, and the **EPN approval email** as an attachment. Acceptance depends on the proposed business model.
  - Sources: https://developer.ebay.com/api-docs/buy/static/buy-requirements.html ; https://developer.ebay.com/develop/get-started/get-started-on-a-buying-application ; https://community.ebay.com/forum/ebay-developers-program-57950/topic/approved-method-for-accessing-soldcompleted-listing-data-for-sell-through-research-468863/ (all SEARCH-SNIPPET-ONLY, hosts blocked).
- All Browse methods use an **Application (client-credentials) access token** (SEARCH-SNIPPET-ONLY, https://developer.ebay.com/api-docs/buy/browse/overview.html).
- Sandbox vs production: sandbox search "is only supported using mock data" and commonly returns 0 results; devs are told to test search against production. Prod URL `https://api.ebay.com/buy/browse/v1/item_summary/search`, sandbox `https://api.sandbox.ebay.com/...`. Sources: https://community.ebay.com/t5/RESTful-Buy-APIs-Browse/Sandbox-API-always-returns-0-results/td-p/33675543 ; https://forums.developer.ebay.com/questions/48870/sandbox-browse-api-not-providing-results-for-some.html (SEARCH-SNIPPET-ONLY).

### 2.2 Rate limits
- Default **5,000 calls/day per application keyset** for the Browse API (application-level, not per user). Raise via the free Application Growth Check. Monitor with Developer Analytics API `getRateLimits` / `getUserRateLimits`.
  - Sources: https://developer.ebay.com/develop/get-started/api-call-limits ; https://forums.developer.ebay.com/questions/15794/how-can-i-have-more-ebay-api-calls-the-limit-which.html ; https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/About-API-limit-calls/td-p/34671615 ; https://developer.ebay.com/api-docs/developer/analytics/resources/user_rate_limit/methods/getUserRateLimits (all SEARCH-SNIPPET-ONLY).
- `item_summary/search` returns at most 10,000 items per query (VERIFIED-BY-FETCH from a third-party mirror of eBay's Browse OpenAPI spec: https://github.com/michabbb/sdk-ebay-rest-browse/blob/master/buy_browse_v1_beta_oas3.yaml — note this is an older *beta* spec mirror, not eBay's live doc).

### 2.3 Category IDs and graded-slab filters
- Trading-card leaf categories: **261328** Sports Trading Card Singles, **183454** CCG Individual Cards (Pokemon/MTG/etc.), **183050** Non-Sport Trading Card Singles.
- Since Oct 23 2023 listings in those categories must use condition **2750 = Graded** or **4000 = Ungraded**. Under 2750, condition descriptors: **27501 Professional Grader**, **27502 Grade**, **27503 Certification Number** (optional).
  - Sources: https://developer.ebay.com/api-docs/user-guides/static/mip-user-guide/mip-enum-condition-descriptor-ids-for-trading-cards.html ; https://developer.ebay.com/updates/newsletter/q3_2023 ; https://community.ebay.com/t5/Seller-Tools/How-to-update-Card-Condition-requirements-for-eBay-2023/td-p/34037857 (SEARCH-SNIPPET-ONLY).
- Browse API: `getItem` / `getItemByLegacyId` / `getItemsByItemGroup` return a `conditionDescriptors` array, e.g. `[{"name":"Professional Grader","values":[{"content":"Professional Sports Authenticator (PSA)"}]},{"name":"Grade","values":[{"content":"10"}]}]` (SEARCH-SNIPPET-ONLY: https://developer.ebay.com/updates/newsletter/q4_2023 , https://developer.ebay.com/api-docs/buy/browse/resources/item/methods/getItem). Cert number descriptor should also surface here when the seller filled it in — UNKNOWN whether `item_summary/search` (vs `getItem`) returns it; the beta spec mirror I fetched predates conditionDescriptors entirely.
- Search-side filtering: community thread https://community.ebay.com/t5/RESTful-Buy-APIs-Browse/Searching-for-PSA-10-graded-cards-only-in-the-Pokemon-TCG/td-p/34789291 (SEARCH-SNIPPET-ONLY) discusses `aspect_filter=categoryId:183454,conditionDescriptors.name:Professional Grader,conditionDescriptors.values.content:Professional Sports Authenticator,conditionDescriptors.name:Grade,conditionDescriptors.values.content:10` style filtering, with reports that grade filtering is imprecise. `aspect_filter` requires `categoryId:` inside the filter AND `category_ids=` as a URI param (VERIFIED-BY-FETCH from the spec mirror). Use `fieldgroups=ASPECT_REFINEMENTS` to discover valid aspect names/values for a category (VERIFIED-BY-FETCH, spec mirror). Exact accepted syntax for condition descriptors in `aspect_filter` is SEARCH-SNIPPET-ONLY — test in production.
- Additional `filter=conditionIds:{2750}` should restrict to graded listings (inference from condition IDs above; UNKNOWN if verified in Browse docs).

### 2.4 Marketplace Insights API (sold data)
- Confirmed **Limited Release, "restricted and not open to new users at this time"**; requires business-unit approval and the `buy.marketplace.insights` scope; returns last 90 days of sales. Finding API (`findCompletedItems`) was restricted in 2020, deprecated Jan 2024, decommissioned Feb 2025.
  - Sources: https://developer.ebay.com/api-docs/buy/static/ref-marketplace-supported.html ; https://developer.ebay.com/develop/api/buy/marketplace-insights_api ; https://community.ebay.com/forum/talk-to-your-fellow-developers-57970/topic/marketplace-insights-api-access-168586/ ; https://scavio.dev/blog/ebay-sold-listings-api-login-wall-2026 ; https://sold-comps.com/alternatives (all SEARCH-SNIPPET-ONLY).
- Practical implication: no official sold-comps feed for a new app. Alternatives are third-party sold-data vendors (scraped — ToS risk) or building your own price history from active-listing snapshots + observed end states.

### 2.5 EPN affiliate links from Browse API results
- Pass request header `X-EBAY-C-ENDUSERCTX: affiliateCampaignId=<10-digit EPN campaign id>,affiliateReferenceId=<optional, <=256 chars>` on Browse calls; the response then includes `itemAffiliateWebUrl`, and EPN affiliates **must** use that URL to forward buyers in order to earn commission. `itemAffiliateWebUrl` is "only returned if the eBay partner enables affiliate tracking for the item by including the X-EBAY-C-ENDUSERCTX request header" (VERIFIED-BY-FETCH from spec mirror; header semantics SEARCH-SNIPPET-ONLY from https://developer.ebay.com/api-docs/buy/static/api-browse.html and https://developer.ebay.com/api-docs/buy/browse/types/gct:ItemSummary).
- Tracking link anatomy (if you build your own): `{target}&mkevt=1&mkcid=1&mkrid={rotation id}&campid={EPN campaign ID}&toolid={tool id}&customid={sub id}` (SEARCH-SNIPPET-ONLY, https://developer.ebay.com/api-docs/buy/static/ref-epn-link.html).
- EPN economics (SEARCH-SNIPPET-ONLY): 24-hour click cookie; rate card is % of sale by region/sub-category, typically 1-4%; a German EPN page shows trading cards at 3% (https://partnernetwork.ebay.de/page/trading-cards). US trading-card rate: check https://partnernetwork.ebay.com/our-program/rate-card and https://partnernetwork.ebay.com/page/trading-cards (both blocked).
- **EPN disclosure rules** (SEARCH-SNIPPET-ONLY from https://partnernetwork.ebay.com/resources/affiliate-disclosure-faq and https://partnernetwork.ebay.com/page/network-agreement): Network Agreement Section I.G requires all partners to disclose the EPN relationship regardless of location; disclosure must (1) make clear to reasonable consumers that content is promotional and the partner earns commissions, (2) be easily identifiable and frequent — a disclosure only in Terms/Legal/About pages is NOT compliant, (3) sit in close proximity to the affiliate links — linking to a disclosure page is not sufficient.

### 2.6 API License Agreement — caching/storing/display
- Sources: https://developer.ebay.com/join/api-license-agreement (SEARCH-SNIPPET-ONLY) and the 2018 PDF https://developer.ebay.com/cms/files/api_license_2018-10-26.pdf (not fetched).
- Snippet-level takeaways: (a) remove/destroy eBay Data when no longer needed for the Terms' purposes, on eBay's written request, or when retention exceeds industry best practice — within 30 days; (b) delete Personal Information promptly on the earlier of your retention policy / eBay or user request / no-longer-necessary / program termination; (c) "Other User Information" (seller/buyer identity data) may only be processed to facilitate use of eBay Services; (d) "all intermediate copies must be deleted when they are no longer required"; (e) display eBay Content consistently with the Agreement / Buy API UX requirements per marketplace (https://developer.ebay.com/api-docs/buy/static/buy-requirements.html). eBay best-practice docs *encourage* local caching to save calls but push Browse for real-time price/availability (https://developer.ebay.com/api-docs/static/gs_follow-best-practices.html, SEARCH-SNIPPET-ONLY).
- A hard "N-hour max cache" number for Browse listing data was NOT found (UNKNOWN). Design assumption: cache active-listing data briefly (hours), refresh price/availability on view, never persist seller PII, and keep a documented deletion path.

---

## 3. Affiliate / referral programs for pack & vault platforms

| Platform | Program exists? | Payout | Content rules | Evidence |
|---|---|---|---|---|
| **Courtyard.io** | Yes — user referral program (points/tiers), not a cash affiliate program | Referee gets discount / guaranteed $25+ buyback on first $25 starter pack; referrer earns points (1,000+ per qualifying referral; 6 tiers; 5,000 pts = $25 pack credit). Qualifying = referee completes ID verification and buys >= $20 of packs. | Rules page prohibits: spam/bulk email, bots/automation to distribute links, buying trademark keywords, **misleading claims about Courtyard**, misrepresenting your connection to Courtyard, fake sites/profiles, "any false or misleading statements to get referees to use your link"; links may only be shared "with people you know" (this last clause arguably excludes public-website affiliate use — confirm). | https://docs.courtyard.io/courtyard/logistics-and-legal/user-agreements/referral-program-rules ; https://docs.courtyard.io/courtyard/resources/referral-program (SEARCH-SNIPPET-ONLY, host blocked) |
| **Collector Crypt** | Yes — referral link; rewards in Gacha Points (tied to $CARDS airdrop allocations), plus quarterly referral-point bonuses | Percentage of referred users' points; exact % not published in any source found (UNKNOWN). Points redeem for free packs. No cash/commission program found. | No public content rules found (UNKNOWN). | https://www.thespike.gg/reviews/collector-crypt/promo-code ; https://airdrops.io/collector-crypt/ ; https://medium.com/@collector_team/exciting-2024-initiatives-at-collector-crypt-ac4e3606f6ab ; https://docs.collectorcrypt.com/gacha/api (all SEARCH-SNIPPET-ONLY) |
| **Phygitals** | Yes — "Refer & Earn" in-app | Referrer gets **1% of referred users' buybacks** (e.g., $100 buyback -> $1), paid as **site credit only** (not withdrawable); currently no cap on referrals or rewards. ToS: "earn a percentage of qualifying purchases... rates, qualifying purchase types, and payout schedules are detailed on the Referrals page... may be updated at Phygitals' sole discretion." | No published content rules found (UNKNOWN). 18+ required. | https://www.thespike.gg/reviews/phygitals/promo-code ; https://docs.phygitals.com/user-agreements/terms-of-service (SEARCH-SNIPPET-ONLY) |
| **Fanatics Collect** | Yes — true affiliate program via **Impact** network, buyer and seller referral tracks | "% of each referred purchase", monthly payments; rate not published (general Fanatics programs ~8-10% but that is merch, not Collect). | Impact/Fanatics approval at discretion. | https://info.fanaticscollect.com/affiliate-referral-page-buyer/ ; https://info.fanaticscollect.com/affiliate-referral-page-seller/ (SEARCH-SNIPPET-ONLY, host blocked) |
| **Fanatics Live / Instant Rips** | User referral ("Spend $25, get $25") | $25 credit each side after qualifying spend. | UNKNOWN | https://www.fanatics.live/invite/... ; https://www.thespike.gg/reviews/fanatics-instant-rips/promo-code (SEARCH-SNIPPET-ONLY) |
| **Whatnot** | Yes — Whatnot Affiliate Program for eligible creators | Commission on eligible purchases within 3-day attribution window; rates quoted anywhere from 1-3.5% up to 10% across third-party sites (UNKNOWN which is current). | Eligibility-gated. | https://help.whatnot.com/hc/en-us/articles/14718641787021-Whatnot-Affiliate-Program (SEARCH-SNIPPET-ONLY, blocked) |
| **Arena Club** | Support article says no referral program; a FlexOffers affiliate listing exists | UNKNOWN | UNKNOWN | https://arenaclubsupport.zendesk.com/hc/en-us/articles/38772041749019-Do-you-have-a-referral-program ; https://www.flexoffers.com/affiliate-programs/arena-club-affiliate-program/ (SEARCH-SNIPPET-ONLY) |
| **DYLI** | Yes — referral | 20% of referee's first DYLI-product purchase + 20 "diamonds" per referral, 2 per second-degree referral. | UNKNOWN | https://docs.dyli.io/core-features/rewards (DNS failed on fetch; SEARCH-SNIPPET-ONLY) |
| **Alt.xyz** | "Alt Rewards" exists; no affiliate program found | UNKNOWN | UNKNOWN | https://support.alt.xyz/en/articles/10743768-alt-rewards (SEARCH-SNIPPET-ONLY) |
| **CGC Cards** (grader, not packs) | Affiliate page exists | UNKNOWN | UNKNOWN | https://www.cgccards.com/affiliates/ (SEARCH-SNIPPET-ONLY) |

Takeaway: of the three named pack platforms, only **Phygitals** pays an ongoing revenue share (site credit, 1% of buybacks), **Courtyard** is a points/tier user-referral scheme with explicit "people you know" and no-misleading-claims rules, and **Collector Crypt** is a points/airdrop scheme with undocumented terms. None is a conventional cash-paying affiliate network; Fanatics Collect (via Impact) and Whatnot are the closest to that.

### 3.1 FTC obligations for affiliate content
- **Endorsement Guides (16 CFR Part 255, revised July 2023):** any material connection (commissions, free product, discounts, referral credit) must be disclosed **clearly and conspicuously** = "difficult to miss (easily noticeable) and easily understandable"; online disclosures must be "unavoidable"; placed near the claim, in the same medium; vague tags like "#sp", "collab", "ambassador" are insufficient. Sources: https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking ; https://www.federalregister.gov/documents/2023/07/26/2023-14795/guides-concerning-the-use-of-endorsements-and-testimonials-in-advertising ; https://www.morganlewis.com/pubs/2023/07/ftc-updates-endorsement-guides-proposes-endorsement-related-rule (all SEARCH-SNIPPET-ONLY; ftc.gov/federalregister/ecfr blocked).
- **Earnings / money-making claims:** FTC's Oct 2021 Notice of Penalty Offenses put 1,100+ businesses on notice that false/unsubstantiated earnings claims can draw civil penalties (~$43,792/violation then; inflation-adjusted higher now); marketers are liable for claims repeated by affiliates/influencers. Sources: https://www.ftc.gov/enforcement/notices-penalty-offenses/penalty-offenses-concerning-money-making-opportunities ; https://www.ftc.gov/news-events/news/press-releases/2021/10/ftc-puts-businesses-notice-false-money-making-claims-could-lead-big-penalties (SEARCH-SNIPPET-ONLY). Relevance: "EV +12% on this pack" style copy is an implied earnings/performance claim — needs substantiation and honest framing (spread, fees, variance, buyback haircut).
- **"Not financial advice" disclaimers:** No FTC document specifically about NFA disclaimers for collectibles was found (UNKNOWN). The general principle from the Guides' own FAQ — the Guides "don't provide a safe harbor"; deception depends on the facts — means an NFA disclaimer does not cure a deceptive claim (SEARCH-SNIPPET-ONLY: https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking ; https://federal-lawyer.com/ftc-defense/affiliate-disclosure/). Use NFA as hygiene, not as a shield.
- **Chance-based products / 18+:** FTC's 2019 "Inside the Game" loot-box workshop and 2020 staff perspective paper say odds disclosures must be accurate and non-misleading (Section 5), and flag minors and addictive behaviors as concerns; 2025 Cognosphere (Genshin Impact) settlement required age-screening, parental consent under 16, and clear odds/cost disclosures. Sources: https://www.ftc.gov/system/files/documents/reports/staff-perspective-paper-loot-box-workshop/loot_box_workshop_staff_perspective.pdf ; https://www.ftc.gov/business-guidance/blog/2020/08/loot-boxes-whats-play ; https://www.lexology.com/library/detail.aspx?g=d5cc7752-3a1b-4f75-9e8a-2e35d97122f9 (SEARCH-SNIPPET-ONLY). Collector Crypt, Courtyard (App Store 18+ rating) and Phygitals all require 18+ per their terms (SEARCH-SNIPPET-ONLY: https://deadspin.com/mystery-boxes/collector-crypt/ ; https://apps.apple.com/us/app/-/id6748155184 ; https://www.strafe.com/esports-betting/reviews/phygitals/). Randomized-pack platforms are described by commentators as a legal "gray zone between gaming, gambling, and securities" (https://coinmarketcap.com/cmc-ai/collector-crypt/what-is/ ; https://www.fairgambling.com/spotlight/alt-gambling-skins-gacha-mystery-boxes-card-rips , SEARCH-SNIPPET-ONLY). Practical: show an 18+ notice and an odds/EV-variance caveat next to any pack link, and mirror each platform's own age gate.

---

## 4. Hosts attempted via WebFetch and blocked (EGRESS_BLOCKED unless noted)
- www.psacard.com
- api.psacard.com
- developer.ebay.com
- community.ebay.com
- partnernetwork.ebay.com
- docs.courtyard.io
- docs.phygitals.com
- docs.collectorcrypt.com
- docs.dyli.io (DNS ENOTFOUND, not proxy)
- help.whatnot.com
- arenaclubsupport.zendesk.com
- info.fanaticscollect.com
- forums.collectors.com
- boards.cgccomics.com
- cardgrader.ai
- www.thespike.gg
- scavio.dev
- www.ftc.gov
- www.federalregister.gov
- www.ecfr.gov

Hosts that fetched successfully: raw.githubusercontent.com (maccann-24 PSA research doc; michabbb Browse OpenAPI beta spec mirror), github.com (brad-newman/fetch-psa-api README).

## 5. Open items requiring a human with a browser / real credentials
1. Generate a PSA token; hit GetByCertNumber ~5 times and read `TotalPopulation`; then hit it >100 times to confirm the real daily cap (100 vs "1/day" rumor). Save the End User Agreement text.
2. Read eBay's live Browse `search` doc for the exact `aspect_filter` syntax for condition descriptors and whether `item_summary/search` returns `conditionDescriptors` / cert number; test against production with a sandbox-turned-prod keyset.
3. Read the EPN Network Agreement Section I.G and the US rate card line for Trading Cards.
4. Read the eBay API License Agreement sections on data retention to set a concrete cache TTL policy.
5. Confirm Courtyard's "share only with people you know" clause vs public-site referral use; ask Collector Crypt for written referral terms.
