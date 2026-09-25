"""Alert delivery: email when SMTP is configured, otherwise the log. Alerts link to the
listing; nothing is bought automatically (ground rule 2)."""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.services import record_alerts
from config import settings
from models import Alert, Listing

log = logging.getLogger("alerts")


def render(a: Alert, listing: Listing) -> tuple[str, str]:
    subject = f"[SlabSpread] floor margin {a.floor_margin} on {listing.title or listing.external_id}"
    body = (
        f"Listing: {listing.title}\nURL: {listing.url or '(see dashboard)'}\n"
        f"Ask: {listing.ask_price} {listing.currency}\nAll-in cost: {a.all_in_cost}\n"
        f"Floor margin: {a.floor_margin}\nMarket margin: {a.market_margin}\n\n"
        f"Calculation: {a.calculation}\n\nThis is information, not a purchase. You decide."
    )
    return subject, body


def deliver(a: Alert, listing: Listing) -> str:
    subject, body = render(a, listing)
    if settings.smtp_host and settings.alert_email_to:
        msg = EmailMessage()
        msg["Subject"], msg["From"], msg["To"] = (
            subject,
            settings.alert_email_from or settings.smtp_user,
            settings.alert_email_to,
        )
        msg.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return "email"
    log.info("ALERT %s\n%s", subject, body)
    return "log"


def scan_and_deliver(s: Session, now: datetime | None = None, *, send=deliver) -> list[Alert]:
    created = record_alerts(s, now)
    for a in created:
        listing = s.get(Listing, a.listing_id)
        try:
            a.channel = send(a, listing)
            a.delivered_at = datetime.utcnow()
        except Exception as e:  # noqa: BLE001 — a mail outage must not lose the alert row
            log.exception("alert delivery failed")
            a.channel = f"failed:{type(e).__name__}"
    s.flush()
    return created
