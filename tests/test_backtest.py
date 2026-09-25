"""Phase 3 exit test, part 2: backtest the spread engine on stored history and report how
many flagged deals would have met their floor margin."""

from datetime import datetime, timedelta
from decimal import Decimal as D

from engines.backtest import FloorObs, backtest_spread
from engines.spread import Ask, SaleObs, SpreadConfig

T0 = datetime(2026, 9, 1)
DAY = timedelta(days=1)
CFG = SpreadConfig(
    shipping=D("5"), sales_tax_rate=D("0"), vault_intake_cost=D("0"), min_sales=99
)  # floor-only


def test_backtest_counts_met_missed_unresolved_and_rejections():
    # Daily floor (buyback) observations, as the workers would record them:
    # 130 through day 4, 100 from day 5, 140 from day 12 to day 14, nothing after.
    floors = (
        [FloorObs(D("130"), T0 + d * DAY, "cc") for d in range(0, 5)]
        + [FloorObs(D("100"), T0 + d * DAY, "cc") for d in range(5, 12)]
        + [FloorObs(D("140"), T0 + d * DAY, "cc") for d in range(12, 15)]
    )
    asks = [
        Ask(
            D("100"), T0 + 1 * DAY, listing_ref="met"
        ),  # cost 105, floor 130 → predicted 25; settle at day 4 → floor 130 → realized 25 ✓
        Ask(
            D("100"), T0 + 3 * DAY, listing_ref="missed"
        ),  # predicted 25; settle day 6 → floor 100 → realized -5 ✗
        Ask(
            D("100"), T0 + 6 * DAY, listing_ref="unresolved"
        ),  # floor 100, cost 105 → margin -5 → not flagged
        Ask(D("100"), T0 + 10 * DAY, listing_ref="late"),  # floor 100 → -5 not flagged
        Ask(
            D("100"), T0 + 13 * DAY, listing_ref="open"
        ),  # floor 140 → 35 flagged, but nothing after settle → unresolved
        Ask(
            D("100"), T0 + 50 * DAY, listing_ref="stale"
        ),  # last floor (day 14) is 36 days old → stale_floor rejection
    ]
    rep = backtest_spread(asks, floors, [], CFG, settle=3 * DAY)
    assert rep.asks == 6
    assert rep.rejected == {"stale_floor": 1}
    assert rep.flagged == 3  # met, missed, open
    assert rep.resolved == 2 and rep.met_floor == 1 and rep.positive_realized == 1
    assert rep.hit_rate == D("0.5")
    outcomes = {d["listing_ref"]: d["outcome"] for d in rep.details}
    assert outcomes == {"met": "met", "missed": "missed", "open": "unresolved"}
    missed = next(d for d in rep.details if d["listing_ref"] == "missed")
    assert missed["realized_margin"] == "-5.00" and missed["predicted_floor_margin"] == "25.00"


def test_backtest_only_uses_information_available_at_decision_time():
    # A sale after the ask must not influence the market exit computed at ask time.
    cfg = SpreadConfig(shipping=D("0"), sales_tax_rate=D("0"), min_sales=1, platform_fee_rate=D("0"))
    floors = [FloorObs(D("50"), T0, "x"), FloorObs(D("50"), T0 + 5 * DAY, "x")]
    sales = [SaleObs(D("999"), T0 + 2 * DAY)]  # future relative to the ask
    rep = backtest_spread([Ask(D("40"), T0 + 1 * DAY, listing_ref="a")], floors, sales, cfg)
    assert rep.flagged == 1 and rep.resolved == 1 and rep.met_floor == 1
    assert rep.details[0]["predicted_floor_margin"] == "10.00"
