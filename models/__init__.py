"""SQLAlchemy models — the core tables sketched in plan §3.

Identity lives in three places, in priority order:
  1. `Slab` (grader + cert_number)      — exact, a specific physical slab
  2. `Card.canonical_key`               — same card at same grade, across slabs
  3. `MatchCandidate`                   — fuzzy pairs awaiting a human verdict
"""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.utcnow()


class Source(Base):
    """Platform registry: courtyard, collector_crypt, phygitals, ebay, price_api…"""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    chain: Mapped[str | None] = mapped_column(String(20))
    # Row in docs/data-licenses.md must be `approved` before a worker writes here.
    license_status: Mapped[str] = mapped_column(String(20), default="provisional")


class Card(Base):
    """Canonical card key: (game, set, number, variant, grader, grade)."""

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_key: Mapped[str] = mapped_column(String(300), unique=True)
    game: Mapped[str] = mapped_column(String(40))
    set_name: Mapped[str] = mapped_column(String(160))
    number: Mapped[str | None] = mapped_column(String(40))
    variant: Mapped[str | None] = mapped_column(String(120))
    grader: Mapped[str | None] = mapped_column(String(20))
    grade_num: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    display_name: Mapped[str] = mapped_column(String(300))
    year: Mapped[int | None]
    language: Mapped[str | None] = mapped_column(String(20))
    image_url: Mapped[str | None] = mapped_column(String(500))

    slabs: Mapped[list[Slab]] = relationship(back_populates="card")


class Slab(Base):
    __tablename__ = "slabs"
    __table_args__ = (UniqueConstraint("grader", "cert_number", name="uq_slab_cert"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    grader: Mapped[str] = mapped_column(String(20))
    cert_number: Mapped[str] = mapped_column(String(40))
    grade_label: Mapped[str | None] = mapped_column(String(40))
    grade_num: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"))
    # Set by the PSA cert API (Phase 2) when available; None = unverified.
    cert_verified_at: Mapped[datetime | None] = mapped_column(DateTime)

    card: Mapped[Card | None] = relationship(back_populates="slabs")


class ListingStatus(enum.StrEnum):
    active = "active"
    delisted = "delisted"
    sold = "sold"


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_listing_source_ext"),
        Index("ix_listing_status_seen", "status", "last_seen"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    external_id: Mapped[str] = mapped_column(String(120))
    slab_id: Mapped[int | None] = mapped_column(ForeignKey("slabs.id"))
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"))
    ask_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    url: Mapped[str | None] = mapped_column(String(500))
    title: Mapped[str | None] = mapped_column(String(300))
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=_now)
    status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), default=ListingStatus.active)
    raw: Mapped[dict | None] = mapped_column(JSON)


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_sale_source_ext"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    external_id: Mapped[str] = mapped_column(String(160))  # tx hash or source id
    slab_id: Mapped[int | None] = mapped_column(ForeignKey("slabs.id"))
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"))
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    sold_at: Mapped[datetime] = mapped_column(DateTime)
    raw: Mapped[dict | None] = mapped_column(JSON)


class ValueType(enum.StrEnum):
    platform_fmv = "platform_fmv"
    buyback = "buyback"
    insured_value = "insured_value"
    licensed_mid = "licensed_mid"
    onchain_median = "onchain_median"


class Valuation(Base):
    """A value someone asserts for a card or slab, with who said it and when.

    `value_type` is the oracle. Public reports name it on every number (decisions.md).
    """

    __tablename__ = "valuations"
    __table_args__ = (Index("ix_valuation_lookup", "card_id", "value_type", "as_of"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"))
    slab_id: Mapped[int | None] = mapped_column(ForeignKey("slabs.id"))
    value_type: Mapped[ValueType] = mapped_column(Enum(ValueType))
    value: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    as_of: Mapped[datetime] = mapped_column(DateTime)


class Pack(Base):
    __tablename__ = "packs"
    __table_args__ = (UniqueConstraint("source_id", "slug", name="uq_pack_source_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    slug: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    buyback_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))


class PackOdds(Base):
    """One published odds bucket at one point in time (tier, probability, value band)."""

    __tablename__ = "pack_odds"

    id: Mapped[int] = mapped_column(primary_key=True)
    pack_id: Mapped[int] = mapped_column(ForeignKey("packs.id"))
    tier: Mapped[str] = mapped_column(String(60))
    probability: Mapped[Decimal] = mapped_column(Numeric(12, 10))
    value_low: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    value_high: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    as_of: Mapped[datetime] = mapped_column(DateTime)
    # How we obtained it: "api_json", "onchain", "manual_snapshot". Never "scrape".
    provenance: Mapped[str] = mapped_column(String(30))


class Verdict(enum.StrEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class MatchCandidate(Base):
    """A fuzzy pairing that a human must confirm. Never trusted automatically."""

    __tablename__ = "match_candidates"
    __table_args__ = (
        UniqueConstraint("left_kind", "left_id", "right_kind", "right_id", name="uq_match_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    left_kind: Mapped[str] = mapped_column(String(20))  # "listing" | "slab" | "card"
    left_id: Mapped[int]
    right_kind: Mapped[str] = mapped_column(String(20))
    right_id: Mapped[int]
    confidence: Mapped[float]
    method: Mapped[str] = mapped_column(String(40))
    explanation: Mapped[dict | None] = mapped_column(JSON)
    verdict: Mapped[Verdict] = mapped_column(Enum(Verdict), default=Verdict.pending)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# --------------------------------------------------------------------------------------
# Ingestion bookkeeping (plan §4)
# --------------------------------------------------------------------------------------


class RunStatus(enum.StrEnum):
    ok = "ok"
    error = "error"
    skipped = "skipped"


class IngestRun(Base):
    """One execution of one worker. /health/ingest reads this table."""

    __tablename__ = "ingest_runs"
    __table_args__ = (Index("ix_ingest_runs_source_started", "source_key", "started_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.ok)
    fetched: Mapped[int] = mapped_column(default=0)
    inserted: Mapped[int] = mapped_column(default=0)
    updated: Mapped[int] = mapped_column(default=0)
    rejected: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(String(2000))
    raw_path: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[dict | None] = mapped_column(JSON)


class IngestCursor(Base):
    """Where a worker resumes from (block number, signature, page token…)."""

    __tablename__ = "ingest_cursors"

    source_key: Mapped[str] = mapped_column(String(40), primary_key=True)
    cursor: Mapped[str] = mapped_column(String(200))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class OnchainEvent(Base):
    """Immutable ledger of decoded chain events. `sales` and pack flows derive from here."""

    __tablename__ = "onchain_events"
    __table_args__ = (
        UniqueConstraint("chain", "tx_hash", "log_index", name="uq_onchain_event"),
        Index("ix_onchain_kind_ts", "source_key", "kind", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(40))
    chain: Mapped[str] = mapped_column(String(20))
    tx_hash: Mapped[str] = mapped_column(String(120))
    log_index: Mapped[int] = mapped_column(default=0)
    block: Mapped[int | None]
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    # trade | mint | pack_purchase | buyback | transfer
    kind: Mapped[str] = mapped_column(String(30))
    token_ref: Mapped[str | None] = mapped_column(String(120))  # tokenId / mint address
    counterparty: Mapped[str | None] = mapped_column(String(120))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    currency: Mapped[str | None] = mapped_column(String(16))
    memo: Mapped[str | None] = mapped_column(String(300))
    raw: Mapped[dict | None] = mapped_column(JSON)
