"""ABI decoding and Solana jsonParsed parsing."""

from decimal import Decimal

from conftest import load

from ingest.chains import evm, solana


def test_event_topics_match_hand_computed_keccak():
    # keccak256 of the canonical signatures; the first is also what DefiLlama's adapter filters on.
    assert evm.TRADE_EXECUTED == "0xa6ae807740439025f50884311ce0f96f5c3809a8f7170f9459dab1b14c9d8afd"
    assert (
        evm.event_topic("TokenPurchasedAndMinted(address,address,uint256,address,uint256)")
        == evm.TOKEN_MINTED
    )
    assert evm.keccak256(b"") == "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"


def test_trade_log_roundtrip_and_usdc_scaling():
    tr = evm.TradeExecuted(
        "0x" + "ab" * 20, "0x" + "cd" * 20, 2**200 + 7, evm.USDC_POLYGON, 366_000_000, 21_960_000
    )
    lg = evm.encode_trade_log(tr, signature=b"\xde\xad\xbe\xef")
    assert evm.decode_trade(lg) == tr
    assert evm.to_amount(tr.amount, tr.erc20) == (Decimal("366"), "USDC")
    assert evm.to_amount(5, "0x" + "00" * 20)[1].startswith("erc20:")


def test_mint_log_roundtrip():
    m = evm.TokenMinted("0x" + "11" * 20, "0x" + "22" * 20, 12345, evm.USDC_POLYGON, 25_000_000)
    assert evm.decode_mint(evm.encode_mint_log(m)) == m


def test_fixture_logs_decode():
    raw = load("rpc/polygon_courtyard_logs.json")
    trade = evm.decode_trade(raw["logs"][0])
    assert trade.amount == 150_000_000 and trade.erc20.lower() == evm.USDC_POLYGON
    assert trade.bidder == "0x52caa1022895c73b4fee8b860862d928aa256c91"


def test_solana_flows_direction_memo_and_nft():
    raw = load("rpc/solana_collectorcrypt_flows.json")
    sink = {"GachaNgyXTU3zFogQ8Z5jR2BLXs8215X2AtEH18VxJq3"}
    opened = solana.parse_usdc_flows(raw["transactions"][0], sink)
    bought_back = solana.parse_usdc_flows(raw["transactions"][1], sink)
    assert len(opened) == 1 and opened[0].direction == "in" and opened[0].amount == Decimal("50")
    assert opened[0].memo == "elite-pack-0001:open" and opened[0].nft_mints == ()
    assert bought_back[0].direction == "out" and bought_back[0].amount == Decimal("27.2")
    assert bought_back[0].nft_mints == ("2w1XbDvP9k2pGP313VKmu8QpS3Ja1nSXLyUuQZG1MK7D",)
    assert bought_back[0].counterparty == "EofCkTaFXUjdwpQdbTnjMsZD1nqjGTenUGFsfEdkraYN"


def test_solana_ignores_failed_and_unrelated_tx():
    raw = load("rpc/solana_collectorcrypt_flows.json")
    tx = raw["transactions"][0]
    assert solana.parse_usdc_flows(tx, {"SomeoneElse"}) == []
    failed = {**tx, "meta": {**tx["meta"], "err": {"InstructionError": [0, "Custom"]}}}
    assert solana.parse_usdc_flows(failed, {"GachaNgyXTU3zFogQ8Z5jR2BLXs8215X2AtEH18VxJq3"}) == []


def test_solana_plain_transfer_resolves_mint_from_balances_and_core_asset():
    raw = load("rpc/solana_phygitals_flows.json")
    wallet = {"62Q9eeDY3eM8A5CnprBGYMPShdBjAzdpBdr71QHsS8dS"}
    opened = solana.parse_usdc_flows(raw["transactions"][0], wallet)
    back = solana.parse_usdc_flows(raw["transactions"][1], wallet)
    assert opened[0].direction == "in" and opened[0].amount == Decimal("10") and opened[0].memo is None
    assert back[0].direction == "out" and back[0].amount == Decimal("8.5")
    assert back[0].nft_mints == ("6sRw5SiUSNu79Nvv2XFjVSJuHJE26X8HTDerV6TWJvQ",)  # from the Core instruction
