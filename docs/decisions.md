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
