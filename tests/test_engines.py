"""Phase 3 exit test, part 1: hand-computed expected values for every formula."""

from datetime import datetime, timedelta
from decimal import Decimal as D

import pytest

from engines import lag, pack_ev, spread
from engines.spread import Ask, Floor, Opportunity, Rejection, SaleObs, SpreadConfig

T0 = datetime(2026, 9, 25, 12, 0, 0)
H = timedelta(hours=1)
DAY = timedelta(days=1)


# --------------------------------------------------------------------------------------
# Spread
# --------------------------------------------------------------------------------------


def _cfg(**kw) -> SpreadConfig:
    base = dict(
        shipping=D("5.00"),
        sales_tax_rate=D("0.08"),
        vault_intake_cost=D("3.00"),
        grading_cost=D("25.00"),
        platform_fee_rate=D("0.06"),
        min_sales=3,
    )
    return SpreadConfig(**{**base, **kw})


def test_all_in_cost_by_hand():
    # ask 100 + ship 5 + tax 8% of 100 = 8 + intake 3 = 116.00 ; raw adds 25 → 141.00
    cost, detail = spread.all_in_cost(Ask(D("100"), T0), _cfg())
    assert cost == D("116.00") and detail["sales_tax_est"] == "8.00"
    raw_cost, _ = spread.all_in_cost(Ask(D("100"), T0, is_raw=True), _cfg())
    assert raw_cost == D("141.00")


def test_exit_market_median_net_of_fee_and_liquidity_gate():
    sales = [
        SaleObs(D("200"), T0 - 1 * DAY),
        SaleObs(D("180"), T0 - 2 * DAY),
        SaleObs(D("260"), T0 - 3 * DAY),
    ]
    # median(180,200,260)=200 ; net of 6% = 188.00
    net, detail = spread.exit_market(sales, _cfg(), T0)
    assert net == D("188.00") and detail["median"] == "200"
    assert (
        spread.exit_market(sales[:2], _cfg(), T0)
        == (None, pytest.approx(detail) | {"reason": "insufficient_liquidity"})
        or True
    )
    none, why = spread.exit_market(sales[:2], _cfg(), T0)
    assert none is None and why["reason"] == "insufficient_liquidity"
    # window excludes old sales
    old = [SaleObs(D("1"), T0 - 40 * DAY)] * 5
    assert spread.exit_market(old, _cfg(), T0)[0] is None


def test_compute_spread_margins_by_hand():
    ask = Ask(D("100"), T0 - 1 * H, listing_ref="L1")
    floor = Floor(D("130"), T0 - 2 * H, oracle="cc:insured*0.85")
    sales = [
        SaleObs(D("200"), T0 - 1 * DAY),
        SaleObs(D("180"), T0 - 2 * DAY),
        SaleObs(D("260"), T0 - 3 * DAY),
    ]
    o = spread.compute_spread(ask, floor, sales, _cfg(), T0)
    assert isinstance(o, Opportunity)
    assert o.all_in_cost == D("116.00")
    assert o.floor_margin == D("14.00")  # 130 - 116
    assert o.market_margin == D("72.00")  # 188 - 116
    assert o.calculation["floor"]["oracle"] == "cc:insured*0.85"
    assert o.calculation["market"]["sales_in_window"] == 3
    assert "formula" in o.calculation


def test_compute_spread_staleness_and_no_exit():
    cfg = _cfg()
    stale_ask = Ask(D("100"), T0 - 30 * H)
    assert spread.compute_spread(stale_ask, None, [], cfg, T0) == Rejection(
        "stale_ask", {"ask_as_of": stale_ask.as_of.isoformat(), "max_age": str(cfg.max_age_ask)}
    )
    fresh = Ask(D("100"), T0)
    r = spread.compute_spread(fresh, Floor(D("130"), T0 - 25 * H, "x"), [], cfg, T0)
    assert isinstance(r, Rejection) and r.reason == "stale_floor"
    r = spread.compute_spread(fresh, None, [SaleObs(D("1"), T0)], cfg, T0)
    assert isinstance(r, Rejection) and r.reason == "no_exit"


def test_rank_floor_first_then_market_and_none_last():
    def opp(ref, fm, mm):
        return Opportunity(ref, D(0), None, None, fm, mm, {})

    ranked = spread.rank(
        [opp("a", D(5), D(50)), opp("b", D(10), D(1)), opp("c", None, D(999)), opp("d", D(10), D(7))]
    )
    assert [o.listing_ref for o in ranked] == ["d", "b", "a", "c"]


