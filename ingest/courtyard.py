"""Courtyard (Polygon) — normalizers for the two record shapes we hold real captures of.

Approved data path (docs/data-licenses.md): on-chain events + the tokenURI each token
points at. `api.courtyard.io/orderbook/*` is **excluded**; its normalizer exists only so a
captured fixture can be replayed and so the shape is documented.
"""

from __future__ import annotations

from decimal import Decimal

from engines.identity import NormalizedSlab, normalize_grader, parse_grade

SOURCE_KEY = "courtyard"
REGISTRY = "0x251BE3A17Af4892035C37ebf5890F4a4D889dcAD"

_TYPED = {
    "Grader",
    "Serial",
    "Grade",
    "Category",
    "Year",
    "Set",
    "Title/Subject",
    "Language",
    "Card Number",
    "Event",
}


def _attrs(attributes: list[dict]) -> tuple[dict[str, str], tuple[str, ...]]:
    """Split attributes into typed fields and the untyped variant tokens ('Holo', 'Full Art')."""
    typed: dict[str, str] = {}
    variants: list[str] = []
    for a in attributes or []:
        key = a.get("trait_type") or a.get("name") or ""
        val = a.get("value")
        if val is None:
            continue
        if key in _TYPED:
            typed[key] = str(val)
        elif not key:
            variants.append(str(val))
    return typed, tuple(variants)


def _build(
    external_id: str, title: str, attributes: list[dict], image: str | None, raw: dict
) -> NormalizedSlab:
    t, variants = _attrs(attributes)
    grade_num, _ = parse_grade(t.get("Grade"))
    year = int(t["Year"]) if t.get("Year", "").isdigit() else None
    return NormalizedSlab(
        source=SOURCE_KEY,
        external_id=external_id,
        title=title,
        game=t.get("Category"),
        set_name=t.get("Set"),
        number=t.get("Card Number"),
        name=t.get("Title/Subject"),
        year=year,
        language=t.get("Language"),
        variant_tokens=variants,
        grader=normalize_grader(t.get("Grader")),
        cert_number=t.get("Serial"),
        grade_label=t.get("Grade"),
        grade_num=grade_num,
        image_url=image,
        raw=raw,
    )


def normalize_metadata(doc: dict) -> NormalizedSlab:
    """tokenURI `metadata.json` (fixtures/real/courtyard/metadata_*.json)."""
    token = doc.get("token_info", {})
    return _build(
        external_id=str(token.get("token_id") or doc.get("name")),
        title=doc.get("name", ""),
        attributes=doc.get("attributes", []),
        image=doc.get("image"),
        raw=doc,
    )


def normalize_orderbook_asset(doc: dict) -> tuple[NormalizedSlab, Decimal | None]:
    """`/orderbook/assets/{poi}` → (slab, fmv_estimate_usd). Replay-only; source excluded."""
    a = doc.get("asset", doc)
    slab = _build(
        external_id=str(a.get("token_id") or a.get("proof_of_integrity")),
        title=a.get("title", ""),
        attributes=a.get("attributes", []),
        image=None,
        raw=doc,
    )
    fmv = a.get("fmv_estimate_usd")
    return slab, (Decimal(str(fmv)) if fmv is not None else None)
