"""upsert(models) — idempotent persistence of NormalizedSlabs with identity resolution.

Given normalized records from any source, this:
  * finds or creates the `Card` by canonical key,
  * finds or creates the `Slab` by (grader, cert) when a cert is present,
  * records `MatchCandidate` rows for fuzzy hits against existing listings,
  * upserts the `Listing` and any `Valuation` supplied.

Nothing here decides a fuzzy match is true. That is the admin page's job (a human).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from engines.identity import (
    Method,
    NormalizedSlab,
    canonical_key,
    normalize_cert,
    normalize_game,
    normalize_number,
    normalize_set,
    resolve,
)
from models import Card, Listing, MatchCandidate, Slab, Source, Valuation, ValueType


@dataclass
class UpsertReport:
    fetched: int = 0
    inserted: int = 0
    updated: int = 0
    rejected: int = 0
    by_method: dict[str, int] = field(default_factory=dict)
    candidates: int = 0
    reasons: list[str] = field(default_factory=list)

    def bump(self, method: Method) -> None:
        self.by_method[method.value] = self.by_method.get(method.value, 0) + 1


def get_or_create_source(s: Session, key: str, name: str | None = None, chain: str | None = None) -> Source:
    src = s.scalar(select(Source).where(Source.key == key))
    if src is None:
        src = Source(key=key, name=name or key, chain=chain)
        s.add(src)
        s.flush()
    return src


def _get_or_create_card(s: Session, ns: NormalizedSlab, ck: str) -> Card:
    card = s.scalar(select(Card).where(Card.canonical_key == ck))
    if card is None:
        card = Card(
            canonical_key=ck,
            game=normalize_game(ns.game) or "unknown",
            set_name=normalize_set(ns.set_name) or "",
            number=normalize_number(ns.number),
            variant=ck.split("|")[3] if ck.split("|")[3] != "-" else None,
            grader=ns.grader if ns.is_graded else None,
            grade_num=ns.grade_num if ns.is_graded else None,
            display_name=ns.title or ns.name or ck,
            year=ns.year,
            language=ns.language,
            image_url=ns.image_url,
        )
        s.add(card)
        s.flush()
    elif not card.image_url and ns.image_url:
        card.image_url = ns.image_url
    return card


def _get_or_create_slab(s: Session, ns: NormalizedSlab, card: Card | None) -> Slab:
    cert = normalize_cert(ns.cert_number)
    slab = s.scalar(select(Slab).where(Slab.grader == ns.grader, Slab.cert_number == cert))
    if slab is None:
        slab = Slab(
            grader=ns.grader, cert_number=cert, grade_label=ns.grade_label, grade_num=ns.grade_num, card=card
        )
        s.add(slab)
        s.flush()
    elif slab.card_id is None and card is not None:
        slab.card = card
    return slab


def _known_from_listings(s: Session, exclude_source: str) -> list[tuple[Listing, NormalizedSlab]]:
    """Existing listings from *other* sources, rebuilt as NormalizedSlab for fuzzy scoring."""
    rows = s.scalars(select(Listing).join(Source).where(Source.key != exclude_source)).all()
    out = []
    for listing in rows:
        r = listing.raw or {}
        ns = r.get("_normalized")
        if ns:
            out.append((listing, NormalizedSlab(**{**ns, "raw": {}})))
    return out


def _snapshot(ns: NormalizedSlab) -> dict:
    d = ns.__dict__.copy()
    d.pop("raw", None)
    d["grade_num"] = str(ns.grade_num) if ns.grade_num is not None else None
    d["variant_tokens"] = list(ns.variant_tokens)
    return d


def _restore_grade(d: dict) -> dict:
    d = dict(d)
    d["grade_num"] = Decimal(d["grade_num"]) if d.get("grade_num") else None
    d["variant_tokens"] = tuple(d.get("variant_tokens") or ())
    return d


def upsert_slabs(
    s: Session,
    source_key: str,
    records: list[tuple[NormalizedSlab, Decimal | None, dict[ValueType, Decimal]]],
    *,
    seen_at: datetime | None = None,
) -> UpsertReport:
    """records: (slab, ask_price or None, {value_type: value}) per source row."""
    seen_at = seen_at or datetime.utcnow()
    src = get_or_create_source(s, source_key)
    rep = UpsertReport(fetched=len(records))

    known_rows = _known_from_listings(s, source_key)
    known = [NormalizedSlab(**_restore_grade(ns.__dict__ | {"raw": {}})) for _, ns in known_rows]
    by_ext = {ns.external_id: listing for listing, ns in known_rows}

    for ns, ask, values in records:
        if not ns.external_id or ns.external_id == "None":
            rep.rejected += 1
            rep.reasons.append(f"{source_key}: record without external_id ({ns.title!r})")
            continue

        res = resolve(ns, known, record_min=settings.fuzzy_record_min)
        rep.bump(res.method)
        ck = res.canonical or canonical_key(ns)
        card = _get_or_create_card(s, ns, ck) if ck else None
        slab = _get_or_create_slab(s, ns, card) if ns.has_cert else None
        if card is None and slab is None:
            rep.rejected += 1
            rep.reasons.append(f"{source_key}:{ns.external_id}: no cert and no canonical key")
            continue

        listing = s.scalar(
            select(Listing).where(Listing.source_id == src.id, Listing.external_id == ns.external_id)
        )
        raw = {"_normalized": _snapshot(ns), "_source": ns.raw}
        if listing is None:
            listing = Listing(
                source_id=src.id,
                external_id=ns.external_id,
                ask_price=ask if ask is not None else Decimal(0),
                currency="USDC",
                title=ns.title,
                first_seen=seen_at,
                last_seen=seen_at,
                raw=raw,
            )
            s.add(listing)
            rep.inserted += 1
        else:
            if ask is not None:
                listing.ask_price = ask
            listing.last_seen = seen_at
            listing.raw = raw
            rep.updated += 1
        listing.card_id = card.id if card else None
        listing.slab_id = slab.id if slab else None
        s.flush()

        for other_ext, score, why in res.candidates:
            other = by_ext.get(other_ext)
            if other is None or score < settings.fuzzy_record_min:
                continue
            exists = s.scalar(
                select(MatchCandidate).where(
                    MatchCandidate.left_kind == "listing",
                    MatchCandidate.left_id == listing.id,
                    MatchCandidate.right_kind == "listing",
                    MatchCandidate.right_id == other.id,
                )
            )
            if exists is None:
                s.add(
                    MatchCandidate(
                        left_kind="listing",
                        left_id=listing.id,
                        right_kind="listing",
                        right_id=other.id,
                        confidence=score,
                        method="fuzzy_title",
                        explanation=why,
                    )
                )
                rep.candidates += 1

        for vtype, value in (values or {}).items():
            s.add(
                Valuation(
                    source_id=src.id,
                    card_id=card.id if card else None,
                    slab_id=slab.id if slab else None,
                    value_type=vtype,
                    value=value,
                    currency="USD",
                    as_of=seen_at,
                )
            )
    s.flush()
    return rep
