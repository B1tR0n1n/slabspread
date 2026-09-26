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


CORE_PROGRAM = "CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d"  # Metaplex Core (prefix match is enough)


def _balance_maps(tx: dict) -> tuple[dict[str, str], dict[str, str]]:
    """(token account → owner, token account → mint) from pre/post token balances."""
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in tx["transaction"]["message"]["accountKeys"]]
    owners: dict[str, str] = {}
    mints: dict[str, str] = {}
    meta = tx.get("meta") or {}
    for bal in (meta.get("preTokenBalances") or []) + (meta.get("postTokenBalances") or []):
        idx = bal.get("accountIndex")
        if idx is None or idx >= len(keys):
            continue
        if bal.get("owner"):
            owners[keys[idx]] = bal["owner"]
        if bal.get("mint"):
            mints[keys[idx]] = bal["mint"]
    return owners, mints


def parse_usdc_flows(tx: dict, platform_wallets: set[str]) -> list[UsdcFlow]:
    """All USDC transfers in a tx that touch a platform wallet, with memo and NFT refs.

    Handles both `transferChecked` (mint inline) and plain `transfer` (mint resolved from the
    token-balance metadata). NFT refs come from spl-token moves of non-USDC mints and from
    Metaplex Core instructions, whose first account is the asset.
    """
    if tx is None or (tx.get("meta") or {}).get("err"):
        return []
    owners, mints = _balance_maps(tx)
    memo = None
    nft_refs: list[str] = []
    transfers: list[tuple[str | None, str | None, int]] = []
    for ins in _instructions(tx):
        prog = ins.get("program") or ins.get("programId") or ""
        pid = ins.get("programId") or ""
        parsed = ins.get("parsed")
        if pid in MEMO_PROGRAMS or prog == "spl-memo":
            memo = parsed if isinstance(parsed, str) else (parsed or {}).get("memo") or memo
            continue
        if pid.startswith("CoREENxT"):
            accts = ins.get("accounts") or []
            if accts:
                nft_refs.append(accts[0] if isinstance(accts[0], str) else str(accts[0]))
            continue
        if prog != "spl-token" or not isinstance(parsed, dict):
            continue
        info = parsed.get("info", {})
        if parsed.get("type") not in ("transfer", "transferChecked"):
            continue
        src, dst = info.get("source"), info.get("destination")
        mint = info.get("mint") or mints.get(src) or mints.get(dst)
        raw = int((info.get("tokenAmount") or {}).get("amount") or info.get("amount") or 0)
        if mint == USDC_SOLANA:
            transfers.append((owners.get(src, info.get("authority")), owners.get(dst, dst), raw))
        elif mint:
            nft_refs.append(mint)
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
                nft_mints=tuple(dict.fromkeys(nft_refs)),
            )
        )
    return flows
