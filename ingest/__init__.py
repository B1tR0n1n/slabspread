"""One module per source. Each will implement fetch() / normalize() / upsert() (plan §4).

Phase 1 ships `normalize()` only — the part that turns a recorded response into
`NormalizedSlab`s. `fetch()` arrives in Phase 2 and only for sources whose row in
docs/data-licenses.md is `approved`.
"""

from ingest import collectorcrypt, courtyard, phygitals

NORMALIZERS = {
    "courtyard": courtyard,
    "collector_crypt": collectorcrypt,
    "phygitals": phygitals,
}

__all__ = ["NORMALIZERS", "collectorcrypt", "courtyard", "phygitals"]
