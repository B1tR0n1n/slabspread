"""Trade ledger (plan §6): buy → intake → exit, realized P&L per trade and per month, CSV
export for taxes, and calibration of the engine's predictions against what actually happened."""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Alert, ExitKind, Listing, Trade


def monthly_pnl(trades: list[Trade]) -> list[dict]:
    buckets: dict[str, dict] = defaultdict(
        lambda: {"closed": 0, "open": 0, "pnl": Decimal(0), "cost": Decimal(0)}
    )
    for t in trades:
        key = (t.exit_at or t.bought_at).strftime("%Y-%m")
        b = buckets[key]
        b["cost"] += t.total_cost
        if t.realized_pnl is None:
            b["open"] += 1
        else:
            b["closed"] += 1
            b["pnl"] += t.realized_pnl
    return [{"month": k, **v} for k, v in sorted(buckets.items(), reverse=True)]


def calibration(trades: list[Trade]) -> dict:
    """How the engine's predicted floor margin compares to realized P&L on closed trades."""
    closed = [t for t in trades if t.realized_pnl is not None and t.predicted_floor_margin is not None]
    if not closed:
        return {"n": 0}
    errors = [t.realized_pnl - Decimal(t.predicted_floor_margin) for t in closed]
    met = sum(e >= 0 for e in errors)
    return {
        "n": len(closed),
        "met_prediction": met,
        "hit_rate": (Decimal(met) / len(closed)).quantize(Decimal("0.001")),
        "mean_error": (sum(errors) / len(errors)).quantize(Decimal("0.01")),
        "worst": min(errors),
        "best": max(errors),
    }


def export_csv(trades: list[Trade]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "id", "description", "source", "listing_ref", "bought_at", "buy_price", "buy_fees",
            "intake_at", "intake_cost", "exit_kind", "exit_at", "exit_price", "exit_fees",
            "total_cost", "realized_pnl", "predicted_floor_margin", "predicted_market_margin", "notes",
        ]
    )  # fmt: skip
    for t in trades:
        iso = lambda d: d.isoformat() if d else ""  # noqa: E731
        blank = lambda v: v if v is not None else ""  # noqa: E731
        w.writerow(
            [
                t.id, t.description, t.source_key or "", t.listing_ref or "",
                iso(t.bought_at), t.buy_price, t.buy_fees, iso(t.intake_at), t.intake_cost,
                t.exit_kind.value, iso(t.exit_at), blank(t.exit_price), t.exit_fees, t.total_cost,
                blank(t.realized_pnl), blank(t.predicted_floor_margin), blank(t.predicted_market_margin),
                t.notes or "",
            ]
        )  # fmt: skip
    return buf.getvalue()


def prefill_from_alert(s: Session, alert_id: int) -> dict:
    """Everything the 'new trade' form can know from the alert, so the owner types only what changed."""
    a = s.get(Alert, alert_id)
    if a is None:
        return {}
    listing = s.get(Listing, a.listing_id)
    cents = lambda v: str(Decimal(v).quantize(Decimal("0.01"))) if v is not None else ""  # noqa: E731
    cost = a.calculation.get("cost", {}) if a.calculation else {}
    fees = sum(Decimal(cost.get(k, "0")) for k in ("shipping", "sales_tax_est")) if cost else Decimal(0)
    return {
        "alert_id": a.id,
        "card_id": a.card_id,
        "listing_ref": f"{listing.source_id}:{listing.external_id}" if listing else "",
        "description": listing.title if listing else "",
        "buy_price": cents(listing.ask_price) if listing else "",
        "buy_fees": cents(fees),
        "intake_cost": cents(cost.get("vault_intake_cost", "0")),
        "predicted_floor_margin": cents(a.floor_margin),
        "predicted_market_margin": cents(a.market_margin),
        "bought_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M"),
    }


def all_trades(s: Session) -> list[Trade]:
    return s.scalars(select(Trade).order_by(Trade.bought_at.desc())).all()


def close_trade(t: Trade, kind: ExitKind, price: Decimal, fees: Decimal, at: datetime) -> None:
    t.exit_kind, t.exit_price, t.exit_fees, t.exit_at = kind, price, fees, at
