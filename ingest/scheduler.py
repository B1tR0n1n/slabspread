"""APScheduler entrypoint for the workers container: `python -m ingest.scheduler`.

Each worker runs in its own DB session on its own interval; a failure is recorded as an
`IngestRun` with status=error and does not affect the others.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.alerts import scan_and_deliver
from app.db import session_scope
from config import settings
from ingest import gated, onchain_courtyard, onchain_solana_flows
from ingest.base import RawStore, run_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

WORKERS = {
    "onchain_courtyard": onchain_courtyard.worker,
    "onchain_collectorcrypt": onchain_solana_flows.collectorcrypt_worker,
    "onchain_phygitals": onchain_solana_flows.phygitals_worker,
    "platform_odds": gated.platform_odds_worker,
}


def run_once(key: str) -> None:
    w = WORKERS[key]()
    with session_scope() as s:
        run_worker(w, s, raw_store=RawStore())


def run_alerts() -> None:
    with session_scope() as s:
        scan_and_deliver(s)


def main() -> None:
    sched = BlockingScheduler()
    sched.add_job(
        run_alerts, "interval", seconds=settings.schedules.get("alerts", 300), id="alerts", max_instances=1
    )
    for key in WORKERS:
        every = settings.schedules.get(key, 600)
        sched.add_job(run_once, "interval", seconds=every, args=[key], id=key, max_instances=1, coalesce=True)
        logging.getLogger("ingest").info("scheduled %s every %ss", key, every)
    sched.start()


if __name__ == "__main__":
    main()
