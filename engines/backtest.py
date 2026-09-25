"""Backtest the spread engine on stored history (plan §5 exit test).

For each historical ask, compute the opportunity *as it would have been seen then* (only
observations at or before that moment), then check what the floor actually was at the first
observation after a settling delay. A flagged deal "met its floor margin" if the realized
floor minus the all-in cost was at least the predicted floor margin.

Pure: takes lists of observations, returns a report. The DB glue lives elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

from engines.spread import Ask, Floor, Opportunity, SaleObs, SpreadConfig, compute_spread


@dataclass(frozen=True)
class FloorObs:
    value: Decimal
    at: datetime
    oracle: str


@dataclass
class BacktestReport:
    asks: int = 0
    flagged: int = 0  # floor_margin >= flag_threshold at decision time
    resolved: int = 0  # a later floor observation existed to judge against
    met_floor: int = 0  # realized floor margin >= predicted floor margin
    positive_realized: int = 0  # realized floor margin > 0 regardless of prediction
    rejected: dict[str, int] = field(default_factory=dict)
    details: list[dict] = field(default_factory=list)

    @property
    def hit_rate(self) -> Decimal | None:
        return Decimal(self.met_floor) / self.resolved if self.resolved else None


def _floor_at(floors: list[FloorObs], at: datetime) -> Floor | None:
    prior = [f for f in floors if f.at <= at]
    if not prior:
        return None
    f = max(prior, key=lambda x: x.at)
    return Floor(f.value, f.at, f.oracle)


def _floor_after(floors: list[FloorObs], at: datetime) -> FloorObs | None:
    later = [f for f in floors if f.at >= at]
    return min(later, key=lambda x: x.at) if later else None


def backtest_spread(
    asks: list[Ask],
    floors: list[FloorObs],
    sales: list[SaleObs],
    cfg: SpreadConfig,
    *,
    flag_threshold: Decimal = Decimal("0"),
    settle: timedelta = timedelta(days=3),
) -> BacktestReport:
    rep = BacktestReport(asks=len(asks))
    for ask in sorted(asks, key=lambda a: a.as_of):
        now = ask.as_of
        seen_sales = [s for s in sales if s.at <= now]
        res = compute_spread(ask, _floor_at(floors, now), seen_sales, cfg, now)
        if not isinstance(res, Opportunity):
            rep.rejected[res.reason] = rep.rejected.get(res.reason, 0) + 1
            continue
        if res.floor_margin is None or res.floor_margin < flag_threshold:
            continue
        rep.flagged += 1
        later = _floor_after(floors, now + settle)
        row = {
            "listing_ref": ask.listing_ref,
            "at": now.isoformat(),
            "predicted_floor_margin": str(res.floor_margin),
        }
        if later is None:
            rep.details.append({**row, "outcome": "unresolved"})
            continue
        rep.resolved += 1
        realized = later.value - res.all_in_cost
        met = realized >= res.floor_margin
        rep.met_floor += met
        rep.positive_realized += realized > 0
        rep.details.append(
            {
                **row,
                "realized_floor": str(later.value),
                "realized_margin": str(realized),
                "outcome": "met" if met else "missed",
            }
        )
    return rep
