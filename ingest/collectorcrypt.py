"""Collector Crypt (Solana) — normalizer for `GET api.collectorcrypt.com/marketplace` rows.

Field notes from the real capture (fixtures/real/collectorcrypt/marketplace_page.json):
  - `serial`      is the CARD NUMBER ("051"), not the cert.
  - `gradingID`   is the cert number per Phase 0 evidence; absent in this capture. Accepted
                  when present, otherwise the row identifies by canonical key / fuzzy only.
  - `grade`       is a label ("GEM-MT 10", "MINT 9"); `gradeNum` was null in the capture.
  - `insuredValue` is the buyback basis (string). Emitted separately as a valuation.
  - `itemName`    "2026 #051 Pikachu PSA 9 Tef EN-Temporal Forces" — parsed only as a
                  fallback for fields the row omits.
"""

from __future__ import annotations

import re
from decimal import Decimal

from engines.identity import NormalizedSlab, normalize_grader, parse_grade

SOURCE_KEY = "collector_crypt"

_NAME_RE = re.compile(
    r"^(?P<year>\d{4})?\s*(?:#(?P<number>[\w-]+))?\s*(?P<name>.+?)\s+"
    r"(?P<grader>PSA|BGS|CGC|SGC|TAG|ACE)\s+(?P<grade>10|\d(?:\.5)?)\s*(?P<set>.*)$",
    re.IGNORECASE,
)


def parse_item_name(name: str) -> dict[str, str]:
    m = _NAME_RE.match(name or "")
    return {k: v for k, v in (m.groupdict() if m else {}).items() if v}


def normalize_row(row: dict) -> tuple[NormalizedSlab, Decimal | None]:
    """One `filterNFtCard[]` row → (slab, insured_value)."""
    parsed = parse_item_name(row.get("itemName", ""))
    grade_label = row.get("grade") or parsed.get("grade")
    grade_num, _ = parse_grade(grade_label)
    if grade_num is None and row.get("gradeNum") is not None:
        grade_num = Decimal(str(row["gradeNum"]))
    year = row.get("year") or (int(parsed["year"]) if parsed.get("year") else None)
    cert = row.get("gradingID") or row.get("certNumber")
    images = row.get("images") or {}
    slab = NormalizedSlab(
        source=SOURCE_KEY,
        external_id=str(row.get("nftAddress") or row.get("id")),
        title=row.get("itemName", ""),
        game=row.get("category"),
        set_name=row.get("set") or parsed.get("set"),
        number=row.get("serial") or parsed.get("number"),
        name=parsed.get("name"),
        year=int(year) if year else None,
        language=None,
        variant_tokens=(),
        grader=normalize_grader(row.get("gradingCompany") or parsed.get("grader")),
        cert_number=str(cert) if cert else None,
        grade_label=grade_label,
        grade_num=grade_num,
        image_url=images.get("front") or images.get("frontM") or images.get("frontS"),
        raw=row,
    )
    iv = row.get("insuredValue")
    return slab, (Decimal(str(iv)) if iv not in (None, "") else None)


def normalize_page(doc: dict) -> list[tuple[NormalizedSlab, Decimal | None]]:
    return [normalize_row(r) for r in doc.get("filterNFtCard", [])]
