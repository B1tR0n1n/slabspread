"""Pure aggregations for the public pages. Inputs are plain records; outputs are derived
numbers only (edges, ratios, counts) — never a licensed raw value (ground rule 3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from statistics import median

from engines import pack_ev

FOUR = Decimal("0.0001")


@dataclass(frozen=True)
class OddsRow:
    platform: str
    pack_slug: str
    pack_name: str
    pack_price: Decimal
    buyback_pct: Decimal
    as_of: datetime
    tier: str
    probability: Decimal
    value_low: Decimal | None
    value_high: Decimal | None
    provenance: str


@dataclass(frozen=True)
class EdgePoint:
    platform: str
    pack_slug: str
    pack_name: str
    as_of: datetime
    provenance: str
    ev: pack_ev.PackEV
    tiers: tuple[pack_ev.Tier, ...]


def house_edge_series(rows: list[OddsRow]) -> list[EdgePoint]:
    """One PackEV per (platform, pack, snapshot). Tier value = band midpoint; buyback = midpoint × pct.
    Tiers without a value band are skipped, and a snapshot with no usable tier is dropped."""
    groups: dict[tuple[str, str, datetime], list[OddsRow]] = {}
    for r in rows:
        groups.setdefault((r.platform, r.pack_slug, r.as_of), []).append(r)
    out: list[EdgePoint] = []
    for (platform, slug, as_of), grp in sorted(groups.items(), key=lambda kv: kv[0]):
        tiers = []
        for r in grp:
            if r.value_low is None:
                continue
            mid = pack_ev.band_midpoint(r.value_low, r.value_high)
            tiers.append(
                pack_ev.Tier(r.tier, r.probability, mid, (mid * r.buyback_pct).quantize(Decimal("0.01")))
            )
        if not tiers:
            continue
        ev = pack_ev.compute_pack_ev(grp[0].pack_price, tiers)
        out.append(EdgePoint(platform, slug, grp[0].pack_name, as_of, grp[0].provenance, ev, tuple(tiers)))
    return out


@dataclass(frozen=True)
class GapPair:
    platform: str
    card_key: str
    platform_value: Decimal  # what the platform says (never published raw)
    external_value: Decimal  # median of real sales (never published raw)


@dataclass(frozen=True)
class GapSummary:
    platform: str
    n: int
    median_ratio: Decimal  # platform_value / external_value, median across cards
    share_above_external: Decimal  # fraction of cards the platform values above real sales
    p25_ratio: Decimal
    p75_ratio: Decimal


def _pct(sorted_vals: list[Decimal], q: Decimal) -> Decimal:
    if not sorted_vals:
        return Decimal(0)
    idx = (len(sorted_vals) - 1) * q
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


def valuation_gap(pairs: list[GapPair], *, min_n: int = 5) -> list[GapSummary]:
    """Aggregate platform-vs-real ratios per platform. Below `min_n` cards the platform is omitted:
    an aggregate over four cards would leak individual values."""
    by_platform: dict[str, list[Decimal]] = {}
    for p in pairs:
        if p.external_value > 0:
            by_platform.setdefault(p.platform, []).append(p.platform_value / p.external_value)
    out = []
    for platform, ratios in sorted(by_platform.items()):
        if len(ratios) < min_n:
            continue
        rs = sorted(ratios)
        q = lambda x: Decimal(x).quantize(FOUR, rounding=ROUND_HALF_UP)  # noqa: E731
        out.append(
            GapSummary(
                platform=platform,
                n=len(rs),
                median_ratio=q(median(rs)),
                share_above_external=q(Decimal(sum(r > 1 for r in rs)) / len(rs)),
                p25_ratio=q(_pct(rs, Decimal("0.25"))),
                p75_ratio=q(_pct(rs, Decimal("0.75"))),
            )
        )
    return out
