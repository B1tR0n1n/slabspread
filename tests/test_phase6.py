"""Phase 6 (plan §8): the paid tier is gated on evidence and paperwork; fan-out is capped and
staggered; Stripe events map to subscriber status without touching card data."""

from datetime import datetime, timedelta
from decimal import Decimal as D

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import paid
from app.db import get_session
from config import settings
from engines import fanout
from models import Alert, Card, ExitKind, Listing, Source, Subscriber, SubStatus, Trade

NOW = datetime(2026, 9, 25, 12, 0)


# --------------------------------------------------------------------------------------
# Fan-out engine (pure)
# --------------------------------------------------------------------------------------


def _subs(n):
    return [fanout.SubPref(i, D(10)) for i in range(1, n + 1)]


def test_fanout_caps_and_staggers():
    a = fanout.AlertFacts(1, "cy:tok1", D(50), "pokemon", "PSA")
    out = fanout.assign(a, _subs(12), now=NOW, per_listing_cap=5, stagger_seconds=90)
    assert len(out) == 5
    assert [x.due_at for x in out] == [NOW + timedelta(seconds=90 * i) for i in range(5)]
    assert len({x.subscriber_id for x in out}) == 5


def test_fanout_rotation_is_deterministic_and_spreads_across_listings():
    subs = _subs(20)
    a1 = fanout.AlertFacts(1, "cy:tok1", D(50), "pokemon", "PSA")
    a2 = fanout.AlertFacts(2, "cy:tok2", D(50), "pokemon", "PSA")
    first1 = [x.subscriber_id for x in fanout.assign(a1, subs, now=NOW, per_listing_cap=3, stagger_seconds=1)]
    again1 = [x.subscriber_id for x in fanout.assign(a1, subs, now=NOW, per_listing_cap=3, stagger_seconds=1)]
    first2 = [x.subscriber_id for x in fanout.assign(a2, subs, now=NOW, per_listing_cap=3, stagger_seconds=1)]
    assert first1 == again1 and first1 != first2


def test_fanout_respects_preferences():
    subs = [
        fanout.SubPref(1, D(10)),
        fanout.SubPref(2, D(100)),  # threshold too high
        fanout.SubPref(3, D(10), games=("baseball",)),  # wrong game
        fanout.SubPref(4, D(10), graders=("CGC",)),  # wrong grader
        fanout.SubPref(5, D(10), games=("pokemon",), graders=("PSA",)),
    ]
    a = fanout.AlertFacts(1, "k", D(50), "pokemon", "PSA")
    assert sorted(
        x.subscriber_id for x in fanout.assign(a, subs, now=NOW, per_listing_cap=10, stagger_seconds=0)
    ) == [1, 5]
    assert fanout.assign(a, subs, now=NOW, per_listing_cap=0, stagger_seconds=0) == []


# --------------------------------------------------------------------------------------
# Launch gate
# --------------------------------------------------------------------------------------


def _closed_trades(n):
    return [
        Trade(
            description=f"t{i}",
            bought_at=NOW,
            buy_price=D(100),
            exit_kind=ExitKind.buyback,
            exit_at=NOW,
            exit_price=D(120),
            predicted_floor_margin=D(15),
        )
        for i in range(n)
    ]


def test_launch_gate_lists_every_missing_condition(session):
    with pytest.raises(paid.LaunchBlocked) as e:
        paid.launch_gate(session)
    text = str(e.value)
    assert "PAID_TIER_ENABLED" in text and "calibrated trades" in text
    assert "licenses" in text and "professionally reviewed" in text and "Stripe" in text


def test_launch_gate_passes_only_with_evidence_and_paperwork(session, monkeypatch):
    for k, v in {
        "paid_tier_enabled": True,
        "launch_licenses_confirmed": True,
        "launch_terms_reviewed": True,
        "stripe_secret_key": "sk_test",
        "stripe_price_id": "price_x",
        "stripe_webhook_secret": "whsec_x",
        "launch_min_calibrated_trades": 3,
    }.items():
        monkeypatch.setattr(settings, k, v)
    session.add_all(_closed_trades(2))
    session.commit()
    with pytest.raises(paid.LaunchBlocked) as e:
        paid.launch_gate(session)
    assert "ledger has 2 calibrated trades; 3 required" in str(e.value)
    session.add_all(_closed_trades(1))
    session.commit()
    paid.launch_gate(session)  # no raise


def test_subscribe_routes_return_503_until_launched(session):
    app_main.app.dependency_overrides[get_session] = lambda: session
    c = TestClient(app_main.app)
    r = c.get("/subscribe")
    assert r.status_code == 503 and "not launched" in r.text
    r = c.post("/subscribe", data={"email": "a@b.c", "accept_terms": "yes"})
    assert r.status_code == 503
    app_main.app.dependency_overrides.clear()


# --------------------------------------------------------------------------------------
# Stripe event mapping + DB fan-out
# --------------------------------------------------------------------------------------


def test_stripe_events_drive_status(session):
    sub = Subscriber(email="a@b.c")
    session.add(sub)
    session.flush()
    paid.apply_stripe_event(
        session,
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {"client_reference_id": str(sub.id), "customer": "cus_1", "subscription": "sub_1"}
            },
        },
    )
    assert sub.status == SubStatus.active and sub.stripe_customer_id == "cus_1"
    paid.apply_stripe_event(
        session, {"type": "invoice.payment_failed", "data": {"object": {"customer": "cus_1"}}}
    )
    assert sub.status == SubStatus.past_due
    paid.apply_stripe_event(
        session,
        {
            "type": "customer.subscription.updated",
            "data": {"object": {"customer": "cus_1", "status": "active"}},
        },
    )
    assert sub.status == SubStatus.active
    paid.apply_stripe_event(
        session,
        {
            "type": "customer.subscription.deleted",
            "data": {"object": {"customer": "cus_1", "status": "canceled"}},
        },
    )
    assert sub.status == SubStatus.canceled


def test_db_fan_out_only_active_subscribers_and_idempotent(session, monkeypatch):
    monkeypatch.setattr(settings, "fanout_per_listing_cap", 2)
    monkeypatch.setattr(settings, "fanout_stagger_seconds", 60)
    src = Source(key="courtyard", name="Courtyard")
    session.add(src)
    session.flush()
    card = Card(
        canonical_key="k", game="pokemon", set_name="s", grader="PSA", grade_num=D(10), display_name="c"
    )
    session.add(card)
    session.flush()
    listing = Listing(source_id=src.id, external_id="tok", card_id=card.id, ask_price=D(100))
    session.add(listing)
    session.flush()
    alert = Alert(
        listing_id=listing.id, card_id=card.id, floor_margin=D(40), all_in_cost=D(105), created_at=NOW
    )
    session.add(alert)
    for i, st in enumerate(
        [SubStatus.active, SubStatus.active, SubStatus.active, SubStatus.pending, SubStatus.canceled]
    ):
        session.add(Subscriber(email=f"s{i}@x.y", status=st, floor_margin_min=D(10)))
    session.commit()
    rows = paid.fan_out(session, alert, NOW)
    assert len(rows) == 2 and rows[1].due_at == NOW + timedelta(seconds=60)
    assert paid.fan_out(session, alert, NOW) == []  # idempotent
    assert (
        len(paid.due_deliveries(session, NOW)) == 1
        and len(paid.due_deliveries(session, NOW + timedelta(seconds=60))) == 2
    )
    assert paid.subscriber_count(session) == 3
