"""Solana JSON-RPC + parsing of jsonParsed transactions into USDC flows with memos.

Both Collector Crypt and Phygitals settle packs and buybacks as plain USDC transfers to
or from a known wallet (Phase 0 §2–3). So the "decoder" is: which direction did USDC move
relative to the platform wallet, and what did the memo say.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from ingest.base import RateLimiter, with_backoff

USDC_SOLANA = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
MEMO_PROGRAMS = {"MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr", "Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo"}


class SolanaRpc:
    def __init__(self, url: str, http: httpx.Client, limiter: RateLimiter):
        self.url, self.http, self.limiter = url, http, limiter
        self._id = 0

    def call(self, method: str, params: list) -> Any:
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}

        def do():
            self.limiter.acquire()
            r = self.http.post(self.url, json=payload)
            r.raise_for_status()
            body = r.json()
            if "error" in body:
                raise RuntimeError(f"rpc {method}: {body['error']}")
            return body["result"]

        return with_backoff(do)

    def signatures_for(self, address: str, *, until: str | None, limit: int) -> list[dict]:
        opts: dict[str, Any] = {"limit": limit}
        if until:
            opts["until"] = until
        return self.call("getSignaturesForAddress", [address, opts])

    def transaction(self, sig: str) -> dict | None:
        return self.call(
            "getTransaction", [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
        )


@dataclass(frozen=True)
class UsdcFlow:
    signature: str
    slot: int
    block_time: int | None
    direction: str  # "in" (to platform wallet) | "out" (from platform wallet)
    amount: Decimal
    counterparty: str | None
    memo: str | None
    nft_mints: tuple[str, ...]  # non-USDC token mints that moved in the same tx


def _instructions(tx: dict) -> list[dict]:
    msg = tx["transaction"]["message"]
    out = list(msg.get("instructions", []))
    for inner in (tx.get("meta") or {}).get("innerInstructions", []) or []:
        out.extend(inner.get("instructions", []))
    return out


def _owner_map(tx: dict) -> dict[str, str]:
    """token account → owner, from pre/post token balances (jsonParsed includes owner)."""
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in tx["transaction"]["message"]["accountKeys"]]
    m: dict[str, str] = {}
    meta = tx.get("meta") or {}
    for bal in (meta.get("preTokenBalances") or []) + (meta.get("postTokenBalances") or []):
        idx, owner = bal.get("accountIndex"), bal.get("owner")
        if idx is not None and owner and idx < len(keys):
            m[keys[idx]] = owner
    return m


def parse_usdc_flows(tx: dict, platform_wallets: set[str]) -> list[UsdcFlow]:
    """All USDC transfers in a tx that touch a platform wallet, with memo and NFT mints."""
    if tx is None or (tx.get("meta") or {}).get("err"):
        return []
    owners = _owner_map(tx)
    memo = None
    nft_mints: list[str] = []
    transfers: list[tuple[str, str, int]] = []  # (src_owner, dst_owner, raw_amount)
    for ins in _instructions(tx):
        prog = ins.get("program") or ins.get("programId")
        parsed = ins.get("parsed")
        if ins.get("programId") in MEMO_PROGRAMS or prog == "spl-memo":
            memo = parsed if isinstance(parsed, str) else (parsed or {}).get("memo") or memo
            continue
        if prog != "spl-token" or not isinstance(parsed, dict):
            continue
        info = parsed.get("info", {})
        ptype = parsed.get("type")
        if ptype not in ("transfer", "transferChecked"):
            continue
        mint = info.get("mint")
        src, dst = info.get("source"), info.get("destination")
        src_owner, dst_owner = owners.get(src, info.get("authority")), owners.get(dst, dst)
        if mint == USDC_SOLANA or (mint is None and ptype == "transfer" and _looks_usdc(info)):
            raw = int((info.get("tokenAmount") or {}).get("amount") or info.get("amount") or 0)
            transfers.append((src_owner, dst_owner, raw))
        elif mint:
            nft_mints.append(mint)
    flows: list[UsdcFlow] = []
    for src_owner, dst_owner, raw in transfers:
        if dst_owner in platform_wallets:
            direction, cp = "in", src_owner
        elif src_owner in platform_wallets:
            direction, cp = "out", dst_owner
        else:
            continue
        flows.append(
            UsdcFlow(
                signature=tx["transaction"]["signatures"][0],
                slot=tx["slot"],
                block_time=tx.get("blockTime"),
                direction=direction,
                amount=Decimal(raw) / Decimal(10**6),
                counterparty=cp,
                memo=memo,
                nft_mints=tuple(nft_mints),
            )
        )
    return flows


def _looks_usdc(info: dict) -> bool:
    # A bare `transfer` carries no mint; we only accept it when the token amount carries 6 decimals.
    ta = info.get("tokenAmount") or {}
    return ta.get("decimals") == 6
