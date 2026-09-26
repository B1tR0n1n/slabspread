"""DB glue that feeds the pure engines. Reads models, builds engine inputs, returns results.

Nothing here computes a margin; that is engines/. Nothing here writes, except `record_alerts`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from engines import lag, pack_ev, spread
from models import (
    Alert,
    Card,
    Listing,
    ListingStatus,
    Pack,
    PackOdds,
    Sale,
    Source,
    Valuation,
    ValueType,
)


def spread_config() -> spread.SpreadConfig:
    s = settings
    return spread.SpreadConfig(
        shipping=Decimal(str(s.spread_shipping)),
        sales_tax_rate=Decimal(str(s.spread_sales_tax_rate)),
        vault_intake_cost=Decimal(str(s.spread_vault_intake_cost)),
        grading_cost=Decimal(str(s.spread_grading_cost)),
        platform_fee_rate=Decimal(str(s.spread_platform_fee_rate)),
        min_sales=s.spread_min_sales,
        sales_window=timedelta(days=s.spread_sales_window_days),
        max_age_ask=timedelta(hours=s.spread_max_age_ask_hours),
        max_age_floor=timedelta(hours=s.spread_max_age_floor_hours),
    )


def lag_config() -> lag.LagConfig:
    return lag.LagConfig(
        drop_pct=Decimal(str(settings.lag_drop_pct)),
        flat_hours=settings.lag_flat_hours,
        flat_tolerance_pct=Decimal(str(settings.lag_flat_tolerance_pct)),
    )


# --------------------------------------------------------------------------------------
# Floors: the guaranteed exit for a card, derived from the freshest platform value
# --------------------------------------------------------------------------------------


def latest_floor(s: Session, card_id: int) -> spread.Floor | None:
    """Best guaranteed exit across sources: an explicit `buyback` valuation wins; otherwise
    `insured_value`/`platform_fmv` × that source's buyback %. Freshest per source, then max."""
    rows = s.execute(
        select(Valuation, Source.key)
        .join(Source, Source.id == Valuation.source_id)
        .where(Valuation.card_id == card_id)
        .where(Valuation.value_type.in_([ValueType.buyback, ValueType.insured_value, ValueType.platform_fmv]))
        .order_by(Valuation.as_of.desc())
    ).all()
    best: spread.Floor | None = None
    seen: set[tuple[str, ValueType]] = set()
    for v, src_key in rows:
        if (src_key, v.value_type) in seen:
            continue
        seen.add((src_key, v.value_type))
        if v.value_type == ValueType.buyback:
            value, oracle = Decimal(v.value), f"{src_key}:buyback"
        else:
            pct = settings.buyback_pct.get(src_key)
            if pct is None:
                continue
            value = (Decimal(v.value) * Decimal(str(pct))).quantize(Decimal("0.01"))
            oracle = f"{src_key}:{v.value_type.value}*{pct}"
        cand = spread.Floor(value, v.as_of, oracle)
        if best is None or cand.value > best.value:
            best = cand
    return best


def sales_for(s: Session, card_id: int, since: datetime) -> list[spread.SaleObs]:
    rows = s.scalars(select(Sale).where(Sale.card_id == card_id, Sale.sold_at >= since)).all()
    return [spread.SaleObs(Decimal(r.price), r.sold_at) for r in rows]


# --------------------------------------------------------------------------------------
# Opportunities
# --------------------------------------------------------------------------------------


@dataclass
class OpportunityRow:
    listing: Listing
    card: Card
    source_key: str
    opp: spread.Opportunity


def opportunities(s: Session, now: datetime | None = None) -> tuple[list[OpportunityRow], dict[str, int]]:
    """Ranked opportunities across every active listing that has a card, plus rejection counts."""
    now = now or datetime.utcnow()
    cfg = spread_config()
    rows: list[OpportunityRow] = []
    rejected: dict[str, int] = {}
    listings = s.execute(
        select(Listing, Card, Source.key)
        .join(Card, Card.id == Listing.card_id)
        .join(Source, Source.id == Listing.source_id)
        .where(Listing.status == ListingStatus.active)
    ).all()
    for listing, card, src_key in listings:
        ask = spread.Ask(
            Decimal(listing.ask_price),
            listing.last_seen,
            is_raw=card.grader is None,
            listing_ref=f"{src_key}:{listing.external_id}",
        )
        floor = latest_floor(s, card.id)
        sales = sales_for(s, card.id, now - cfg.max_age_sale)
        res = spread.compute_spread(ask, floor, sales, cfg, now)
        if isinstance(res, spread.Rejection):
            rejected[res.reason] = rejected.get(res.reason, 0) + 1
            continue
        rows.append(OpportunityRow(listing, card, src_key, res))
    rows.sort(key=lambda r: r.opp.sort_key, reverse=True)
    return rows, rejected


# --------------------------------------------------------------------------------------
# Card detail
# --------------------------------------------------------------------------------------


