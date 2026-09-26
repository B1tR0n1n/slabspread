"""Phygitals public API (Phase 0 Q2). Gated: default OFF.

The API docs (phygitals.mintlify.app) say pack and marketplace GETs "do not require a key" and
name "bots, scripts, custom tooling" and "price-comparison tooling" as intended uses; the ToS
§11 forbids "bots, scripts, or automated tools … without Phygitals' prior written consent". The
docs are the closest thing to consent, but the ToS names *written* consent, so this worker runs
only after the owner sets SLABSPREAD_PHYGITALS_API_ENABLED (see owner-runbook §7, Q2).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from config import settings
from ingest.base import Context, SourceNotApproved, with_backoff
from ingest.collectorcrypt_api import upsert_pack_odds
from ingest.persist import UpsertReport, upsert_slabs
from ingest.phygitals import SOURCE_KEY, normalize_listing

PACKS_URL = "https://api.phygitals.com/api/vm/available"
LISTINGS_URL = "https://api.phygitals.com/api/marketplace/marketplace-listings"


def _get(ctx: Context, url: str, params: dict | None = None) -> Any:
    def do():
        ctx.limiter.acquire()
        r = ctx.http.get(
            url, params=params, headers={"User-Agent": settings.user_agent, "Accept": "application/json"}
        )
        r.raise_for_status()
        return r.json()

    return with_backoff(do)


def _gate() -> None:
    if not settings.phygitals_api_enabled:
        raise SourceNotApproved(
            "phygitals api: SLABSPREAD_PHYGITALS_API_ENABLED is off (Q2: written consent)"
        )


class PhygitalsPacksWorker:
    key = "phygitals_packs"
    limiter_key = "phygitals_api"

    def fetch(self, ctx: Context) -> dict:
        _gate()
        packs = _get(ctx, PACKS_URL, {"includeRepacks": "true"})
        ctx.notes.update({"packs": len(packs)})
        return {"fetched_at": datetime.utcnow().isoformat(), "packs": packs}

    def next_cursor(self, raw: dict) -> str | None:
        return None

    def normalize(self, raw: dict) -> list[dict]:
        as_of = datetime.fromisoformat(raw["fetched_at"])
        out = []
        for p in raw.get("packs", []):
            dist = p.get("rarity_distribution") or []
            total = sum(Decimal(str(d.get("weight", 0))) for d in dist)
            if not dist or total <= 0 or not p.get("mint_price"):
                continue
            tiers = [
                {
                    "tier": d.get("name") or str(d.get("id")),
                    "probability": (Decimal(str(d["weight"])) / total).quantize(Decimal("0.000001")),
                    "value_low": Decimal(str(d["lower"])) if d.get("lower") is not None else None,
                    "value_high": Decimal(str(d["upper"])) if d.get("upper") is not None else None,
                }
                for d in dist
            ]
            out.append(
                {
                    "slug": p["slug"],
                    "name": p.get("name") or p["slug"],
                    "price": Decimal(str(p["mint_price"])),
                    "buyback_pct": Decimal(str(p.get("buyback_percent", 0.85))),
                    "as_of": as_of,
                    "tiers": tiers,
                    "ev_stated": p.get("ev"),
                }
            )
        return out

    def upsert(self, s: Session, records: list[dict]) -> UpsertReport:
        return upsert_pack_odds(s, SOURCE_KEY, "Phygitals", records, provenance="api_json")


class PhygitalsListingsWorker:
    key = "phygitals_listings"
    limiter_key = "phygitals_api"

    def fetch(self, ctx: Context) -> dict:
        _gate()
        pages = []
        for page in range(1, settings.phygitals_pages_per_run + 1):
            doc = _get(ctx, LISTINGS_URL, {"page": page, "itemsPerPage": 100, "listedStatus": "listed"})
            pages.append(doc)
            if not doc.get("listings"):
                break
        ctx.notes.update({"pages": len(pages), "amount": pages[0].get("amount") if pages else None})
        return {"fetched_at": datetime.utcnow().isoformat(), "pages": pages}

    def next_cursor(self, raw: dict) -> str | None:
        return None

    def normalize(self, raw: dict) -> list:
        out = []
        for page in raw.get("pages", []):
            for row in page.get("listings", []):
                slab, ask = normalize_listing(row)
                out.append((slab, ask, {}))
        return out

    def upsert(self, s: Session, records: list) -> UpsertReport:
        return upsert_slabs(s, SOURCE_KEY, records)


def packs_worker() -> PhygitalsPacksWorker:
    return PhygitalsPacksWorker()


def listings_worker() -> PhygitalsListingsWorker:
    return PhygitalsListingsWorker()
