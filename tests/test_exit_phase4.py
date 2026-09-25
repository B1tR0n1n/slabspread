"""Phase 4 exit test (plan §6):

  owner can go from alert → manual purchase → ledger entry → realized P&L in under two
  minutes of UI time.

Measured here as the number of HTTP round trips and typed fields: 1 click to the prefilled
form, 0 required fields to change, 1 save, 1 close. Plus: dashboard views render from DB,
alerts honour threshold and cooldown, auth guards every private route.
"""

from datetime import datetime, timedelta
from decimal import Decimal as D

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import alerts, auth, services
from app import main as app_main
from app.db import get_session
from config import settings
from models import (
    Alert,
    Card,
    Listing,
    Sale,
    Source,
    Trade,
    Valuation,
    ValueType,
)

NOW = datetime(2026, 9, 25, 12, 0)


@pytest.fixture
def seeded(session):
    """One card listed on Courtyard, insured on Collector Crypt, with three recent CC sales."""
    cy = Source(key="courtyard", name="Courtyard", chain="polygon")
    cc = Source(key="collector_crypt", name="Collector Crypt", chain="solana")
    session.add_all([cy, cc])
    session.flush()
    card = Card(
        canonical_key="pokemon|base set|4|holo|PSA|10",
        game="pokemon",
        set_name="base set",
        number="4",
        variant="holo",
        grader="PSA",
        grade_num=D(10),
        display_name="1999 Base Set #4 Charizard Holo PSA 10",
    )
    session.add(card)
    session.flush()
    listing = Listing(
        source_id=cy.id,
        external_id="tok1",
        card_id=card.id,
        ask_price=D("100"),
        currency="USDC",
        url="https://courtyard.io/asset/x",
        title="Charizard PSA 10",
        first_seen=NOW - timedelta(hours=1),
        last_seen=NOW - timedelta(hours=1),
    )
    session.add(listing)
    # CC insured value 200 → floor = 200 × 0.85 = 170 ; all-in = 100 + 5 = 105 → floor margin 65
    session.add(
        Valuation(
            source_id=cc.id,
            card_id=card.id,
            value_type=ValueType.insured_value,
            value=D("200"),
            as_of=NOW - timedelta(hours=2),
        )
    )
    for i, p in enumerate([D("180"), D("200"), D("220")]):
        session.add(
            Sale(
                source_id=cc.id,
                external_id=f"s{i}",
                card_id=card.id,
                price=p,
                currency="USDC",
                sold_at=NOW - timedelta(days=i + 1),
            )
        )
    session.commit()
    return session, card, listing


def _client(session):
    app_main.app.dependency_overrides[get_session] = lambda: session
    return TestClient(app_main.app)


def test_floor_and_opportunity_from_db(seeded, monkeypatch):
    s, card, listing = seeded
    monkeypatch.setattr(settings, "spread_shipping", 5.0)
    floor = services.latest_floor(s, card.id)
    assert floor.value == D("170.00") and floor.oracle == "collector_crypt:insured_value*0.85"
    rows, rejected = services.opportunities(s, NOW)
    assert rejected == {} and len(rows) == 1
    o = rows[0].opp
    assert o.all_in_cost == D("105.00") and o.floor_margin == D("65.00")
    assert o.exit_market == D("188.00") and o.market_margin == D("83.00")  # median 200 × 0.94


def test_alert_threshold_and_cooldown(seeded, monkeypatch):
    s, card, listing = seeded
    monkeypatch.setattr(settings, "alert_floor_margin_min", 10.0)
    sent = []
    created = alerts.scan_and_deliver(s, NOW, send=lambda a, lst: sent.append(a) or "test")
    assert len(created) == 1 and created[0].channel == "test" and created[0].delivered_at is not None
    assert alerts.scan_and_deliver(s, NOW + timedelta(hours=1), send=lambda a, lst: "test") == []  # cooldown
    monkeypatch.setattr(settings, "alert_floor_margin_min", 999.0)
    assert (
        alerts.scan_and_deliver(s, NOW + timedelta(hours=24), send=lambda a, lst: "test") == []
    )  # threshold


