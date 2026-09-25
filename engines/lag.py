"""Lag detector (plan §5c) — Trade + Publish.

Compare the trend of *real* prices (on-chain + licensed sales) to the trend of a platform's
stated valuation for the same card. Alert when real prices fall X% while the platform value
stays flat for Y hours. Output is informational; a human decides what, if anything, to do.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from statistics import median

FOUR = Decimal("0.0001")


@dataclass(frozen=True)
class Point:
    at: datetime
    value: Decimal


@dataclass(frozen=True)
class LagConfig:
    real_window: timedelta = timedelta(days=14)  # trend window for real prices
    drop_pct: Decimal = Decimal("0.15")  # real prices must fall at least this much
    flat_hours: int = 48  # platform value must be flat for this long
    flat_tolerance_pct: Decimal = Decimal("0.02")  # "flat" = moved less than this
    min_real_points: int = 4  # need at least this many real observations (2 per half)


@dataclass(frozen=True)
class Trend:
    start_median: Decimal
    end_median: Decimal
    change_pct: Decimal
    n: int


@dataclass(frozen=True)
class LagAlert:
    real_change_pct: Decimal
    platform_change_pct: Decimal
    flat_since: datetime
    explanation: dict


def trend(points: list[Point], window: timedelta, now: datetime, *, min_points: int = 4) -> Trend | None:
    """Median of the first half of the window vs median of the second half."""
    cutoff = now - window
    pts = sorted((p for p in points if cutoff <= p.at <= now), key=lambda p: p.at)
    if len(pts) < min_points:
        return None
    mid = cutoff + window / 2
    first = [p.value for p in pts if p.at < mid]
    second = [p.value for p in pts if p.at >= mid]
    if len(first) < 2 or len(second) < 2:
        return None
    a, b = Decimal(median(first)), Decimal(median(second))
    if a == 0:
        return None
    return Trend(a, b, ((b - a) / a).quantize(FOUR, rounding=ROUND_HALF_UP), len(pts))


def flatness(points: list[Point], hours: int, now: datetime) -> tuple[Decimal | None, datetime | None]:
    """Relative range (max-min)/first of platform values over the last `hours`.
    Returns (change, earliest point in window) or (None, None) if nothing to judge."""
    cutoff = now - timedelta(hours=hours)
    pts = sorted((p for p in points if p.at >= cutoff), key=lambda p: p.at)
    if not pts:
        return None, None
    # Require the platform to have *had* a value at the start of the window: otherwise a
    # single fresh point would look perfectly flat.
    if pts[0].at > cutoff + timedelta(hours=hours) / 4:
        return None, None
    lo, hi = min(p.value for p in pts), max(p.value for p in pts)
    if lo == 0:
        return None, None
    return ((hi - lo) / lo).quantize(FOUR, rounding=ROUND_HALF_UP), pts[0].at


def detect_lag(real: list[Point], platform: list[Point], cfg: LagConfig, now: datetime) -> LagAlert | None:
    t = trend(real, cfg.real_window, now, min_points=cfg.min_real_points)
    if t is None or t.change_pct > -cfg.drop_pct:
        return None
    flat, since = flatness(platform, cfg.flat_hours, now)
    if flat is None or flat > cfg.flat_tolerance_pct:
        return None
    return LagAlert(
        real_change_pct=t.change_pct,
        platform_change_pct=flat,
        flat_since=since,
        explanation={
            "computed_at": now.isoformat(),
            "real": {
                "start_median": str(t.start_median),
                "end_median": str(t.end_median),
                "n": t.n,
                "window_days": cfg.real_window.days,
            },
            "platform": {"range_pct": str(flat), "flat_hours": cfg.flat_hours, "since": since.isoformat()},
            "thresholds": {"drop_pct": str(cfg.drop_pct), "flat_tolerance_pct": str(cfg.flat_tolerance_pct)},
            "note": (
                "informational — whether any action is appropriate and within platform terms "
                "is a human decision"
            ),
        },
    )
