"""FastAPI app. Phase 1 ships the match-candidate review page only."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from ingest.base import recent_runs
from ingest.gated import EXCLUDED_UNTIL_LICENSED
from models import Listing, MatchCandidate, Slab, Verdict

app = FastAPI(title="SlabSpread", docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _pair(s: Session, mc: MatchCandidate) -> dict:
    left = s.get(Listing, mc.left_id)
    right = s.get(Listing, mc.right_id)
    return {"mc": mc, "left": left, "right": right}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, s: Session = Depends(get_session)):
    pending = s.scalar(select(MatchCandidate).where(MatchCandidate.verdict == Verdict.pending))
    return templates.TemplateResponse(request, "home.html", {"has_pending": pending is not None})


@app.get("/admin/matches", response_class=HTMLResponse)
def matches(request: Request, s: Session = Depends(get_session), verdict: str = "pending"):
    try:
        v = Verdict(verdict)
    except ValueError as e:
        raise HTTPException(400, "unknown verdict") from e
    rows = s.scalars(
        select(MatchCandidate)
        .where(MatchCandidate.verdict == v)
        .order_by(MatchCandidate.confidence.desc())
        .limit(200)
    ).all()
    return templates.TemplateResponse(
        request,
        "matches.html",
        {"pairs": [_pair(s, mc) for mc in rows], "verdict": v.value, "verdicts": list(Verdict)},
    )


@app.post("/admin/matches/{mc_id}", response_class=HTMLResponse)
def decide(request: Request, mc_id: int, verdict: str = Form(...), s: Session = Depends(get_session)):
    mc = s.get(MatchCandidate, mc_id)
    if mc is None:
        raise HTTPException(404)
    try:
        mc.verdict = Verdict(verdict)
    except ValueError as e:
        raise HTTPException(400, "unknown verdict") from e
    mc.decided_at = datetime.utcnow()
    if mc.verdict == Verdict.accepted:
        # A human said these two listings are the same card: move everything that pointed at
        # the right-hand card onto the left-hand one. The orphan card row is left in place
        # (harmless, and keeps the audit trail of what the source originally said).
        left, right = s.get(Listing, mc.left_id), s.get(Listing, mc.right_id)
        if left and right:
            keep = left.card_id or right.card_id
            drop = right.card_id if left.card_id else None
            if keep and drop and keep != drop:
                for lst in s.scalars(select(Listing).where(Listing.card_id == drop)):
                    lst.card_id = keep
                for slab in s.scalars(select(Slab).where(Slab.card_id == drop)):
                    slab.card_id = keep
            left.card_id = right.card_id = keep
    s.flush()
    return templates.TemplateResponse(request, "_match_row.html", {**_pair(s, mc), "done": True})


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/health/ingest", response_class=HTMLResponse)
def health_ingest(request: Request, s: Session = Depends(get_session)):
    window = 20
    rows = []
    for key, runs in sorted(recent_runs(s, window).items()):
        errors = sum(r.status.value == "error" for r in runs)
        last_ok = next((r.finished_at for r in runs if r.status.value == "ok"), None)
        latest = runs[0]
        rows.append(
            {
                "key": key,
                "last_ok": last_ok.strftime("%Y-%m-%d %H:%M:%S") if last_ok else None,
                "last_status": latest.status.value,
                "error_rate": errors / len(runs),
                "counts": f"{latest.fetched} / {latest.inserted} / {latest.updated} / {latest.rejected}",
                "note": (latest.error or "")[:160] if latest.status.value != "ok" else (latest.notes or {}),
            }
        )
    return templates.TemplateResponse(
        request, "health_ingest.html", {"rows": rows, "window": window, "excluded": EXCLUDED_UNTIL_LICENSED}
    )
