"""Collector Crypt documented public API (Phase 0 Q1, FETCH-grade 2026-09-26).

docs.collectorcrypt.com/marketplace/api: "Marketplace endpoints need no credential … Anonymous
callers are counted per IP … 300 / minute … Send a non-empty User-Agent." docs.collectorcrypt.com/
gacha/api: GET /api/machines answers without a key. We identify ourselves, stay far under the
published limits, and send a bearer key when the owner has one (support@collectorcrypt.com).

Two workers:
  cc_marketplace — listings → Listing + Slab (gradingID = cert) + Valuation(insured_value)
  cc_gacha_odds  — machines → Pack + PackOdds (tier probability + insured-value band), provenance api_json
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from ingest.base import Context, SourceNotApproved, with_backoff
from ingest.collectorcrypt import SOURCE_KEY, normalize_row
from ingest.persist import UpsertReport, get_or_create_source, upsert_slabs
from models import Pack, PackOdds, ValueType

MARKETPLACE_URL = "https://api.collectorcrypt.com/marketplace"
MACHINES_URL = "https://gacha.collectorcrypt.com/api/machines"
POOL_URL = (
    "https://gacha.collectorcrypt.com/api/getNfts"  # ?code=&rarity= → the tier's prize pool (paged, ~40)
)


def _headers() -> dict[str, str]:
    h = {"User-Agent": settings.user_agent, "Accept": "application/json"}
    if settings.collectorcrypt_api_key:
        h["Authorization"] = f"Bearer {settings.collectorcrypt_api_key}"
    return h


def _get(ctx: Context, url: str, params: dict | None = None) -> Any:
    def do():
        ctx.limiter.acquire()
        r = ctx.http.get(url, params=params, headers=_headers())
        r.raise_for_status()
        return r.json()

    return with_backoff(do)


def _gate() -> None:
    if not settings.collectorcrypt_api_enabled:
        raise SourceNotApproved("cc api: SLABSPREAD_COLLECTORCRYPT_API_ENABLED is off (Q1)")


class CCMarketplaceWorker:
    key = "cc_marketplace"
    limiter_key = "collectorcrypt_api"

    def fetch(self, ctx: Context) -> dict:
        _gate()
        pages, cursor = [], None
        for _ in range(settings.collectorcrypt_pages_per_run):
            params = {"step": settings.collectorcrypt_step}
            if cursor:
                params["cursor"] = cursor
            page = _get(ctx, MARKETPLACE_URL, params)
            pages.append(page)
            cursor = page.get("nextCursor")
            if not cursor or not page.get("filterNFtCard"):
                break
        ctx.notes.update({"pages": len(pages), "total_listed": pages[0].get("findTotal") if pages else None})
        return {"fetched_at": datetime.utcnow().isoformat(), "pages": pages}

    def next_cursor(self, raw: dict) -> str | None:
        return None  # newest-first listing feed: always start from the top

    def normalize(self, raw: dict) -> list:
        out = []
        for page in raw.get("pages", []):
            for row in page.get("filterNFtCard", []):
                slab, iv = normalize_row(row)
                lst = row.get("listing") or {}
                price = lst.get("price")
                out.append(
                    (
                        slab,
                        Decimal(str(price)) if price is not None else None,
                        {ValueType.insured_value: iv} if iv is not None else {},
                    )
                )
        return out

    def upsert(self, s: Session, records: list) -> UpsertReport:
        return upsert_slabs(s, SOURCE_KEY, records)


class CCGachaOddsWorker:
    key = "cc_gacha_odds"
    limiter_key = "collectorcrypt_api"

    def fetch(self, ctx: Context) -> dict:
        _gate()
        doc = _get(ctx, MACHINES_URL)
        pools: dict[str, dict[str, list]] = {}
        if settings.collectorcrypt_sample_pools:
            for m in doc.get("machines", []):
                for tier in m.get("odds") or {}:
                    cards, page = [], 1
                    while page <= settings.collectorcrypt_pool_max_pages:
                        try:
                            pool = _get(
                                ctx, POOL_URL, {"code": m["code"], "rarity": tier, "page": page, "limit": 100}
                            )
                        except Exception:  # noqa: BLE001 — a missing pool degrades to band midpoint
                            break
                        cards += [
                            {"nft_address": n.get("nft_address"), "insured_value": n.get("insured_value")}
                            for n in pool.get("nfts", [])
                        ]
                        if not pool.get("hasMore"):
                            break
                        page += 1
                    if cards:
                        pools.setdefault(m["code"], {})[tier] = cards
        ctx.notes.update(
            {"machines": len(doc.get("machines", [])), "pools_sampled": sum(len(v) for v in pools.values())}
        )
        return {"fetched_at": datetime.utcnow().isoformat(), "pools": pools, **doc}

    def next_cursor(self, raw: dict) -> str | None:
        return None

    def normalize(self, raw: dict) -> list[dict]:
        as_of = datetime.fromisoformat(raw["fetched_at"]) if raw.get("fetched_at") else datetime.utcnow()
        out = []
        for m in raw.get("machines", []):
            odds, ranges = m.get("odds") or {}, m.get("tierRanges") or {}
            if not odds or not m.get("price"):
                continue
            if sum((m.get("stock") or {}).values()) == 0:
                continue  # no inventory: nothing to value, and a band midpoint would be fiction
            tiers = []
            pools = (raw.get("pools") or {}).get(m["code"], {})
            for tier, p in odds.items():
                rng = ranges.get(tier) or {}
                vals = [
                    Decimal(str(n["insured_value"])) for n in pools.get(tier, []) if n.get("insured_value")
                ]
                tiers.append(
                    {
                        "tier": tier,
                        "probability": Decimal(str(p)),
                        "value_low": Decimal(str(rng["start"])) if "start" in rng else None,
                        "value_high": Decimal(str(rng["end"])) if "end" in rng else None,
                        "value_mean": (sum(vals) / len(vals)).quantize(Decimal("0.01")) if vals else None,
                        "sample_n": len(vals) or None,
                        "pool_size": (m.get("stock") or {}).get(tier),
                    }
                )
            out.append(
                {
                    "slug": m["code"],
                    "name": m.get("name") or m["code"],
                    "price": Decimal(str(m["price"])),
                    "buyback_pct": Decimal(str(m.get("instantBuyback", 0))) / 100,
                    "as_of": as_of,
                    "tiers": tiers,
                    "public": m.get("public", True),
                    "stated_ev": Decimal(str(m["ev"])).quantize(Decimal("0.01"))
                    if m.get("ev") is not None
                    else None,
                }
            )
        return out

    def upsert(self, s: Session, records: list[dict]) -> UpsertReport:
        return upsert_pack_odds(s, SOURCE_KEY, "Collector Crypt", records, provenance="api_json")


def upsert_pack_odds(
    s: Session, source_key: str, source_name: str, records: list[dict], *, provenance: str
) -> UpsertReport:
    """Shared by every odds source: one Pack per slug, one PackOdds row per tier per snapshot."""
    rep = UpsertReport(fetched=len(records))
    src = get_or_create_source(s, source_key, source_name)
    for r in records:
        pack = s.scalar(select(Pack).where(Pack.source_id == src.id, Pack.slug == r["slug"]))
        if pack is None:
            pack = Pack(
                source_id=src.id,
                slug=r["slug"],
                name=r["name"],
                price=r["price"],
                buyback_pct=r["buyback_pct"],
            )
            s.add(pack)
            s.flush()
            rep.inserted += 1
        else:
            pack.name, pack.price, pack.buyback_pct = r["name"], r["price"], r["buyback_pct"]
            rep.updated += 1
        exists = s.scalar(select(PackOdds).where(PackOdds.pack_id == pack.id, PackOdds.as_of == r["as_of"]))
        if exists:
            continue
        for t in r["tiers"]:
            s.add(
                PackOdds(
                    pack_id=pack.id,
                    tier=t["tier"],
                    probability=t["probability"],
                    value_low=t["value_low"],
                    value_high=t["value_high"],
                    value_mean=t.get("value_mean"),
                    sample_n=t.get("sample_n"),
                    pool_size=t.get("pool_size"),
                    stated_ev=r.get("stated_ev"),
                    as_of=r["as_of"],
                    provenance=provenance,
                )
            )
    s.flush()
    return rep


def marketplace_worker() -> CCMarketplaceWorker:
    return CCMarketplaceWorker()


def gacha_odds_worker() -> CCGachaOddsWorker:
    return CCGachaOddsWorker()
