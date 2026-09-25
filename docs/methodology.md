# Methodology

Every number SlabSpread publishes is reproducible from this page plus the named inputs. The
engines that compute them are pure functions in [`engines/`](../engines/) — no I/O, no hidden
state — and each returns its full calculation alongside the result. When this page and the
code disagree, the code is wrong and this page is the spec; file it.

Conventions: money is decimal, rounded half-up to the cent at each named step. Percentages are
reported to four decimals. Times are UTC. Nothing here is financial advice.

## 1. Oracles — where a "value" comes from

A value is never shown without its oracle. The oracles we use:

| Oracle | Meaning | Source | Public? |
|---|---|---|---|
| `buyback` | What the platform will pay to take the card back right now | Platform terms × its stated value (e.g. Collector Crypt `insuredValue × 85–93%`) | derived only |
| `platform_fmv` | The platform's own estimate of market value | Platform (Courtyard `fmv_estimate_usd`; gated, see data-licenses) | derived only |
| `insured_value` | Value the platform insures/buys back against | Collector Crypt metadata | derived only |
| `onchain_median` | Median of recent on-chain sales of the same card+grade | Polygon / Solana events we index ourselves | yes |
| `licensed_mid` | Licensed price-guide value | Vendor under contract | derived only |

"Derived only" means public pages show edges, spreads, and percentages computed from the
value — never the value itself (ground rule 3).

## 2. Spread (Trade lane) — `engines/spread.py`

For an external listing matched to a vault-platform card at the same grade:

```
all_in_cost   = ask + shipping + ask × sales_tax_rate + vault_intake_cost + (grading_cost if raw)
exit_floor    = buyback value                                   # guaranteed exit
exit_market   = median(sales in window) × (1 − platform_fee_rate) # requires ≥ min_sales
floor_margin  = exit_floor  − all_in_cost
market_margin = exit_market − all_in_cost
```

Filters, applied before any arithmetic:
- **Staleness.** Ask older than `max_age_ask`, floor older than `max_age_floor`, or sales older than `max_age_sale` are discarded, not extrapolated. A listing with a stale input is rejected with the reason and the timestamp.
- **Liquidity.** `exit_market` is undefined until at least `min_sales` sales fall inside `sales_window`. A listing with neither a floor nor a liquid market is rejected (`no_exit`).

Ranking: `floor_margin` descending, then `market_margin` descending. A listing without a floor never outranks one with a floor, however large its market margin.

Defaults (all configurable; the private dashboard shows the values in force): shipping $5.00, sales tax 0%, vault intake $0, grading $25 (raw only), platform fee 6%, `min_sales` 3, window 30 days, ask/floor max age 24 h, sale max age 30 days.

Worked example (from the unit tests): ask $100, tax 8%, intake $3 → all-in $116.00. Floor $130 → floor margin **$14.00**. Sales $180/$200/$260 in window → median $200 × 0.94 = $188.00 → market margin **$72.00**.

## 3. Pack EV and house edge (Publish lane) — `engines/pack_ev.py`

For a pack tier with published odds `p_i` and a per-tier value under each oracle:

```
EV_platform = Σ p_i × platform_value_i
EV_buyback  = Σ p_i × buyback_value_i
EV_external = Σ p_i × external_value_i        # only over tiers that have an external comp
house_edge  = 1 − EV_buyback / pack_price
```

- **The house edge is computed against `buyback`**, because that is the only exit a buyer is guaranteed. `platform_edge` (against the platform's own value) is reported beside it so the gap is visible.
- **External coverage.** `EV_external` is reported with the share of probability mass it covers. A tier with no external comp is omitted from that sum, never assumed.
- **FMV divergence** = `EV_platform(covered) / EV_external − 1`, on the covered mass only. Positive means the platform values its inventory above external comps.
- When a platform publishes a value *band* per tier, the tier value is the band midpoint and is labelled as such.
- Probabilities that do not sum to 1 (±0.001) produce a warning on the result, not a silent renormalisation.

Worked example: Collector Crypt's documented 1/4/15/80% tiers at $50 with buyback values 1700/255/51/21.25 → `EV_buyback` = 17 + 10.20 + 7.65 + 17 = **$51.85**, house edge **−3.70%** (the buyback EV exceeds the price, as the platform advertises; whether the *insured values* behind it match external comps is exactly what the divergence figure measures).

## 4. Lag detector — `engines/lag.py`

```
real_trend     = median(real prices, second half of window) / median(first half) − 1
platform_range = (max − min) / min of platform value over the last flat_hours
alert iff real_trend ≤ −drop_pct  and  platform_range ≤ flat_tolerance_pct
```

Requires at least `min_real_points` real observations with at least two in each half, and a platform observation from the first quarter of the flat window (a single fresh point cannot be "flat"). Defaults: 14-day window, 15% drop, 48 h flat, 2% tolerance. The alert is informational; it carries both series' summaries and the thresholds.

## 5. Backtest — `engines/backtest.py`

For each historical ask, the spread is computed using only observations at or before that moment. A deal is *flagged* if its `floor_margin` ≥ threshold. It is *resolved* if a floor observation exists at or after `ask_time + settle`; it *met* its margin if `realized_floor − all_in_cost ≥ predicted floor_margin`. The report gives asks, flagged, resolved, met, positive-realised, rejections by reason, and per-deal rows. `hit_rate = met / resolved`.

## 6. Identity — `engines/identity.py`

Two records are the same card when, in order: (1) grader and cert number match; (2) the canonical key `game|set|number|variant|grader|grade` matches after normalisation; (3) otherwise a title-similarity score minus hard-field penalties yields a *candidate* that a human accepts or rejects. Nothing fuzzy is ever trusted automatically.

## 7. Limitations

- On-chain sales cover only the venues we index; off-chain sales on the same platforms are invisible to `onchain_median`.
- Buyback values are the platform's promise, not a market; a platform can change its terms.
- Published odds are per tier; per-card odds are derived (tier weight ÷ cards in tier) only where the platform exposes tier inventory.
- Data-source status and open license questions: [`data-licenses.md`](data-licenses.md), [`phase0-findings.md`](phase0-findings.md) §10.
