"""Collector Crypt / Phygitals API workers and the Courtyard odds-text path, against real captures."""

from datetime import datetime
from decimal import Decimal as D

import httpx
import pytest
from conftest import load
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app import main as app_main
from app import services
from app.db import get_session
from config import settings
from engines.odds_text import parse_odds_line
from ingest import collectorcrypt_api, phygitals_api
from ingest.base import RawStore, run_worker
from models import Listing, Pack, PackOdds, RunStatus, Slab, Valuation


def _transport(routes: dict[str, object]) -> httpx.MockTransport:
    """Route by URL prefix; a callable value receives the query params."""

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.headers.get("user-agent"), "platforms require a User-Agent"
        for prefix, doc in sorted(routes.items(), key=lambda kv: -len(kv[0])):
            if str(req.url).startswith(prefix):
                body = doc(dict(req.url.params)) if callable(doc) else doc
                return httpx.Response(200, json=body) if body is not None else httpx.Response(404)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def _pool(params: dict):
    if params.get("code") != "pokemon_3000":
        return None  # other machines: no pool → band midpoint fallback
    return load(f"real/collectorcrypt/gacha_pool/pokemon_3000_{params['rarity']}.json")


def test_cc_marketplace_worker_creates_slabs_with_real_certs(session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "collectorcrypt_api_enabled", True)
    monkeypatch.setattr(settings, "collectorcrypt_pages_per_run", 1)
    page = load("real/collectorcrypt/marketplace_live_step100.json")
    with httpx.Client(transport=_transport({collectorcrypt_api.MARKETPLACE_URL: page})) as http:
        run = run_worker(
            collectorcrypt_api.marketplace_worker(), session, raw_store=RawStore(tmp_path), http=http
        )
    assert run.status == RunStatus.ok, run.error
    rows = page["filterNFtCard"]
    with_cert = [r for r in rows if r.get("gradingID")]
    assert run.fetched == len(rows) and len(with_cert) >= 50
    assert session.scalar(select(func.count(Slab.id))) == len(
        {(r["gradingCompany"], r["gradingID"]) for r in with_cert}
    )
    assert run.notes["by_method"].get("cert", 0) == len(with_cert)
    # insured values recorded as the buyback basis
    with_iv = sum(1 for r in rows if r.get("insuredValue") not in (None, ""))
    assert session.scalar(select(func.count(Valuation.id))) == with_iv - run.rejected
    assert run.rejected <= 2  # e.g. a promo with no set, no cert — refused, not guessed
    # replay → nothing new
    run2 = run_worker(
        collectorcrypt_api.marketplace_worker(),
        session,
        raw_store=RawStore(tmp_path),
        replay=RawStore(tmp_path).load(run.raw_path),
    )
    assert run2.inserted == 0 and session.scalar(select(func.count(Listing.id))) == len(rows) - run.rejected


def test_cc_gacha_odds_worker_measures_pool_and_keeps_stated_ev(session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "collectorcrypt_api_enabled", True)
    doc = load("real/collectorcrypt/gacha_machines_live.json")
    routes = {collectorcrypt_api.MACHINES_URL: doc, collectorcrypt_api.POOL_URL: _pool}
    with httpx.Client(transport=_transport(routes)) as http:
        run = run_worker(
            collectorcrypt_api.gacha_odds_worker(), session, raw_store=RawStore(tmp_path), http=http
        )
    assert run.status == RunStatus.ok, run.error
    n_packs = session.scalar(select(func.count(Pack.id)))
    assert n_packs == run.inserted and n_packs >= 50 and run.notes["pools_sampled"] == 4
    boss = session.scalar(select(Pack).where(Pack.slug == "pokemon_3000"))
    assert boss.price == D("3000") and boss.buyback_pct == D("0.93")
    odds = {o.tier: o for o in session.scalars(select(PackOdds).where(PackOdds.pack_id == boss.id))}
    assert (odds["epic"].probability, odds["epic"].value_low, odds["epic"].value_high) == (
        D("0.01"),
        D("15000"),
        D("303001"),
    )
    assert odds["epic"].sample_n == 23 and odds["common"].sample_n == 40
    assert odds["common"].stated_ev == D("3031.82")

    edges = {e["pack"].slug: e for e in services.pack_edges(session)}
    assert len(edges) == n_packs
    ev = edges["pokemon_3000"]["ev"]
    # measured from the pool sample (hand-computed from the fixtures): 2799.68 / 4829.88 / 8693.75 / 44639.13
    means = {"common": D("2799.68"), "uncommon": D("4829.88"), "rare": D("8693.75"), "epic": D("44639.13")}
    probs = {"common": D("0.75"), "uncommon": D("0.2"), "rare": D("0.04"), "epic": D("0.01")}
    ev_platform = sum(probs[t] * means[t] for t in probs)
    ev_buyback = sum(probs[t] * (means[t] * D("0.93")).quantize(D("0.01")) for t in probs)
    assert ev.ev_platform == ev_platform.quantize(D("0.0001")) and ev.ev_buyback == ev_buyback.quantize(
        D("0.0001")
    )
    assert ev.house_edge == (1 - ev_buyback / D("3000")).quantize(D("0.0001"))
    assert ev.stated_ev == D("3031.8200") and ev.stated_edge == (
        1 - D("0.93") * D("3031.82") / D("3000")
    ).quantize(D("0.0001"))
    assert all(t["method"] == "pool_sample" for t in ev.calculation["tiers"]) and not ev.warnings
    # a machine without a pool sample falls back to the band midpoint, and says so
    other = next(e for slug, e in edges.items() if slug != "pokemon_3000")
    assert all(t["method"] == "band_midpoint" for t in other["ev"].calculation["tiers"])
    assert edges["pokemon_3000"]["provenance"] == "api_json"
    # replay → idempotent
    run2 = run_worker(
        collectorcrypt_api.gacha_odds_worker(),
        session,
        raw_store=RawStore(tmp_path),
        replay=RawStore(tmp_path).load(run.raw_path),
    )
    assert run2.inserted == 0 and run2.updated == n_packs


