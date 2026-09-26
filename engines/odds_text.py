"""Parse the odds line Courtyard publishes inside each pack's description (Phase 0 Q3).

Real example (pkmn-starter-pack, 2026-09-26):
    "**Odds***: 45% $5-25 | 53% 25-50 | 1% $50-100 | 0.5% $100-200 | 0.5% Grail $200+"

Pure. Used by the manual-snapshot admin form: the owner reads the pack page in a browser and
pastes the line; nothing automated touches Courtyard's site (ToS §14.8).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

_SEG = re.compile(
    r"(?P<p>\d+(?:\.\d+)?)\s*%\s*"  # probability
    r"(?P<label>[A-Za-z][A-Za-z ]*?)?\s*"  # optional label ("Grail")
    r"\$?\s*(?P<lo>\d+(?:\.\d+)?)\s*"  # band low
    r"(?:-\s*\$?\s*(?P<hi>\d+(?:\.\d+)?)|(?P<plus>\+))"  # band high or "+"
)


@dataclass(frozen=True)
class OddsBand:
    label: str
    probability: Decimal  # 0..1
    low: Decimal
    high: Decimal | None  # None = open-ended ("$200+")


def parse_odds_line(text: str) -> list[OddsBand]:
    """Return bands in order. Raises ValueError if nothing parses or probabilities are absurd."""
    text = text.replace("**", "").replace("*", "")
    if ":" in text[:20]:
        text = text.split(":", 1)[1]
    bands = []
    for i, seg in enumerate(s.strip() for s in text.split("|")):
        m = _SEG.search(seg)
        if not m:
            continue
        lo = Decimal(m.group("lo"))
        hi = None if m.group("plus") else Decimal(m.group("hi"))
        label = (m.group("label") or "").strip() or f"band{i + 1}"
        bands.append(OddsBand(label, Decimal(m.group("p")) / 100, lo, hi))
    if not bands:
        raise ValueError("no odds bands found")
    total = sum(b.probability for b in bands)
    if not Decimal("0.98") <= total <= Decimal("1.02"):
        raise ValueError(f"probabilities sum to {total}")
    return bands
