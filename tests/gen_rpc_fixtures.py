"""Build fixtures/rpc/: JSON-RPC responses shaped per the public specs, with values we control.

SYNTHETIC — the build environment cannot reach any RPC. Log data is produced by the same
ABI encoders the decoders are tested against; Solana transactions follow the documented
`jsonParsed` layout. Replace with recorded responses as soon as RPC access exists.

    python tests/gen_rpc_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

from ingest.chains.evm import TokenMinted, TradeExecuted, encode_mint_log, encode_trade_log

OUT = Path(__file__).resolve().parent.parent / "fixtures" / "rpc"
USDC_POLY = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
USDC_SOL = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
ORDERBOOK = "0x5E4943373c2198625BD441Ae0629E9E7b4FB4797"
BLASTOISE_TOKEN = 28726077222572370237223419992242905820335237414880435749025633080341558574479


def polygon() -> dict:
    trade = TradeExecuted(
        bidder="0x52CAa1022895c73B4FEE8B860862d928AA256C91",
        asker="0x1111111111111111111111111111111111111111",
        token_id=BLASTOISE_TOKEN,
        erc20=USDC_POLY,
        amount=150_000_000,  # 150 USDC — the real 2026-06-09 sale amount from Phase 0
        fee_accrued=0,
    )
    mint = TokenMinted(
        minted_to="0x2222222222222222222222222222222222222222",
        token_address="0x251BE3A17Af4892035C37ebf5890F4a4D889dcAD",
        token_id=BLASTOISE_TOKEN + 1,
        payment_token=USDC_POLY,
        payment_amount=25_000_000,
    )
    logs = []
    for i, (lg, blk, tx) in enumerate(
        [
            (
                encode_trade_log(trade),
                88_175_795,
                "0x71f546e311d3196c0babe3dd76754c23710f298938b8953d6017cfd704e71c3a",
            ),
            (encode_mint_log(mint), 88_175_800, "0x" + "ab" * 32),
        ]
    ):
        logs.append(
            {
                **lg,
                "address": ORDERBOOK.lower(),
                "blockNumber": hex(blk),
                "transactionHash": tx,
                "logIndex": hex(i),
                "removed": False,
            }
        )
    return {
        "from_block": 88_175_000,
        "to_block": 88_176_999,
        "logs": logs,
        "timestamps": {"88175795": 1780964400, "88175800": 1780964410},
    }


def _sol_tx(
    sig: str,
    slot: int,
    block_time: int,
    memo: str,
    amount: int,
    src_owner: str,
    dst_owner: str,
    nft_mint: str | None,
) -> dict:
    keys = [
        src_owner,
        dst_owner,
        "SrcUsdcAta1111111111111111111111111111111111",
        "DstUsdcAta1111111111111111111111111111111111",
    ]
    instructions = [
        {"programId": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr", "program": "spl-memo", "parsed": memo},
        {
            "program": "spl-token",
            "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            "parsed": {
                "type": "transferChecked",
                "info": {
                    "authority": src_owner,
                    "source": keys[2],
                    "destination": keys[3],
                    "mint": USDC_SOL,
                    "tokenAmount": {"amount": str(amount), "decimals": 6, "uiAmount": amount / 1e6},
                },
            },
        },
    ]
    if nft_mint:
        instructions.append(
            {
                "program": "spl-token",
                "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                "parsed": {
                    "type": "transferChecked",
                    "info": {
                        "authority": dst_owner,
                        "source": "NftAta1",
                        "destination": "NftAta2",
                        "mint": nft_mint,
                        "tokenAmount": {"amount": "1", "decimals": 0},
                    },
                },
            }
        )
    return {
        "slot": slot,
        "blockTime": block_time,
        "meta": {
            "err": None,
            "preTokenBalances": [
                {"accountIndex": 2, "mint": USDC_SOL, "owner": src_owner},
                {"accountIndex": 3, "mint": USDC_SOL, "owner": dst_owner},
            ],
            "postTokenBalances": [
                {"accountIndex": 2, "mint": USDC_SOL, "owner": src_owner},
                {"accountIndex": 3, "mint": USDC_SOL, "owner": dst_owner},
            ],
            "innerInstructions": [],
        },
        "transaction": {
            "signatures": [sig],
            "message": {"accountKeys": [{"pubkey": k} for k in keys], "instructions": instructions},
        },
    }


def collectorcrypt() -> dict:
    sink = "GachaNgyXTU3zFogQ8Z5jR2BLXs8215X2AtEH18VxJq3"
    player = "EofCkTaFXUjdwpQdbTnjMsZD1nqjGTenUGFsfEdkraYN"
    team = "cc3novbXuNSe292qKH2gGhxToaWjuBvJbA7zQf8NVxi"
    txs = [
        _sol_tx("sigOpen1", 300_000_001, 1780964500, "elite-pack-0001:open", 50_000_000, player, sink, None),
        _sol_tx(
            "sigBuyback1",
            300_000_050,
            1780965000,
            "elite-pack-0001:buyback",
            27_200_000,
            sink,
            player,
            "2w1XbDvP9k2pGP313VKmu8QpS3Ja1nSXLyUuQZG1MK7D",
        ),
        _sol_tx(
            "sigTeam1", 300_000_060, 1780965100, "", 999_000_000, sink, team, None
        ),  # excluded (team wallet)
    ]
    sigs = [
        {
            "signature": t["transaction"]["signatures"][0],
            "slot": t["slot"],
            "err": None,
            "blockTime": t["blockTime"],
        }
        for t in reversed(txs)
    ]
    return {"scan_address": sink, "signatures": sigs, "transactions": txs}


def phygitals() -> dict:
    wallet = "62Q9eeDY3eM8A5CnprBGYMPShdBjAzdpBdr71QHsS8dS"
    player = "DNMKGBRxpsGoNjt8iycrB5G2UXWsnqhJdd4MQeV2KPoi"
    txs = [
        _sol_tx("phySigOpen1", 300_100_001, 1780970000, "", 10_000_000, player, wallet, None),
        _sol_tx(
            "phySigBuyback1",
            300_100_020,
            1780970500,
            "",
            8_500_000,
            wallet,
            player,
            "6sRw5SiUSNu79Nvv2XFjVSJuHJE26X8HTDerV6TWJvQ",
        ),
    ]
    sigs = [
        {
            "signature": t["transaction"]["signatures"][0],
            "slot": t["slot"],
            "err": None,
            "blockTime": t["blockTime"],
        }
        for t in reversed(txs)
    ]
    return {"scan_address": wallet, "signatures": sigs, "transactions": txs}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, doc in [
        ("polygon_courtyard_logs.json", polygon()),
        ("solana_collectorcrypt_flows.json", collectorcrypt()),
        ("solana_phygitals_flows.json", phygitals()),
    ]:
        (OUT / name).write_text(json.dumps(doc, indent=1))
    print("wrote", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
