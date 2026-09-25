"""Solana USDC-flow workers for Collector Crypt and Phygitals (approved on-chain paths).

Both platforms settle pack purchases as USDC *into* a known wallet and buybacks as USDC
*out of* it (Phase 0 §2–3, FETCH-grade via DefiLlama's adapters). One worker class,
two configurations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from ingest.base import Context
from ingest.chains.solana import SolanaRpc, UsdcFlow, parse_usdc_flows
from ingest.persist import UpsertReport, get_or_create_source
from models import OnchainEvent

CHAIN = "solana"

# Collector Crypt gacha sinks (Tangem README + DefiLlama adapter).
CC_WALLETS = {
    "GachaNgyXTU3zFogQ8Z5jR2BLXs8215X2AtEH18VxJq3",  # gacha operator / memo authority
    "D9CEogjHA6CpS12F8St9zpSco7pQKJB5uR1RqDsuzQZk",  # USDC treasury ATA owner side
    "GachazZscHZ5bn3vnq1yEC4zpYdhAYJBzuKJwSJksc9z",  # old sink
    "96DULv1BqYfe5wyMr6pVUNC6Uyrtj6yr3tNi6VtfwW9s",  # fiat rail
}
CC_TEAM = {"cc3novbXuNSe292qKH2gGhxToaWjuBvJbA7zQf8NVxi", "jrS7Pbn38wKiPsXbyNhGCr3icfXuJxdytZr1N4TwfFu"}

# Phygitals (DefiLlama adapter + their own /api/vm/available `buyback_wallet`).
PHY_WALLETS = {
    "62Q9eeDY3eM8A5CnprBGYMPShdBjAzdpBdr71QHsS8dS",  # primary gacha + buyback
    "42oNTirN62M3MkA52KiTTGyf9RnDh2YvqNdpFSgkf97e",  # secondary
}


def classify(flow: UsdcFlow) -> str:
    memo = (flow.memo or "").lower()
    if flow.direction == "in":
        return "pack_purchase" if (memo.endswith(":open") or not memo or flow.nft_mints) else "transfer"
    return "buyback" if (memo.endswith(":buyback") or flow.nft_mints or not memo) else "transfer"


class SolanaFlowsWorker:
    limiter_key = "solana_rpc"

    def __init__(
        self,
        key: str,
        source_key: str,
        name: str,
        wallets: set[str],
        scan_address: str,
        exclude: set[str] = frozenset(),
        rpc_url: str | None = None,
    ):
        self.key, self.source_key, self.name = key, source_key, name
        self.wallets, self.scan_address, self.exclude = wallets, scan_address, exclude
        self.rpc_url = rpc_url or settings.solana_rpc_url

    def fetch(self, ctx: Context) -> dict[str, Any]:
        rpc = SolanaRpc(self.rpc_url, ctx.http, ctx.limiter)
        sigs = rpc.signatures_for(self.scan_address, until=ctx.cursor, limit=settings.solana_sig_page)
        txs = []
        for sg in sigs:
            if sg.get("err"):
                continue
            tx = rpc.transaction(sg["signature"])
            if tx:
                txs.append(tx)
        ctx.notes.update({"signatures": len(sigs), "transactions": len(txs)})
        return {"scan_address": self.scan_address, "signatures": sigs, "transactions": txs}

    def next_cursor(self, raw: dict) -> str | None:
        sigs = raw.get("signatures") or []
        return sigs[0]["signature"] if sigs else None  # newest first

    def normalize(self, raw: dict) -> list[OnchainEvent]:
        out: list[OnchainEvent] = []
        for tx in raw.get("transactions", []):
            for i, flow in enumerate(parse_usdc_flows(tx, self.wallets)):
                if flow.counterparty in self.exclude:
                    continue
                out.append(
                    OnchainEvent(
                        source_key=self.source_key,
                        chain=CHAIN,
                        tx_hash=flow.signature,
                        log_index=i,
                        block=flow.slot,
                        occurred_at=datetime.utcfromtimestamp(flow.block_time or 0),
                        kind=classify(flow),
                        token_ref=flow.nft_mints[0] if flow.nft_mints else None,
                        counterparty=flow.counterparty,
                        amount=flow.amount,
                        currency="USDC",
                        memo=flow.memo,
                        raw={"direction": flow.direction, "nft_mints": list(flow.nft_mints)},
                    )
                )
        return out

    def upsert(self, s: Session, records: list[OnchainEvent]) -> UpsertReport:
        rep = UpsertReport(fetched=len(records))
        get_or_create_source(s, self.source_key, self.name, CHAIN)
        for ev in records:
            if s.scalar(
                select(OnchainEvent).where(
                    OnchainEvent.chain == ev.chain,
                    OnchainEvent.tx_hash == ev.tx_hash,
                    OnchainEvent.log_index == ev.log_index,
                )
            ):
                rep.updated += 1
                continue
            s.add(ev)
            rep.inserted += 1
        s.flush()
        return rep


def collectorcrypt_worker() -> SolanaFlowsWorker:
    return SolanaFlowsWorker(
        "onchain_collectorcrypt",
        "collector_crypt",
        "Collector Crypt",
        CC_WALLETS,
        scan_address="GachaNgyXTU3zFogQ8Z5jR2BLXs8215X2AtEH18VxJq3",
        exclude=CC_TEAM,
    )


def phygitals_worker() -> SolanaFlowsWorker:
    return SolanaFlowsWorker(
        "onchain_phygitals",
        "phygitals",
        "Phygitals",
        PHY_WALLETS,
        scan_address="62Q9eeDY3eM8A5CnprBGYMPShdBjAzdpBdr71QHsS8dS",
    )