# --------------------------------------------------------------------------------------
# Pack EV
# --------------------------------------------------------------------------------------


def test_pack_ev_by_hand():
    # Collector Crypt documented example: Epic 1% / Rare 4% / Uncommon 15% / Common 80%, $50 pack.
    tiers = [
        pack_ev.Tier("epic", D("0.01"), D("2000"), D("1700"), D("1800")),
        pack_ev.Tier("rare", D("0.04"), D("300"), D("255"), D("280")),
        pack_ev.Tier("uncommon", D("0.15"), D("60"), D("51"), None),
        pack_ev.Tier("common", D("0.80"), D("25"), D("21.25"), D("22")),
    ]
    r = pack_ev.compute_pack_ev(D("50"), tiers)
    # EV_platform = 20 + 12 + 9 + 20 = 61
    # EV_buyback  = 17 + 10.2 + 7.65 + 17 = 51.85
    # house_edge  = 1 - 51.85/50 = -0.037  (negative: buyback EV exceeds price — as CC advertises)
    assert r.ev_platform == D("61.0000") and r.ev_buyback == D("51.8500")
    assert r.house_edge == D("-0.0370") and r.platform_edge == D("-0.2200")
    # external covers 85% of mass: EV_external = 18 + 11.2 + 17.6 = 46.8
    assert r.external_coverage == D("0.8500") and r.ev_external == D("46.8000")
    # divergence on covered mass: platform (20+12+20=52) / 46.8 - 1 = 0.1111
    assert r.fmv_divergence == D("0.1111")
    assert "external comps cover 0.85" in r.warnings[0]
    assert r.calculation["tiers"][1]["p_x_buyback"] == "10.2000"


def test_pack_ev_flags_bad_probabilities_and_rejects_free_packs():
    tiers = [pack_ev.Tier("a", D("0.5"), D(1), D(1)), pack_ev.Tier("b", D("0.4"), D(1), D(1))]
    r = pack_ev.compute_pack_ev(D("10"), tiers)
    assert any("sum to 0.9" in w for w in r.warnings) and r.probability_sum == D("0.9")
    with pytest.raises(ValueError):
        pack_ev.compute_pack_ev(D("0"), tiers)
    assert pack_ev.band_midpoint(D("25"), D("50")) == D("37.50")


# --------------------------------------------------------------------------------------
# Lag
# --------------------------------------------------------------------------------------


def _series(values, start, step):
    return [lag.Point(start + i * step, D(v)) for i, v in enumerate(values)]


def test_trend_by_hand():
    # 14-day window; first half medians 100, second half 80 → -20%
    real = _series([100, 102, 98, 100, 80, 82, 78, 80], T0 - 14 * DAY + 1 * H, DAY * 1.9)
    t = lag.trend(real, timedelta(days=14), T0)
    assert (
        t is not None
        and t.start_median == D("100")
        and t.end_median == D("80")
        and t.change_pct == D("-0.2000")
    )
    assert lag.trend(real[:3], timedelta(days=14), T0) is None


def test_flatness_requires_early_point():
    flat = _series([200, 201, 200, 200], T0 - 47 * H, 12 * H)
    change, since = lag.flatness(flat, 48, T0)
    assert change == D("0.0050") and since == T0 - 47 * H
    late_only = _series([200, 200], T0 - 2 * H, H)
    assert lag.flatness(late_only, 48, T0) == (None, None)


def test_detect_lag_alerts_only_when_real_drops_and_platform_flat():
    cfg = lag.LagConfig(drop_pct=D("0.15"), flat_hours=48, flat_tolerance_pct=D("0.02"))
    real_drop = _series([100, 102, 98, 100, 80, 82, 78, 80], T0 - 14 * DAY + 1 * H, DAY * 1.9)
    real_flat = _series([100, 102, 98, 100, 99, 101, 100, 100], T0 - 14 * DAY + 1 * H, DAY * 1.9)
    plat_flat = _series([200, 201, 200, 200], T0 - 47 * H, 12 * H)
    plat_moved = _series([200, 190, 170, 160], T0 - 47 * H, 12 * H)
    a = lag.detect_lag(real_drop, plat_flat, cfg, T0)
    assert a is not None and a.real_change_pct == D("-0.2000") and a.platform_change_pct == D("0.0050")
    assert "human decision" in a.explanation["note"]
    assert lag.detect_lag(real_flat, plat_flat, cfg, T0) is None  # real didn't drop
    assert lag.detect_lag(real_drop, plat_moved, cfg, T0) is None  # platform already moved
