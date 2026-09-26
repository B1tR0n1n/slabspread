"""Courtyard on-chain worker (approved path): Polygon `TradeExecuted` + `TokenPurchasedAndMinted`.

Produces `OnchainEvent` rows (kind trade|mint) and derives `Sale` rows from trades.
Token metadata enrichment via tokenURI is a separate, gated step (Q3 in phase0-findings).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from ingest.base import Context, limiter_for
from ingest.chains.evm import (
    TOKEN_MINTED,
    TRADE_EXECUTED,
    EvmRpc,
    decode_mint,
    decode_trade,
    to_amount,
)
from ingest.persist import UpsertReport, get_or_create_source
from models import OnchainEvent, Sale

KEY = "onchain_courtyard"
SOURCE_KEY = "courtyard"
CHAIN = "polygon"
REGISTRY = "0x251BE3A17Af4892035C37ebf5890F4a4D889dcAD"


ROLE_LISTS = (
    "listTrustedOperatorRoleMembers()",
    "listTrustedForwarderRoleMembers()",
    "listMinterRoleMembers()",
)


def registry_role_members(rpc: EvmRpc) -> list[str]:
    """Addresses that emit Courtyard's events: operators ∪ forwarders ∪ minters, read from the
    registry's view functions (as DefiLlama does). Public nodes require an address filter on
    eth_getLogs, and these are the only legitimate emitters."""
    out: list[str] = []
    for fn in ROLE_LISTS:
        out.extend(rpc.call_address_list(REGISTRY, fn))
    return sorted(set(out))


class CourtyardOnchainWorker:
    key = KEY
    limiter_key = "polygon_rpc"

    def __init__(self, rpc_url: str | None = None):
        self.rpc_url = rpc_url or settings.polygon_rpc_url

    # fetch ------------------------------------------------------------------------------
    def fetch(self, ctx: Context) -> dict[str, Any]:
        rpc = EvmRpc(self.rpc_url, ctx.http, ctx.limiter)
        head = rpc.block_number()
        start = int(ctx.cursor) + 1 if ctx.cursor else max(0, head - settings.polygon_backfill_blocks)
        end = min(head, start + settings.polygon_log_chunk_blocks - 1)
        emitters = registry_role_members(rpc)
        logs: list[dict] = []
        if start <= end:
            # Public nodes reject long address lists ("Request blocked" above ~4); chunk and merge.
            seen: set[tuple[str, str]] = set()
            for i in range(0, len(emitters), settings.polygon_address_chunk):
                for lg in rpc.get_logs(
                    start, end, [[TRADE_EXECUTED, TOKEN_MINTED]],
                    addresses=emitters[i : i + settings.polygon_address_chunk],
                ):  # fmt: skip
                    key = (lg["transactionHash"], lg["logIndex"])
                    if key not in seen:
                        seen.add(key)
                        logs.append(lg)
        blocks = sorted({int(lg["blockNumber"], 16) for lg in logs})
        timestamps = rpc.block_timestamps(blocks)
        ctx.notes.update({"from_block": start, "to_block": end, "head": head, "emitters": len(emitters)})
        return {
            "from_block": start,
            "to_block": end,
            "logs": logs,
            "timestamps": {str(k): v for k, v in timestamps.items()},
        }

    def next_cursor(self, raw: dict) -> str | None:
        return str(raw["to_block"]) if raw.get("to_block") is not None else None

    # normalize --------------------------------------------------------------------------
    def normalize(self, raw: dict) -> list[OnchainEvent]:
        out: list[OnchainEvent] = []
        ts = {int(k): v for k, v in raw.get("timestamps", {}).items()}
        for lg in raw.get("logs", []):
            topic0 = lg["topics"][0].lower()
            block = int(lg["blockNumber"], 16)
            when = datetime.utcfromtimestamp(ts.get(block, 0))
            base = dict(
                source_key=SOURCE_KEY,
                chain=CHAIN,
                tx_hash=lg["transactionHash"],
                log_index=int(lg["logIndex"], 16),
                block=block,
                occurred_at=when,
                raw=lg,
            )
            if topic0 == TRADE_EXECUTED:
                t = decode_trade(lg)
                amount, cur = to_amount(t.amount, t.erc20)
                out.append(
                    OnchainEvent(
                        kind="trade",
                        token_ref=str(t.token_id),
                        counterparty=t.bidder,
                        amount=amount,
                        currency=cur,
                        **base,
                    )
                )
            elif topic0 == TOKEN_MINTED:
                m = decode_mint(lg)
                amount, cur = to_amount(m.payment_amount, m.payment_token)
                out.append(
                    OnchainEvent(
                        kind="mint",
                        token_ref=str(m.token_id),
                        counterparty=m.minted_to,
                        amount=amount,
                        currency=cur,
                        **base,
                    )
                )
        return out

    # upsert -----------------------------------------------------------------------------
    def upsert(self, s: Session, records: list[OnchainEvent]) -> UpsertReport:
        rep = UpsertReport(fetched=len(records))
        src = get_or_create_source(s, SOURCE_KEY, "Courtyard", CHAIN)
        for ev in records:
            exists = s.scalar(
                select(OnchainEvent).where(
                    OnchainEvent.chain == ev.chain,
                    OnchainEvent.tx_hash == ev.tx_hash,
                    OnchainEvent.log_index == ev.log_index,
                )
            )
            if exists:
                rep.updated += 1
                continue
            s.add(ev)
            rep.inserted += 1
            if ev.kind == "trade":
                ext = f"{ev.tx_hash}:{ev.log_index}"
                if not s.scalar(select(Sale).where(Sale.source_id == src.id, Sale.external_id == ext)):
                    s.add(
                        Sale(
                            source_id=src.id,
                            external_id=ext,
                            price=ev.amount,
                            currency=ev.currency or "USDC",
                            sold_at=ev.occurred_at,
                            raw={"token_id": ev.token_ref, "bidder": ev.counterparty, "chain": CHAIN},
                        )
                    )
        s.flush()
        return rep


def worker() -> CourtyardOnchainWorker:
    return CourtyardOnchainWorker()


__all__ = ["CourtyardOnchainWorker", "worker", "limiter_for"]