def card_detail(s: Session, card_id: int) -> dict:
    card = s.get(Card, card_id)
    if card is None:
        return {}
    listings = s.execute(
        select(Listing, Source.key)
        .join(Source)
        .where(Listing.card_id == card_id)
        .order_by(Listing.last_seen.desc())
    ).all()
    sales = s.execute(
        select(Sale, Source.key).join(Source).where(Sale.card_id == card_id).order_by(Sale.sold_at)
    ).all()
    vals = s.execute(
        select(Valuation, Source.key)
        .join(Source)
        .where(Valuation.card_id == card_id)
        .order_by(Valuation.as_of)
    ).all()
    return {
        "card": card,
        "listings": [(lst, k) for lst, k in listings],
        "sales": [(sl, k) for sl, k in sales],
        "valuations": [(v, k) for v, k in vals],
        "floor": latest_floor(s, card_id),
        "chart": {
            "sales": [{"x": sl.sold_at.isoformat(), "y": float(sl.price), "src": k} for sl, k in sales],
            "valuations": [
                {"x": v.as_of.isoformat(), "y": float(v.value), "src": f"{k}:{v.value_type.value}"}
                for v, k in vals
            ],
        },
    }


# --------------------------------------------------------------------------------------
# Lag alerts
# --------------------------------------------------------------------------------------


def lag_alerts(s: Session, now: datetime | None = None) -> list[tuple[Card, lag.LagAlert]]:
    now = now or datetime.utcnow()
    cfg = lag_config()
    out = []
    for card in s.scalars(select(Card)).all():
        real = [
            lag.Point(sl.sold_at, Decimal(sl.price))
            for sl in s.scalars(select(Sale).where(Sale.card_id == card.id))
        ]
        plat = [
            lag.Point(v.as_of, Decimal(v.value))
            for v in s.scalars(
                select(Valuation).where(
                    Valuation.card_id == card.id,
                    Valuation.value_type.in_([ValueType.platform_fmv, ValueType.insured_value]),
                )
            )
        ]
        a = lag.detect_lag(real, plat, cfg, now)
        if a:
            out.append((card, a))
    return out


# --------------------------------------------------------------------------------------
# Pack edges
# --------------------------------------------------------------------------------------


def pack_edges(s: Session) -> list[dict]:
    """Latest odds snapshot per pack → PackEV. Tier value = band midpoint, buyback = midpoint × pct."""
    out = []
    for pack, src_key in s.execute(select(Pack, Source.key).join(Source)).all():
        odds = s.scalars(
            select(PackOdds).where(PackOdds.pack_id == pack.id).order_by(PackOdds.as_of.desc())
        ).all()
        if not odds:
            continue
        latest_as_of = odds[0].as_of
        snapshot = [o for o in odds if o.as_of == latest_as_of]
        pct = Decimal(
            str(pack.buyback_pct if pack.buyback_pct is not None else settings.buyback_pct.get(src_key, 0))
        )
        tiers = []
        for o in snapshot:
            t = pack_ev.tier_from_snapshot(
                o.tier,
                Decimal(o.probability),
                value_low=o.value_low,
                value_high=o.value_high,
                value_mean=o.value_mean,
                sample_n=o.sample_n,
                buyback_pct=pct,
                pool_size=o.pool_size,
            )
            if t:
                tiers.append(t)
        if not tiers:
            continue
        stated = next((Decimal(o.stated_ev) for o in snapshot if o.stated_ev is not None), None)
        ev = pack_ev.compute_pack_ev(Decimal(pack.price), tiers, stated_ev=stated, buyback_pct=pct)
        out.append(
            {
                "pack": pack,
                "source": src_key,
                "as_of": latest_as_of,
                "provenance": snapshot[0].provenance,
                "ev": ev,
            }
        )
    out.sort(key=lambda r: r["ev"].house_edge)
    return out


# --------------------------------------------------------------------------------------
# Alerts (write path)
# --------------------------------------------------------------------------------------


def record_alerts(s: Session, now: datetime | None = None) -> list[Alert]:
    """Create Alert rows for opportunities at/above the threshold, honouring the cooldown."""
    now = now or datetime.utcnow()
    threshold = Decimal(str(settings.alert_floor_margin_min))
    cooldown = now - timedelta(hours=settings.alert_cooldown_hours)
    created: list[Alert] = []
    rows, _ = opportunities(s, now)
    for r in rows:
        if r.opp.floor_margin is None or r.opp.floor_margin < threshold:
            continue
        recent = s.scalar(select(Alert).where(Alert.listing_id == r.listing.id, Alert.created_at >= cooldown))
        if recent:
            continue
        a = Alert(
            listing_id=r.listing.id,
            card_id=r.card.id,
            floor_margin=r.opp.floor_margin,
            market_margin=r.opp.market_margin,
            all_in_cost=r.opp.all_in_cost,
            calculation=r.opp.calculation,
            created_at=now,
        )
        s.add(a)
        created.append(a)
    s.flush()
    return created
