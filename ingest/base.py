"""Shared worker plumbing (plan §4): rate limiting, backoff, raw capture, run ledger.

A worker is three functions and a key:

    fetch(ctx)            -> raw payload (JSON-serialisable)   # official API / RPC only
    normalize(raw)        -> list of model-shaped records
    upsert(session, recs) -> UpsertReport

`run_worker` wires them together, records an `IngestRun`, stores the raw payload
compressed for replay, and never lets one source's failure touch another's.
"""

from __future__ import annotations

import gzip
import json
import logging
import random
import time
import traceback
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from ingest.persist import UpsertReport
from models import IngestCursor, IngestRun, RunStatus

log = logging.getLogger("ingest")


class SourceNotApproved(RuntimeError):
    """Raised by workers whose docs/data-licenses.md row is not `approved`."""


# --------------------------------------------------------------------------------------
# Rate limiting and backoff — injectable clocks so tests never sleep
# --------------------------------------------------------------------------------------


class RateLimiter:
    """Token bucket. `rate` tokens/second, up to `burst` stored."""

    def __init__(self, rate: float, burst: int, *, clock=time.monotonic, sleep=time.sleep):
        self.rate, self.burst = rate, burst
        self._clock, self._sleep = clock, sleep
        self._tokens = float(burst)
        self._last = clock()

    def acquire(self) -> float:
        """Block until a token is available; return seconds waited."""
        now = self._clock()
        self._tokens = min(self.burst, self._tokens + (now - self._last) * self.rate)
        self._last = now
        waited = 0.0
        if self._tokens < 1:
            waited = (1 - self._tokens) / self.rate
            self._sleep(waited)
            self._tokens = 1.0
            self._last = self._clock()
        self._tokens -= 1
        return waited


def limiter_for(key: str) -> RateLimiter:
    rate, burst = settings.rate_limits.get(key, (1.0, 1))
    return RateLimiter(rate, burst)


RETRYABLE = (httpx.TransportError, httpx.TimeoutException)


def with_backoff(
    fn: Callable[[], Any],
    *,
    retries: int | None = None,
    base: float | None = None,
    cap: float | None = None,
    sleep=time.sleep,
    rng=random.random,
    retry_on: tuple[type[BaseException], ...] = RETRYABLE,
    retry_status: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Any:
    """Exponential backoff with full jitter. Retries transport errors and retryable HTTP codes."""
    retries = settings.max_retries if retries is None else retries
    base = settings.backoff_base_s if base is None else base
    cap = settings.backoff_max_s if cap is None else cap
    attempt = 0
    while True:
        try:
            return fn()
        except httpx.HTTPStatusError as e:
            if e.response.status_code not in retry_status or attempt >= retries:
                raise
        except retry_on:
            if attempt >= retries:
                raise
        delay = min(cap, base * (2**attempt)) * rng()
        log.warning("retry %d after %.2fs", attempt + 1, delay)
        sleep(delay)
        attempt += 1


# --------------------------------------------------------------------------------------
# Raw capture
# --------------------------------------------------------------------------------------


class RawStore:
    """Compressed JSON payloads under <raw_dir>/<source>/<UTC timestamp>.json.gz."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or settings.raw_dir)

    def save(self, source_key: str, payload: Any, *, at: datetime | None = None) -> Path:
        at = at or datetime.utcnow()
        d = self.root / source_key
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{at.strftime('%Y%m%dT%H%M%S%f')}.json.gz"
        with gzip.open(p, "wt", encoding="utf-8") as f:
            json.dump(payload, f, separators=(",", ":"), default=str)
        return p

    def load(self, path: str | Path) -> Any:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)

    def iter(self, source_key: str) -> Iterator[tuple[Path, Any]]:
        for p in sorted((self.root / source_key).glob("*.json.gz")):
            yield p, self.load(p)


# --------------------------------------------------------------------------------------
# Worker protocol and runner
# --------------------------------------------------------------------------------------


@dataclass
class Context:
    session: Session
    cursor: str | None
    limiter: RateLimiter
    http: httpx.Client
    notes: dict = field(default_factory=dict)


class Worker(Protocol):
    key: str
    limiter_key: str

    def fetch(self, ctx: Context) -> Any: ...
    def normalize(self, raw: Any) -> list[Any]: ...
    def upsert(self, session: Session, records: list[Any]) -> UpsertReport: ...
    def next_cursor(self, raw: Any) -> str | None: ...


def get_cursor(s: Session, key: str) -> str | None:
    row = s.get(IngestCursor, key)
    return row.cursor if row else None


def set_cursor(s: Session, key: str, cursor: str | None) -> None:
    if cursor is None:
        return
    row = s.get(IngestCursor, key)
    if row is None:
        s.add(IngestCursor(source_key=key, cursor=cursor))
    else:
        row.cursor = cursor


def run_worker(
    worker: Worker,
    session: Session,
    *,
    raw_store: RawStore | None = None,
    http: httpx.Client | None = None,
    replay: Any = None,
) -> IngestRun:
    """Execute one worker run. With `replay`, skip fetch and use that payload instead.

    Replaying the stored payload must reproduce the same DB state (plan §4 exit test).
    """
    run = IngestRun(source_key=worker.key, started_at=datetime.utcnow())
    session.add(run)
    # Commit the run row on its own so no write transaction is open while fetch() runs —
    # a long fetch would otherwise hold SQLite's write lock and starve the other workers.
    session.commit()
    raw_store = raw_store or RawStore()
    own_http = http is None
    http = http or httpx.Client(timeout=30)
    try:
        ctx = Context(
            session=session,
            cursor=get_cursor(session, worker.key),
            limiter=limiter_for(worker.limiter_key),
            http=http,
        )
        if replay is None:
            raw = worker.fetch(ctx)
            run.raw_path = str(raw_store.save(worker.key, raw))
        else:
            raw = replay
            run.notes = {"replay": True}
        records = worker.normalize(raw)
        rep = worker.upsert(session, records)
        run.fetched, run.inserted, run.updated, run.rejected = (
            rep.fetched,
            rep.inserted,
            rep.updated,
            rep.rejected,
        )
        run.notes = {
            **(run.notes or {}),
            **ctx.notes,
            "by_method": rep.by_method,
            "reasons": rep.reasons[:50],
        }
        if replay is None:
            set_cursor(session, worker.key, worker.next_cursor(raw))
        run.status = RunStatus.ok
        log.info(
            "%s ok fetched=%d inserted=%d updated=%d rejected=%d",
            worker.key,
            rep.fetched,
            rep.inserted,
            rep.updated,
            rep.rejected,
        )
    except SourceNotApproved as e:
        run.status, run.error = RunStatus.skipped, str(e)
        log.info("%s skipped: %s", worker.key, e)
    except Exception as e:  # noqa: BLE001 — one source's failure must not stop the others
        run.status, run.error = RunStatus.error, f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}"
        log.exception("%s failed", worker.key)
    finally:
        run.finished_at = datetime.utcnow()
        session.commit()
        if own_http:
            http.close()
    return run


def recent_runs(s: Session, limit_per_source: int = 20) -> dict[str, list[IngestRun]]:
    out: dict[str, list[IngestRun]] = {}
    rows = s.scalars(select(IngestRun).order_by(IngestRun.started_at.desc()).limit(2000)).all()
    for r in rows:
        bucket = out.setdefault(r.source_key, [])
        if len(bucket) < limit_per_source:
            bucket.append(r)
    return out
