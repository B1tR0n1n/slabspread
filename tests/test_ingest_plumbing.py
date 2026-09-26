"""Rate limiting, backoff, raw capture, and the run ledger — with injected clocks, no sleeping."""

import httpx
import pytest

from ingest.base import RateLimiter, RawStore, SourceNotApproved, limiter_for, run_worker, with_backoff
from ingest.gated import GatedWorker
from models import IngestRun, RunStatus


class FakeClock:
    def __init__(self):
        self.t = 0.0
        self.slept = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


def test_rate_limiter_token_bucket():
    clk = FakeClock()
    rl = RateLimiter(rate=2.0, burst=2, clock=clk.now, sleep=clk.sleep)
    assert rl.acquire() == 0 and rl.acquire() == 0  # burst
    waited = rl.acquire()  # bucket empty → wait 0.5s for one token at 2/s
    assert waited == pytest.approx(0.5) and clk.slept == [pytest.approx(0.5)]
    clk.t += 10  # refill caps at burst
    assert rl.acquire() == 0 and rl.acquire() == 0 and rl.acquire() > 0


def test_backoff_retries_then_succeeds_with_jitter():
    calls, slept = [], []

    def fn():
        calls.append(1)
        if len(calls) < 3:
            raise httpx.ConnectError("boom")
        return "ok"

    assert with_backoff(fn, retries=5, base=1.0, cap=60, sleep=slept.append, rng=lambda: 0.5) == "ok"
    assert slept == [0.5, 1.0]  # 1*2^0*0.5, 1*2^1*0.5


def test_backoff_gives_up_and_respects_status_codes():
    def bad():
        raise httpx.ConnectError("down")

    with pytest.raises(httpx.ConnectError):
        with_backoff(bad, retries=2, sleep=lambda s: None)
    resp = httpx.Response(404, request=httpx.Request("GET", "http://x"))

    def notfound():
        raise httpx.HTTPStatusError("404", request=resp.request, response=resp)

    calls = []

    def counted():
        calls.append(1)
        notfound()

    with pytest.raises(httpx.HTTPStatusError):
        with_backoff(counted, retries=3, sleep=lambda s: None)
    assert len(calls) == 1  # 404 is not retryable


def test_raw_store_roundtrip(tmp_path):
    store = RawStore(tmp_path)
    payload = {"logs": [{"a": 1}], "n": "x"}
    p = store.save("src", payload)
    assert p.suffix == ".gz" and store.load(p) == payload
    assert [pl for _, pl in store.iter("src")] == [payload]


def test_gated_worker_records_skipped_run(session, tmp_path):
    run = run_worker(
        GatedWorker("phygitals_api", "phygitals_api_enabled", "Q2"),
        session,
        raw_store=RawStore(tmp_path),
    )
    assert run.status == RunStatus.skipped and "Q2" in run.error
    assert session.get(IngestRun, run.id).finished_at is not None


def test_worker_exception_is_contained(session, tmp_path):
    class Broken:
        key, limiter_key = "broken", "polygon_rpc"

        def fetch(self, ctx):
            raise ValueError("nope")

        def normalize(self, raw):
            return []

        def upsert(self, s, r):
            raise AssertionError

        def next_cursor(self, raw):
            return None

    run = run_worker(Broken(), session, raw_store=RawStore(tmp_path))
    assert run.status == RunStatus.error and "ValueError: nope" in run.error


def test_source_not_approved_is_a_runtime_error():
    assert issubclass(SourceNotApproved, RuntimeError)


def test_limiters_are_shared_per_key():
    assert limiter_for("solana_rpc") is limiter_for("solana_rpc")
    assert limiter_for("solana_rpc") is not limiter_for("polygon_rpc")


def test_backoff_honours_retry_after():
    resp = httpx.Response(429, request=httpx.Request("GET", "http://x"), headers={"retry-after": "7"})
    calls, slept = [], []

    def fn():
        calls.append(1)
        if len(calls) == 1:
            raise httpx.HTTPStatusError("429", request=resp.request, response=resp)
        return "ok"

    assert with_backoff(fn, retries=2, base=1.0, sleep=slept.append, rng=lambda: 0.1) == "ok"
    assert slept == [7.0]
