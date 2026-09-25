"""FastAPI app: private dashboard, admin, ledger, health. Public site is generated separately."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app import auth, ledger, paid, services
from app.db import get_session
from config import settings
from ingest.base import recent_runs
from ingest.gated import EXCLUDED_UNTIL_LICENSED
from models import Alert, ExitKind, Listing, MatchCandidate, Slab, Trade, Verdict

app = FastAPI(title="SlabSpread", docs_url=None, redoc_url=None)
app.add_middleware(
    SessionMiddleware, secret_key=settings.session_secret, https_only=not settings.debug, same_site="lax"
)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

Owner = Depends(auth.require_owner)
app.include_router(paid.router)
DOCS = Path(__file__).resolve().parent.parent / "docs"


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse(
        request, "doc.html", {"title": "Terms of Service", "body": (DOCS / "terms.md").read_text()}
    )


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse(
        request, "doc.html", {"title": "Privacy Policy", "body": (DOCS / "privacy.md").read_text()}
    )


@app.get("/subscribed", response_class=HTMLResponse)
def subscribed(request: Request):
    return templates.TemplateResponse(
        request,
        "doc.html",
        {
            "title": "Subscribed",
            "body": (
                "Thanks. Alerts begin once Stripe confirms the subscription. "
                "Every alert is information; you place every order yourself."
            ),
        },
    )


def _parse_dt(v: str | None) -> datetime | None:
    return datetime.fromisoformat(v) if v else None


# --------------------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------------------


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/"):
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "mode": settings.auth_mode,
            "next": next,
            "supabase_url": settings.supabase_url,
            "anon_key": settings.supabase_anon_key,
        },
    )


@app.post("/login")
def login_local(request: Request, email: str = Form(...), password: str = Form(...), next: str = Form("/")):
    if settings.auth_mode != "local" or not auth.verify_local(email, password):
        raise HTTPException(401, "invalid credentials")
    request.session[auth.SESSION_KEY] = email.strip().lower()
    return RedirectResponse(next if next.startswith("/") else "/", status_code=303)


@app.post("/login/token")
def login_token(request: Request, access_token: str = Form(...)):
    if settings.auth_mode != "supabase":
        raise HTTPException(400, "not in supabase mode")
    request.session[auth.SESSION_KEY] = auth.verify_supabase_token(access_token)
    return {"ok": True}


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# --------------------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def home(request: Request, s: Session = Depends(get_session), who: str = Owner):
    rows, rejected = services.opportunities(s)
    pending = s.scalar(select(MatchCandidate).where(MatchCandidate.verdict == Verdict.pending)) is not None
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "rows": rows[:100],
            "rejected": rejected,
            "cfg": services.spread_config(),
            "has_pending": pending,
            "who": who,
        },
    )


@app.get("/cards/{card_id}", response_class=HTMLResponse)
def card(request: Request, card_id: int, s: Session = Depends(get_session), who: str = Owner):
    d = services.card_detail(s, card_id)
    if not d:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "card.html", d)


@app.get("/lag", response_class=HTMLResponse)
def lag_page(request: Request, s: Session = Depends(get_session), who: str = Owner):
    return templates.TemplateResponse(
        request, "lag.html", {"alerts": services.lag_alerts(s), "cfg": services.lag_config()}
    )


@app.get("/packs", response_class=HTMLResponse)
def packs_page(request: Request, s: Session = Depends(get_session), who: str = Owner):
    return templates.TemplateResponse(request, "packs.html", {"rows": services.pack_edges(s)})


@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request, s: Session = Depends(get_session), who: str = Owner):
    rows = s.execute(
        select(Alert, Listing)
        .join(Listing, Listing.id == Alert.listing_id)
        .order_by(Alert.created_at.desc())
        .limit(200)
    ).all()
    return templates.TemplateResponse(
        request, "alerts.html", {"rows": rows, "threshold": settings.alert_floor_margin_min}
    )


# --------------------------------------------------------------------------------------
# Ledger
# --------------------------------------------------------------------------------------


@app.get("/ledger", response_class=HTMLResponse)
def ledger_page(request: Request, s: Session = Depends(get_session), who: str = Owner):
    trades = ledger.all_trades(s)
    return templates.TemplateResponse(
        request,
        "ledger.html",
        {
            "trades": trades,
            "months": ledger.monthly_pnl(trades),
            "calib": ledger.calibration(trades),
            "ExitKind": ExitKind,
        },
    )


@app.get("/ledger/new", response_class=HTMLResponse)
def ledger_new(
    request: Request, from_alert: int | None = None, s: Session = Depends(get_session), who: str = Owner
):
    pre = (
        ledger.prefill_from_alert(s, from_alert)
        if from_alert
        else {"bought_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M")}
    )
    return templates.TemplateResponse(request, "ledger_new.html", {"pre": pre})


@app.post("/ledger")
def ledger_create(
    request: Request,
    description: str = Form(...),
    bought_at: str = Form(...),
    buy_price: Decimal = Form(...),
    buy_fees: Decimal = Form(Decimal(0)),
    intake_cost: Decimal = Form(Decimal(0)),
    intake_at: str = Form(""),
    source_key: str = Form(""),
    listing_ref: str = Form(""),
    card_id: int | None = Form(None),
    alert_id: int | None = Form(None),
    predicted_floor_margin: str = Form(""),
    predicted_market_margin: str = Form(""),
    notes: str = Form(""),
    s: Session = Depends(get_session),
    who: str = Owner,
):
    t = Trade(
        description=description,
        bought_at=datetime.fromisoformat(bought_at),
        buy_price=buy_price,
        buy_fees=buy_fees,
        intake_cost=intake_cost,
        intake_at=_parse_dt(intake_at),
        source_key=source_key or None,
        listing_ref=listing_ref or None,
        card_id=card_id,
        alert_id=alert_id,
        predicted_floor_margin=Decimal(predicted_floor_margin) if predicted_floor_margin else None,
        predicted_market_margin=Decimal(predicted_market_margin) if predicted_market_margin else None,
        notes=notes or None,
    )
    s.add(t)
    s.flush()
    return RedirectResponse("/ledger", status_code=303)


@app.post("/ledger/{trade_id}/exit", response_class=HTMLResponse)
def ledger_exit(
    request: Request,
    trade_id: int,
    exit_kind: str = Form(...),
    exit_price: Decimal = Form(...),
    exit_fees: Decimal = Form(Decimal(0)),
    exit_at: str = Form(""),
    s: Session = Depends(get_session),
    who: str = Owner,
):
    t = s.get(Trade, trade_id)
    if t is None:
        raise HTTPException(404)
    ledger.close_trade(t, ExitKind(exit_kind), exit_price, exit_fees, _parse_dt(exit_at) or datetime.utcnow())
    s.flush()
    return templates.TemplateResponse(request, "_trade_row.html", {"t": t, "ExitKind": ExitKind})


@app.get("/ledger/export.csv")
def ledger_export(s: Session = Depends(get_session), who: str = Owner):
    return PlainTextResponse(
        ledger.export_csv(ledger.all_trades(s)),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=slabspread-trades.csv"},
    )


# --------------------------------------------------------------------------------------
# Admin: match review
# --------------------------------------------------------------------------------------


def _pair(s: Session, mc: MatchCandidate) -> dict:
    return {"mc": mc, "left": s.get(Listing, mc.left_id), "right": s.get(Listing, mc.right_id)}


@app.get("/admin/matches", response_class=HTMLResponse)
def matches(request: Request, s: Session = Depends(get_session), verdict: str = "pending", who: str = Owner):
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
def decide(
    request: Request,
    mc_id: int,
    verdict: str = Form(...),
    s: Session = Depends(get_session),
    who: str = Owner,
):
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
        # the right-hand card onto the left-hand one. The orphan card row stays (audit trail).
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


# --------------------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/health/ingest", response_class=HTMLResponse)
def health_ingest(request: Request, s: Session = Depends(get_session), who: str = Owner):
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
