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