def test_cc_workers_skip_when_gate_off(session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "collectorcrypt_api_enabled", False)
    run = run_worker(collectorcrypt_api.marketplace_worker(), session, raw_store=RawStore(tmp_path))
    assert run.status == RunStatus.skipped and "Q1" in run.error


def test_phygitals_workers_gated_then_real_shapes(session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "phygitals_api_enabled", False)
    run = run_worker(phygitals_api.packs_worker(), session, raw_store=RawStore(tmp_path))
    assert run.status == RunStatus.skipped and "written consent" in run.error
    monkeypatch.setattr(settings, "phygitals_api_enabled", True)
    monkeypatch.setattr(settings, "phygitals_pages_per_run", 1)
    packs = load("real/phygitals/vm_available_live.json")
    listings = load("real/phygitals/marketplace_listings_live_p1.json")
    with httpx.Client(
        transport=_transport({phygitals_api.PACKS_URL: packs, phygitals_api.LISTINGS_URL: listings})
    ) as http:
        r1 = run_worker(phygitals_api.packs_worker(), session, raw_store=RawStore(tmp_path), http=http)
        r2 = run_worker(phygitals_api.listings_worker(), session, raw_store=RawStore(tmp_path), http=http)
    assert r1.status == RunStatus.ok and r2.status == RunStatus.ok, (r1.error, r2.error)
    mythic = session.scalar(select(Pack).where(Pack.slug == "10-mythic-ocvlnz"))
    odds = {o.tier: o for o in session.scalars(select(PackOdds).where(PackOdds.pack_id == mythic.id))}
    assert odds["Mythic"].probability == D("0.1") and odds["Common"].value_high == D("100")
    assert mythic.buyback_pct == D("0.85") and mythic.price == D("100")
    assert r2.fetched == len(listings["listings"]) and r2.rejected == 0


def test_courtyard_odds_line_parses_real_text():
    bands = parse_odds_line(
        "**Odds***: 45% $5-25 | 53% 25-50 | 1% $50-100 | 0.5% $100-200 | 0.5% Grail $200+"
    )
    assert [(b.probability, b.low, b.high) for b in bands] == [
        (D("0.45"), D(5), D(25)), (D("0.53"), D(25), D(50)), (D("0.01"), D(50), D(100)),
        (D("0.005"), D(100), D(200)), (D("0.005"), D(200), None),
    ]  # fmt: skip
    assert bands[4].label == "Grail"
    master = parse_odds_line("46.5% $50-70 | 33% $70-100 | 16% $100-250 | 4% $250-800 | 0.5% $800+")
    assert sum(b.probability for b in master) == D("1.000")
    with pytest.raises(ValueError):
        parse_odds_line("nothing here")
    with pytest.raises(ValueError):
        parse_odds_line("50% $1-2 | 10% $2-3")


def test_manual_odds_form_records_snapshot_with_provenance(session):
    app_main.app.dependency_overrides[get_session] = lambda: session
    c = TestClient(app_main.app)
    assert c.get("/admin/odds").status_code == 200
    r = c.post(
        "/admin/odds",
        data={
            "source_key": "courtyard", "slug": "pkmn-starter-pack", "name": "Pokémon Starter Pack",
            "price": "25", "buyback_pct": "0.90",
            "odds_text": "**Odds***: 45% $5-25 | 53% 25-50 | 1% $50-100 | 0.5% $100-200 | 0.5% Grail $200+",
        },
    )  # fmt: skip
    assert r.status_code == 200 and "saved" in r.text
    pack = session.scalar(select(Pack).where(Pack.slug == "pkmn-starter-pack"))
    odds = session.scalars(select(PackOdds).where(PackOdds.pack_id == pack.id)).all()
    assert len(odds) == 5 and all(o.provenance == "manual_snapshot" for o in odds)
    edge = next(e for e in services.pack_edges(session) if e["pack"].slug == "pkmn-starter-pack")
    # bands valued at midpoint, open band at its floor: 15/37.5/75/150/200 × 0.9 buyback
    ev_bb = sum(
        D(p) * (D(m) * D("0.9")).quantize(D("0.01"))
        for p, m in [("0.45", "15"), ("0.53", "37.5"), ("0.01", "75"), ("0.005", "150"), ("0.005", "200")]
    )
    assert edge["ev"].ev_buyback == ev_bb.quantize(D("0.0001"))
    assert isinstance(edge["as_of"], datetime)
    app_main.app.dependency_overrides.clear()
