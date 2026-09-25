"""Workers for sources whose license row is not `approved`. Each refuses to fetch unless its
gate in config is on, and records a `skipped` run so /health/ingest shows *why* it is idle.

Turning a gate on is not a config tweak; it is an assertion that the Phase 0 question was
answered and logged in docs/data-licenses.md.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from config import settings
from ingest.base import Context, SourceNotApproved
from ingest.persist import UpsertReport


class GatedWorker:
    limiter_key = "collectorcrypt_api"

    def __init__(self, key: str, gate_attr: str, question: str):
        self.key, self.gate_attr, self.question = key, gate_attr, question

    def fetch(self, ctx: Context) -> Any:
        if not getattr(settings, self.gate_attr):
            raise SourceNotApproved(
                f"{self.key}: gate SLABSPREAD_{self.gate_attr.upper()} is off — {self.question} unresolved "
                "(docs/phase0-findings.md §10)"
            )
        raise NotImplementedError(f"{self.key}: fetch arrives once {self.question} is resolved")

    def normalize(self, raw: Any) -> list[Any]:
        return []

    def upsert(self, session: Session, records: list[Any]) -> UpsertReport:
        return UpsertReport()

    def next_cursor(self, raw: Any) -> str | None:
        return None


def platform_odds_worker() -> GatedWorker:
    return GatedWorker("platform_odds", "collectorcrypt_api_enabled", "Q1")


def courtyard_metadata_worker() -> GatedWorker:
    return GatedWorker("courtyard_metadata", "courtyard_metadata_enabled", "Q3")


def phygitals_api_worker() -> GatedWorker:
    return GatedWorker("phygitals_api", "phygitals_api_enabled", "Q2")


# Not even gated: excluded outright until the owner completes an application/contract.
EXCLUDED_UNTIL_LICENSED = {
    "ebay_browse": "production Buy API approval + EPN (Q6)",
    "price_api": "commercial license with the chosen vendor (Q4)",
    "psa_cert": "PSA End User Agreement read and token issued (Q5)",
}
