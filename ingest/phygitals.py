"""Phygitals (Solana) — normalizer for marketplace listing rows.

Data-license status: on-chain approved; `api.phygitals.com` **excluded until written
permission** (Phase 0 Q2). This normalizer replays captured fixtures only.

Observed metadata keys: Name, Set, Type, Rarity, Grade ("PSA 10" / "CGC 10.0" / "Ungraded"),
Title, Language. No cert number in the capture. Prices are micro-USDC strings.
"""

from __future__ import annotations

import re
from decimal import Decimal

from engines.identity import NormalizedSlab, normalize_grader, parse_grade

SOURCE_KEY = "phygitals"

_TITLE_RE = re.compile(r"^(?P<year>\d{4})\s+(?P<name>.+?)\s+(?P<set>.+?)\s+#(?P<number>[\w-]+)$")


def _meta(row: dict) -> dict[str, str]:
    return {m["key"]: str(m["value"]) for m in row.get("metadata", []) if m.get("value") is not None}


def normalize_listing(row: dict) -> tuple[NormalizedSlab, Decimal | None]:
    """One listing → (slab, ask_price_usdc)."""
    meta = _meta(row)
    title = meta.get("Title") or row.get("name", "")
    parsed = _TITLE_RE.match(title)
    p = parsed.groupdict() if parsed else {}
    grade_label = meta.get("Grade")
    grade_num, _ = parse_grade(grade_label)
    grader_word = grade_label.split()[0] if grade_label and grade_num is not None else None
    price = row.get("price")
    ask = Decimal(str(price)) / Decimal(1_000_000) if price not in (None, "") else None
    slab = NormalizedSlab(
        source=SOURCE_KEY,
        external_id=str(row.get("address") or row.get("slug")),
        title=title,
        game=meta.get("Type"),
        set_name=meta.get("Set") or p.get("set"),
        number=p.get("number"),
        name=meta.get("Name") or p.get("name"),
        year=int(p["year"]) if p.get("year") else None,
        language=meta.get("Language"),
        variant_tokens=tuple(v for v in (meta.get("Rarity"),) if v),
        grader=normalize_grader(grader_word),
        cert_number=None,
        grade_label=grade_label,
        grade_num=grade_num,
        image_url=row.get("image"),
        raw=row,
    )
    return slab, ask


def normalize_page(doc: dict) -> list[tuple[NormalizedSlab, Decimal | None]]:
    return [normalize_listing(r) for r in doc.get("listings", [])]
