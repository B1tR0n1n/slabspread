"""Paid tier (plan §8) — Sell lane. Gated on evidence and paperwork, enforced in code.

`launch_gate()` must pass before any signup or checkout route does anything:
  1. SLABSPREAD_PAID_TIER_ENABLED
  2. the ledger shows ≥ launch_min_calibrated_trades closed trades with a prediction
  3. SLABSPREAD_LAUNCH_LICENSES_CONFIRMED  (every data license permits a commercial derived product)
  4. SLABSPREAD_LAUNCH_TERMS_REVIEWED      (ToS + privacy reviewed by a professional)
Stripe handles cards; we never see a card number. Webhooks are signature-verified.
"""

from __future__ import annotations

from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.ledger import calibration
from config import settings
from engines import fanout
from models import Alert, Card, Listing, Subscriber, SubscriberAlert, SubStatus, Trade

router = APIRouter()


class LaunchBlocked(Exception):
    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def launch_gate(s: Session) -> None:
    reasons = []
    if not settings.paid_tier_enabled:
        reasons.append("SLABSPREAD_PAID_TIER_ENABLED is off")
    calib = calibration(s.scalars(select(Trade)).all())
    if calib.get("n", 0) < settings.launch_min_calibrated_trades:
        reasons.append(
            f"ledger has {calib.get('n', 0)} calibrated trades; "
            f"{settings.launch_min_calibrated_trades} required"
        )
    if not settings.launch_licenses_confirmed:
        reasons.append(
            "data licenses not confirmed for a commercial derived-data product (docs/data-licenses.md)"
        )
    if not settings.launch_terms_reviewed:
        reasons.append("terms of service and privacy policy not yet professionally reviewed")
    if not (settings.stripe_secret_key and settings.stripe_price_id and settings.stripe_webhook_secret):
        reasons.append("Stripe keys / price / webhook secret not configured")
    if reasons:
        raise LaunchBlocked(reasons)


def _gate_or_503(s: Session) -> None:
    try:
        launch_gate(s)
    except LaunchBlocked as e:
        raise HTTPException(503, "paid tier not launched: " + "; ".join(e.reasons)) from e


# --------------------------------------------------------------------------------------
# Signup + checkout
# --------------------------------------------------------------------------------------


@router.get("/subscribe", response_class=HTMLResponse)
def subscribe_page(request: Request, s: Session = Depends(get_session)):
    _gate_or_503(s)
    from app.main import templates

    return templates.TemplateResponse(request, "subscribe.html", {})


@router.post("/subscribe")
def subscribe(
    request: Request,
    email: str = Form(...),
    floor_margin_min: str = Form("10"),
    games: str = Form(""),
    graders: str = Form(""),
    accept_terms: str = Form(...),
    s: Session = Depends(get_session),
):
    _gate_or_503(s)
    if accept_terms != "yes":
        raise HTTPException(400, "terms must be accepted")
    email = email.strip().lower()
    sub = s.scalar(select(Subscriber).where(Subscriber.email == email))
    if sub is None:
        sub = Subscriber(email=email)
        s.add(sub)
    sub.floor_margin_min = floor_margin_min or "10"
    sub.games = [g.strip() for g in games.split(",") if g.strip()] or None
    sub.graders = [g.strip().upper() for g in graders.split(",") if g.strip()] or None
    sub.accepted_terms_at = datetime.utcnow()
    s.flush()
    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        customer_email=email,
        client_reference_id=str(sub.id),
        success_url=f"{settings.site_base_url}/subscribed",
        cancel_url=f"{settings.site_base_url}/subscribe",
    )
    return RedirectResponse(session.url, status_code=303)


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, s: Session = Depends(get_session)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(400, "bad signature") from e
    apply_stripe_event(s, event)
    return {"ok": True}


def apply_stripe_event(s: Session, event) -> None:
    """Pure-ish mapping from Stripe events to subscriber status. Called by the webhook and tests."""
    kind, obj = event["type"], event["data"]["object"]
    if kind == "checkout.session.completed":
        sub = s.get(Subscriber, int(obj.get("client_reference_id") or 0))
        if sub:
            sub.stripe_customer_id = obj.get("customer")
            sub.stripe_subscription_id = obj.get("subscription")
            sub.status = SubStatus.active
    elif kind in ("customer.subscription.updated", "customer.subscription.deleted"):
        sub = s.scalar(select(Subscriber).where(Subscriber.stripe_customer_id == obj.get("customer")))
        if sub:
            status = obj.get("status")
            sub.status = (
                SubStatus.canceled
                if kind.endswith("deleted") or status == "canceled"
                else SubStatus.past_due
                if status in ("past_due", "unpaid")
                else SubStatus.active
            )
    elif kind == "invoice.payment_failed":
        sub = s.scalar(select(Subscriber).where(Subscriber.stripe_customer_id == obj.get("customer")))
        if sub:
            sub.status = SubStatus.past_due
    s.flush()


# --------------------------------------------------------------------------------------
# Fan-out: alerts → subscribers, capped and staggered
# --------------------------------------------------------------------------------------


def fan_out(s: Session, alert: Alert, now: datetime) -> list[SubscriberAlert]:
    card = s.get(Card, alert.card_id) if alert.card_id else None
    listing = s.get(Listing, alert.listing_id)
    facts = fanout.AlertFacts(
        alert_id=alert.id,
        listing_key=f"{listing.source_id}:{listing.external_id}" if listing else str(alert.listing_id),
        floor_margin=alert.floor_margin or 0,
        game=card.game if card else None,
        grader=card.grader if card else None,
    )
    subs = [
        fanout.SubPref(
            x.id,
            x.floor_margin_min,
            tuple(x.games) if x.games else None,
            tuple(x.graders) if x.graders else None,
        )
        for x in s.scalars(select(Subscriber).where(Subscriber.status == SubStatus.active))
    ]
    rows = []
    for a in fanout.assign(
        facts,
        subs,
        now=now,
        per_listing_cap=settings.fanout_per_listing_cap,
        stagger_seconds=settings.fanout_stagger_seconds,
    ):
        exists = s.scalar(
            select(SubscriberAlert).where(
                SubscriberAlert.subscriber_id == a.subscriber_id, SubscriberAlert.alert_id == alert.id
            )
        )
        if exists:
            continue
        row = SubscriberAlert(subscriber_id=a.subscriber_id, alert_id=alert.id, due_at=a.due_at)
        s.add(row)
        rows.append(row)
    s.flush()
    return rows


def due_deliveries(s: Session, now: datetime) -> list[SubscriberAlert]:
    return s.scalars(
        select(SubscriberAlert).where(SubscriberAlert.sent_at.is_(None), SubscriberAlert.due_at <= now)
    ).all()


def subscriber_count(s: Session) -> int:
    return s.scalar(select(func.count(Subscriber.id)).where(Subscriber.status == SubStatus.active)) or 0
