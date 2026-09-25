"""Alert fan-out (plan §8): don't point every subscriber at the same single listing.

Pure. Given an alert, the eligible subscribers, and a policy, decide who is told and when:
  * at most `per_listing_cap` subscribers per alert,
  * chosen by a deterministic rotation seeded from the alert, so no subscriber is always first,
  * each successive recipient staggered by `stagger_seconds`.
Subscribers whose preferences exclude the card (game, grader, threshold) are not eligible.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal


@dataclass(frozen=True)
class SubPref:
    subscriber_id: int
    floor_margin_min: Decimal
    games: tuple[str, ...] | None = None  # None = all
    graders: tuple[str, ...] | None = None


@dataclass(frozen=True)
class AlertFacts:
    alert_id: int
    listing_key: str  # stable per listing so re-alerts rotate consistently
    floor_margin: Decimal
    game: str | None
    grader: str | None


@dataclass(frozen=True)
class Assignment:
    subscriber_id: int
    due_at: datetime
    position: int


def eligible(sub: SubPref, a: AlertFacts) -> bool:
    if a.floor_margin < sub.floor_margin_min:
        return False
    if sub.games is not None and (a.game or "") not in sub.games:
        return False
    return not (sub.graders is not None and (a.grader or "") not in sub.graders)


def rotation_offset(listing_key: str, n: int) -> int:
    """Deterministic start index: same listing → same rotation, different listings → spread."""
    if n == 0:
        return 0
    h = hashlib.sha256(listing_key.encode()).digest()
    return int.from_bytes(h[:4], "big") % n


def assign(
    a: AlertFacts,
    subs: list[SubPref],
    *,
    now: datetime,
    per_listing_cap: int,
    stagger_seconds: int,
) -> list[Assignment]:
    pool = sorted((s for s in subs if eligible(s, a)), key=lambda s: s.subscriber_id)
    if not pool or per_listing_cap <= 0:
        return []
    start = rotation_offset(a.listing_key, len(pool))
    chosen = [pool[(start + i) % len(pool)] for i in range(min(per_listing_cap, len(pool)))]
    return [
        Assignment(s.subscriber_id, now + timedelta(seconds=stagger_seconds * i), i)
        for i, s in enumerate(chosen)
    ]
