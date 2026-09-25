"""Spread engine (plan §5a) — Trade lane.

    all_in_cost   = ask + shipping + sales_tax_est + vault_intake_cost + (grading_cost if raw)
    exit_floor    = platform buyback value                      # the guaranteed exit
    exit_market   = conservative platform resale value          # median recent sales minus fees
    floor_margin  = exit_floor  - all_in_cost
    market_margin = exit_market - all_in_cost

Rank by floor_margin first (downside-protected), then market_margin. Liquidity and staleness
filters reject rather than guess. Every result carries its full calculation, inputs and
timestamps — no black-box scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from statistics import median

ZERO = Decimal(0)
CENT = Decimal("0.01")


def money(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SpreadConfig:
    shipping: Decimal = Decimal("5.00")
    sales_tax_rate: Decimal = Decimal("0.00")  # estimated; owner's jurisdiction
    vault_intake_cost: Decimal = Decimal("0.00")  # platform intake / shipping-to-vault
    grading_cost: Decimal = Decimal("25.00")  # applied only when the item is raw
    platform_fee_rate: Decimal = Decimal("0.06")  # taken off exit_market (Courtyard ~6%)
    min_sales: int = 3  # liquidity: sales needed before exit_market is trusted
    sales_window: timedelta = timedelta(days=30)
    max_age_ask: timedelta = timedelta(hours=24)
    max_age_floor: timedelta = timedelta(hours=24)
    max_age_sale: timedelta = timedelta(days=30)


@dataclass(frozen=True)
class Ask:
    price: Decimal
    as_of: datetime
    is_raw: bool = False
    listing_ref: str = ""


@dataclass(frozen=True)
class Floor:
    """A guaranteed exit: the platform's buyback value for this exact card/grade."""

    value: Decimal
    as_of: datetime
    oracle: str  # e.g. "collector_crypt:insured_value*0.85"


@dataclass(frozen=True)
class SaleObs:
    price: Decimal
    at: datetime


# --------------------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Rejection:
    reason: str
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Opportunity:
    listing_ref: str
    all_in_cost: Decimal
    exit_floor: Decimal | None
    exit_market: Decimal | None
    floor_margin: Decimal | None
    market_margin: Decimal | None
    calculation: dict  # every input, every intermediate, every timestamp

    @property
    def sort_key(self) -> tuple[Decimal, Decimal]:
        # None sorts last: an opportunity without a floor is never ranked above one with a floor.
        return (
            self.floor_margin if self.floor_margin is not None else Decimal("-Infinity"),
            self.market_margin if self.market_margin is not None else Decimal("-Infinity"),
        )


# --------------------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------------------


def all_in_cost(ask: Ask, cfg: SpreadConfig) -> tuple[Decimal, dict]:
    tax = money(ask.price * cfg.sales_tax_rate)
    grading = cfg.grading_cost if ask.is_raw else ZERO
    total = money(ask.price + cfg.shipping + tax + cfg.vault_intake_cost + grading)
    return total, {
        "ask": str(ask.price),
        "shipping": str(cfg.shipping),
        "sales_tax_est": str(tax),
        "vault_intake_cost": str(cfg.vault_intake_cost),
        "grading_cost": str(grading),
        "all_in_cost": str(total),
    }


def exit_market(sales: list[SaleObs], cfg: SpreadConfig, now: datetime) -> tuple[Decimal | None, dict]:
    """Median of sales inside the window, net of platform fee. None if below `min_sales`."""
    cutoff = now - cfg.sales_window
    recent = sorted((s for s in sales if s.at >= cutoff), key=lambda s: s.at)
    detail = {
        "sales_in_window": len(recent),
        "min_sales": cfg.min_sales,
        "window_days": cfg.sales_window.days,
        "sales": [(str(s.price), s.at.isoformat()) for s in recent],
    }
    if len(recent) < cfg.min_sales:
        return None, {**detail, "reason": "insufficient_liquidity"}
    med = Decimal(median(s.price for s in recent))
    net = money(med * (1 - cfg.platform_fee_rate))
    return net, {
        **detail,
        "median": str(med),
        "platform_fee_rate": str(cfg.platform_fee_rate),
        "exit_market": str(net),
    }


def compute_spread(
    ask: Ask,
    floor: Floor | None,
    sales: list[SaleObs],
    cfg: SpreadConfig,
    now: datetime,
) -> Opportunity | Rejection:
    # Staleness first: a stale input is discarded, never extrapolated.
    if now - ask.as_of > cfg.max_age_ask:
        return Rejection("stale_ask", {"ask_as_of": ask.as_of.isoformat(), "max_age": str(cfg.max_age_ask)})
    if floor is not None and now - floor.as_of > cfg.max_age_floor:
        return Rejection(
            "stale_floor", {"floor_as_of": floor.as_of.isoformat(), "max_age": str(cfg.max_age_floor)}
        )
    fresh_sales = [s for s in sales if now - s.at <= cfg.max_age_sale]

    cost, cost_detail = all_in_cost(ask, cfg)
    mkt, mkt_detail = exit_market(fresh_sales, cfg, now)
    if floor is None and mkt is None:
        return Rejection("no_exit", {"cost": cost_detail, "market": mkt_detail})

    floor_margin = money(floor.value - cost) if floor else None
    market_margin = money(mkt - cost) if mkt is not None else None
    return Opportunity(
        listing_ref=ask.listing_ref,
        all_in_cost=cost,
        exit_floor=floor.value if floor else None,
        exit_market=mkt,
        floor_margin=floor_margin,
        market_margin=market_margin,
        calculation={
            "computed_at": now.isoformat(),
            "cost": cost_detail,
            "floor": (
                {"value": str(floor.value), "as_of": floor.as_of.isoformat(), "oracle": floor.oracle}
                if floor
                else None
            ),
            "market": mkt_detail,
            "floor_margin": str(floor_margin) if floor_margin is not None else None,
            "market_margin": str(market_margin) if market_margin is not None else None,
            "formula": "floor_margin = exit_floor - all_in_cost; market_margin = exit_market - all_in_cost",
        },
    )


def rank(opps: list[Opportunity]) -> list[Opportunity]:
    """Downside-protected deals first: floor_margin desc, then market_margin desc."""
    return sorted(opps, key=lambda o: o.sort_key, reverse=True)