def test_alert_to_ledger_to_pnl_in_four_requests(seeded, monkeypatch):
    s, card, listing = seeded
    monkeypatch.setattr(settings, "alert_floor_margin_min", 10.0)
    alerts.scan_and_deliver(s, NOW, send=lambda a, lst: "log")
    s.commit()
    a = s.scalar(select(Alert))
    c = _client(s)

    # 1. alerts page shows the button to the prefilled form
    page = c.get("/alerts")
    assert page.status_code == 200 and f"/ledger/new?from_alert={a.id}" in page.text

    # 2. prefilled form: no required field needs typing
    form = c.get(f"/ledger/new?from_alert={a.id}")
    assert form.status_code == 200
    assert (
        'value="100.00"' in form.text and 'value="65.00"' in form.text and "prefilled from alert" in form.text
    )

    # 3. save the purchase as prefilled (buy 100, fees 5 = shipping, intake 0)
    r = c.post(
        "/ledger",
        data={
            "description": "Charizard PSA 10",
            "bought_at": NOW.strftime("%Y-%m-%dT%H:%M"),
            "buy_price": "100.00",
            "buy_fees": "5.00",
            "intake_cost": "0",
            "alert_id": str(a.id),
            "card_id": str(card.id),
            "predicted_floor_margin": "65.00",
            "predicted_market_margin": "83.00",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    t = s.scalar(select(Trade))
    assert t.total_cost == D("105.00") and t.realized_pnl is None and t.alert_id == a.id

    # 4. close it at the buyback → realized P&L = 170 − 0 − 105 = 65.00, meeting the prediction
    r = c.post(
        f"/ledger/{t.id}/exit", data={"exit_kind": "buyback", "exit_price": "170.00", "exit_fees": "0"}
    )
    assert r.status_code == 200 and "65.00" in r.text
    s.refresh(t)
    assert t.realized_pnl == D("65.00")

    ledger_page = c.get("/ledger")
    assert "met prediction 1 (1.000)" in ledger_page.text
    csv = c.get("/ledger/export.csv")
    assert (
        csv.headers["content-type"].startswith("text/csv")
        and "65.00" in csv.text
        and "realized_pnl" in csv.text
    )
    app_main.app.dependency_overrides.clear()


def test_dashboard_views_render(seeded, monkeypatch):
    s, card, listing = seeded
    c = _client(s)
    for path in ["/", f"/cards/{card.id}", "/lag", "/packs", "/health/ingest", "/admin/matches"]:
        r = c.get(path)
        assert r.status_code == 200, path
    assert "Charizard" in c.get("/").text and "collector_crypt:insured_value*0.85" in c.get("/").text
    assert c.get("/cards/999999").status_code == 404
    app_main.app.dependency_overrides.clear()


def test_local_auth_guards_private_routes(seeded, monkeypatch):
    s, *_ = seeded
    monkeypatch.setattr(settings, "auth_mode", "local")
    monkeypatch.setattr(settings, "owner_email", "owner@example.com")
    monkeypatch.setattr(settings, "owner_password_hash", auth.make_hash("hunter2"))
    c = _client(s)
    r = c.get("/ledger", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/login")
    assert c.get("/health").status_code == 200  # public liveness
    assert c.post("/login", data={"email": "owner@example.com", "password": "wrong"}).status_code == 401
    assert c.post("/login", data={"email": "nobody@example.com", "password": "hunter2"}).status_code == 401
    r = c.post(
        "/login",
        data={"email": "Owner@Example.com", "password": "hunter2", "next": "/ledger"},
        follow_redirects=False,
    )
    assert r.status_code == 303 and r.headers["location"] == "/ledger"
    assert c.get("/ledger").status_code == 200
    c.post("/logout")
    assert c.get("/ledger", follow_redirects=False).status_code == 303
    app_main.app.dependency_overrides.clear()


def test_supabase_token_verification(monkeypatch):
    import jwt

    monkeypatch.setattr(settings, "supabase_jwt_secret", "s3cret")
    monkeypatch.setattr(settings, "owner_email", "owner@example.com")
    good = jwt.encode({"email": "owner@example.com", "aud": "authenticated"}, "s3cret", algorithm="HS256")
    assert auth.verify_supabase_token(good) == "owner@example.com"
    other = jwt.encode({"email": "intruder@example.com", "aud": "authenticated"}, "s3cret", algorithm="HS256")
    with pytest.raises(Exception) as e:
        auth.verify_supabase_token(other)
    assert e.value.status_code == 403
    forged = jwt.encode({"email": "owner@example.com", "aud": "authenticated"}, "wrong", algorithm="HS256")
    with pytest.raises(Exception) as e:
        auth.verify_supabase_token(forged)
    assert e.value.status_code == 401
