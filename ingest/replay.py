"""Replay recorded fixtures into the configured database.

    python -m ingest.replay                 # fixtures/real + fixtures/corpus
    python -m ingest.replay fixtures/real   # one directory

This is the Phase 2 "replaying stored raw data reproduces the same DB state" path in
miniature: no network, idempotent, prints the per-source report each worker will log.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

from app.db import engine, session_scope
from ingest import collectorcrypt, courtyard, phygitals
from ingest.persist import upsert_slabs
from models import Base, ValueType

ROOT = Path(__file__).resolve().parent.parent


def _load_dir(d: Path) -> dict[str, list]:
    """Group normalized records by source key, choosing the normalizer from path/shape."""
    out: dict[str, list] = {"courtyard": [], "collector_crypt": [], "phygitals": []}
    for f in sorted(d.rglob("*.json")):
        if f.name == "truth.json":
            continue
        doc = json.loads(f.read_text())
        name = f.as_posix()
        if "courtyard" in name:
            docs = doc if isinstance(doc, list) else [doc]
            for d_ in docs:
                if "asset" in d_:
                    slab, fmv = courtyard.normalize_orderbook_asset(d_)
                    out["courtyard"].append((slab, None, {ValueType.platform_fmv: fmv} if fmv else {}))
                else:
                    out["courtyard"].append((courtyard.normalize_metadata(d_), None, {}))
        elif "collectorcrypt" in name:
            rows = doc.get("filterNFtCard", [])
            for (slab, iv), r in zip(collectorcrypt.normalize_page(doc), rows, strict=True):
                price = (r.get("listing") or {}).get("price")
                out["collector_crypt"].append(
                    (
                        slab,
                        Decimal(str(price)) if price is not None else None,
                        {ValueType.insured_value: iv} if iv is not None else {},
                    )
                )
        elif "phygitals" in name:
            for slab, ask in phygitals.normalize_page(doc):
                out["phygitals"].append((slab, ask, {}))
    return out


def main(paths: list[str]) -> None:
    Base.metadata.create_all(engine)
    dirs = [Path(p) for p in paths] or [ROOT / "fixtures" / "real", ROOT / "fixtures" / "corpus"]
    with session_scope() as s:
        for d in dirs:
            for source, records in _load_dir(d).items():
                if not records:
                    continue
                rep = upsert_slabs(s, source, records)
                print(
                    f"{d.name}/{source}: fetched={rep.fetched} inserted={rep.inserted} "
                    f"updated={rep.updated} rejected={rep.rejected} by_method={rep.by_method} "
                    f"candidates={rep.candidates}"
                )
                for r in rep.reasons:
                    print("   rejected:", r)


if __name__ == "__main__":
    main(sys.argv[1:])
