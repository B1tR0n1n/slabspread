"""Polygon JSON-RPC + minimal ABI decoding for Courtyard's events (Phase 0 §1)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx
from Crypto.Hash import keccak

from ingest.base import RateLimiter, with_backoff


def keccak256(data: bytes) -> str:
    return "0x" + keccak.new(digest_bits=256, data=data).hexdigest()


def event_topic(signature: str) -> str:
    return keccak256(signature.encode())


# Courtyard events, from DefiLlama's adapter (Phase 0, FETCH-grade).
TRADE_EXECUTED_SIG = "TradeExecuted(address,address,uint256,address,uint256,bytes,uint256)"
TOKEN_MINTED_SIG = "TokenPurchasedAndMinted(address,address,uint256,address,uint256)"
TRADE_EXECUTED = event_topic(TRADE_EXECUTED_SIG)
TOKEN_MINTED = event_topic(TOKEN_MINTED_SIG)

USDC_POLYGON = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
USDC_DECIMALS = 6


class EvmRpc:
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

    def block_number(self) -> int:
        return int(self.call("eth_blockNumber", []), 16)

    def get_logs(self, from_block: int, to_block: int, topics: list) -> list[dict]:
        return self.call(
            "eth_getLogs", [{"fromBlock": hex(from_block), "toBlock": hex(to_block), "topics": topics}]
        )

    def block_timestamp(self, block: int) -> int:
        b = self.call("eth_getBlockByNumber", [hex(block), False])
        return int(b["timestamp"], 16)


# --------------------------------------------------------------------------------------
# ABI decoding (only what the two events need)
# --------------------------------------------------------------------------------------


def _word(data: bytes, i: int) -> bytes:
    return data[32 * i : 32 * (i + 1)]


def _addr(word: bytes) -> str:
    return "0x" + word[-20:].hex()


def _uint(word: bytes) -> int:
    return int.from_bytes(word, "big")


def _hexbytes(h: str) -> bytes:
    return bytes.fromhex(h[2:] if h.startswith("0x") else h)


@dataclass(frozen=True)
class TradeExecuted:
    bidder: str
    asker: str
    token_id: int
    erc20: str
    amount: int
    fee_accrued: int


@dataclass(frozen=True)
class TokenMinted:
    minted_to: str
    token_address: str
    token_id: int
    payment_token: str
    payment_amount: int


def decode_trade(log: dict) -> TradeExecuted:
    t, data = log["topics"], _hexbytes(log["data"])
    return TradeExecuted(
        bidder=_addr(_hexbytes(t[1])),
        asker=_addr(_hexbytes(t[2])),
        token_id=_uint(_hexbytes(t[3])),
        erc20=_addr(_word(data, 0)),
        amount=_uint(_word(data, 1)),
        # word 2 is the offset of the dynamic `bytes tradeSignature`; we don't need it
        fee_accrued=_uint(_word(data, 3)),
    )


def decode_mint(log: dict) -> TokenMinted:
    t, data = log["topics"], _hexbytes(log["data"])
    return TokenMinted(
        minted_to=_addr(_hexbytes(t[1])),
        token_address=_addr(_word(data, 0)),
        token_id=_uint(_word(data, 1)),
        payment_token=_addr(_word(data, 2)),
        payment_amount=_uint(_word(data, 3)),
    )


def to_amount(raw: int, token: str) -> tuple[Decimal, str]:
    """Raw integer → (decimal amount, currency). Only USDC is understood; others stay raw."""
    if token.lower() == USDC_POLYGON:
        return Decimal(raw) / Decimal(10**USDC_DECIMALS), "USDC"
    return Decimal(raw), f"erc20:{token}"


# --- encoders, used only by tests/fixtures to build self-consistent logs ---------------


def _enc_addr(a: str) -> str:
    return a[2:].lower().rjust(64, "0")


def _enc_uint(n: int) -> str:
    return f"{n:064x}"


def encode_trade_log(tr: TradeExecuted, *, signature: bytes = b"\x01\x02") -> dict:
    data = (
        _enc_addr(tr.erc20)
        + _enc_uint(tr.amount)
        + _enc_uint(0x80)
        + _enc_uint(tr.fee_accrued)
        + _enc_uint(len(signature))
        + signature.hex().ljust(64, "0")
    )
    return {
        "topics": [
            TRADE_EXECUTED,
            "0x" + _enc_addr(tr.bidder),
            "0x" + _enc_addr(tr.asker),
            "0x" + _enc_uint(tr.token_id),
        ],
        "data": "0x" + data,
    }


def encode_mint_log(m: TokenMinted) -> dict:
    data = (
        _enc_addr(m.token_address)
        + _enc_uint(m.token_id)
        + _enc_addr(m.payment_token)
        + _enc_uint(m.payment_amount)
    )
    return {"topics": [TOKEN_MINTED, "0x" + _enc_addr(m.minted_to)], "data": "0x" + data}
