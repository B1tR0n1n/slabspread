"""Phase 2 exit test (plan §4), the part runnable offline:

  "replaying stored raw data reproduces the same DB state"

plus: the workers run end-to-end against a mocked RPC, store raw payloads, advance cursors,
log counts, and /health/ingest shows last success + error rate per source.

The 48-hour scheduled soak is NOT covered here — it needs RPC access (phase0-findings §10).
"""

import json

import httpx
from conftest import load
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app import main as app_main
from app.db import get_session
from ingest import onchain_courtyard, onchain_solana_flows
from ingest.base import RawStore, get_cursor, run_worker
from models import IngestRun, OnchainEvent, RunStatus, Sale


def _polygon_transport(fixture: dict) -> httpx.MockTransport:
    """Answer eth_blockNumber / eth_getLogs / eth_getBlockByNumber from the fixture."""

    def handler(req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content)
        m, p = body["method"], body["params"]
        if m == "eth_blockNumber":
            res = hex(fixture["to_block"])
        elif m == "eth_getLogs":
            lo, hi = int(p[0]["fromBlock"], 16), int(p[0]["toBlock"], 16)
            res = [lg for lg in fixture["logs"] if lo <= int(lg["blockNumber"], 16) <= hi]
        elif m == "eth_getBlockByNumber":
            res = {"timestamp": hex(fixture["timestamps"][str(int(p[0], 16))])}
        else:
            return httpx.Response(400)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": res})

    return httpx.MockTransport(handler)


def _solana_transport(fixture: dict) -> httpx.MockTransport:
    by_sig = {t["transaction"]["signatures"][0]: t for t in fixture["transactions"]}

    def handler(req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content)
        m, p = body["method"], body["params"]
        if m == "getSignaturesForAddress":
            res = fixture["signatures"] if not p[1].get("until") else []
        elif m == "getTransaction":
            res = by_sig.get(p[0])
        else:
            return httpx.Response(400)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": res})

    return httpx.MockTransport(handler)


def _state(s):
    evs = s.scalars(select(OnchainEvent).order_by(OnchainEvent.tx_hash, OnchainEvent.log_index)).all()
    sales = s.scalars(select(Sale).order_by(Sale.external_id)).all()
    return (
        [
            (e.chain, e.tx_hash, e.log_index, e.kind, str(e.amount), e.currency, e.memo, e.token_ref)
            for e in evs
        ],
        [(x.external_id, str(x.price), x.currency) for x in sales],
    )


def test_courtyard_worker_live_then_replay_reproduces_state(session, tmp_path, monkeypatch):
    monkeypatch.setattr("config.settings.polygon_start_block", 88_175_000)
    fx = load("rpc/polygon_courtyard_logs.json")
    store = RawStore(tmp_path)
    w = onchain_courtyard.CourtyardOnchainWorker(rpc_url="http://polygon.test")
    with httpx.Client(transport=_polygon_transport(fx)) as http:
        run = run_worker(w, session, raw_store=store, http=http)
    assert run.status == RunStatus.ok, run.error
    assert (run.fetched, run.inserted) == (2, 2)
    assert get_cursor(session, w.key) == str(fx["to_block"])
    assert run.raw_path and store.load(run.raw_path)["logs"] == fx["logs"]
    live = _state(session)
    assert [e[3] for e in live[0]] == ["trade", "mint"] or sorted(e[3] for e in live[0]) == ["mint", "trade"]
    assert live[1] == [
        ("0x71f546e311d3196c0babe3dd76754c23710f298938b8953d6017cfd704e71c3a:0", "150.00", "USDC")
    ]

    # replay the stored payload → identical state, nothing inserted
    run2 = run_worker(w, session, raw_store=store, replay=store.load(run.raw_path))
    assert run2.status == RunStatus.ok and run2.inserted == 0 and run2.updated == 2
    assert _state(session) == live

    # second live poll: cursor advanced, no new blocks → empty, still ok
    with httpx.Client(transport=_polygon_transport(fx)) as http:
        run3 = run_worker(w, session, raw_store=store, http=http)
    assert run3.status == RunStatus.ok and run3.fetched == 0


def test_solana_workers_classify_flows_and_exclude_team(session, tmp_path):
    store = RawStore(tmp_path)
    cc = onchain_solana_flows.collectorcrypt_worker()
    cc.rpc_url = "http://solana.test"
    with httpx.Client(transport=_solana_transport(load("rpc/solana_collectorcrypt_flows.json"))) as http:
        run = run_worker(cc, session, raw_store=store, http=http)
    assert run.status == RunStatus.ok, run.error
    kinds = dict(
        session.execute(
            select(OnchainEvent.tx_hash, OnchainEvent.kind).where(
                OnchainEvent.source_key == "collector_crypt"
            )
        ).all()
    )
    assert kinds == {"sigOpen1": "pack_purchase", "sigBuyback1": "buyback"}  # team transfer excluded
    assert get_cursor(session, cc.key) == "sigTeam1"  # newest signature first

    phy = onchain_solana_flows.phygitals_worker()
    phy.rpc_url = "http://solana.test"
    with httpx.Client(transport=_solana_transport(load("rpc/solana_phygitals_flows.json"))) as http:
        run = run_worker(phy, session, raw_store=store, http=http)
    assert run.status == RunStatus.ok
    kinds = dict(
        session.execute(
            select(OnchainEvent.tx_hash, OnchainEvent.kind).where(OnchainEvent.source_key == "phygitals")
        ).all()
    )
    assert kinds == {"phySigOpen1": "pack_purchase", "phySigBuyback1": "buyback"}

    # replay both → no growth
    n = session.scalar(select(func.count(OnchainEvent.id)))
    for w, fx in [(cc, "rpc/solana_collectorcrypt_flows.json"), (phy, "rpc/solana_phygitals_flows.json")]:
        r = run_worker(w, session, raw_store=store, replay=load(fx))
        assert r.inserted == 0
    assert session.scalar(select(func.count(OnchainEvent.id))) == n


def test_health_ingest_page(session, tmp_path):
    store = RawStore(tmp_path)
    cc = onchain_solana_flows.collectorcrypt_worker()
    cc.rpc_url = "http://solana.test"
    with httpx.Client(transport=_solana_transport(load("rpc/solana_collectorcrypt_flows.json"))) as http:
        run_worker(cc, session, raw_store=store, http=http)
    from ingest.gated import platform_odds_worker

    run_worker(platform_odds_worker(), session, raw_store=store)
    session.commit()
    app_main.app.dependency_overrides[get_session] = lambda: session
    page = TestClient(app_main.app).get("/health/ingest")
    app_main.app.dependency_overrides.clear()
    assert page.status_code == 200
    assert "onchain_collectorcrypt" in page.text and "platform_odds" in page.text
    assert "skipped" in page.text and "Q1" in page.text
    assert session.scalar(select(func.count(IngestRun.id))) == 2
