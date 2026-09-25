"""Pack EV auditor (plan §5b) — Publish lane.

    EV_platform = Σ p_i × platform_value_i
    EV_buyback  = Σ p_i × buyback_value_i
    EV_external = Σ p_i × external_value_i        # where external comps exist
    house_edge  = 1 − EV_buyback / pack_price

Every EV names its oracle. `EV_external` is reported with the probability mass it actually
covers, because a tier with no external comp contributes nothing and hiding that would
overstate the platform's generosity.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

FOUR = Decimal("0.0001")
CENT = Decimal("0.01")


@dataclass(frozen=True)
class Tier:
    name: str
    probability: Decimal
    platform_value: Decimal  # platform's stated value for the tier (mean of eligible cards)
    buyback_value: Decimal  # what the platform will pay to take it back
    external_value: Decimal | None = None  # licensed / on-chain comp, if any


@dataclass(frozen=True)
class PackEV:
    pack_price: Decimal
    ev_platform: Decimal
    ev_buyback: Decimal
    ev_external: Decimal | None
    external_coverage: Decimal  # share of probability mass with an external comp
    house_edge: Decimal  # 1 - ev_buyback / price
    platform_edge: Decimal  # 1 - ev_platform / price  (what the platform's own numbers imply)
    fmv_divergence: Decimal | None  # ev_platform / ev_external - 1, on covered mass
    probability_sum: Decimal
    warnings: tuple[str, ...]
    calculation: dict


def band_midpoint(low: Decimal, high: Decimal) -> Decimal:
    """When a platform publishes a value *band* per tier rather than a value, the midpoint is
    the most defensible single number — and it is named as such in the output."""
    return ((low + high) / 2).quantize(CENT, rounding=ROUND_HALF_UP)


def compute_pack_ev(
    pack_price: Decimal, tiers: list[Tier], *, tolerance: Decimal = Decimal("0.001")
) -> PackEV:
    if pack_price <= 0:
        raise ValueError("pack_price must be positive")
    warnings: list[str] = []
    p_sum = sum((t.probability for t in tiers), Decimal(0))
    if abs(p_sum - 1) > tolerance:
        warnings.append(f"probabilities sum to {p_sum}, not 1")

    ev_platform = sum((t.probability * t.platform_value for t in tiers), Decimal(0))
    ev_buyback = sum((t.probability * t.buyback_value for t in tiers), Decimal(0))
    covered = [t for t in tiers if t.external_value is not None]
    coverage = sum((t.probability for t in covered), Decimal(0))
    ev_external = sum((t.probability * t.external_value for t in covered), Decimal(0)) if covered else None
    if covered and coverage < p_sum:
        warnings.append(f"external comps cover {coverage} of probability mass")

    divergence = None
    if ev_external is not None and ev_external > 0:
        ev_platform_covered = sum((t.probability * t.platform_value for t in covered), Decimal(0))
        divergence = (ev_platform_covered / ev_external - 1).quantize(FOUR, rounding=ROUND_HALF_UP)

    q = lambda x: x.quantize(FOUR, rounding=ROUND_HALF_UP)  # noqa: E731
    return PackEV(
        pack_price=pack_price,
        ev_platform=q(ev_platform),
        ev_buyback=q(ev_buyback),
        ev_external=q(ev_external) if ev_external is not None else None,
        external_coverage=q(coverage),
        house_edge=q(1 - ev_buyback / pack_price),
        platform_edge=q(1 - ev_platform / pack_price),
        fmv_divergence=divergence,
        probability_sum=p_sum,
        warnings=tuple(warnings),
        calculation={
            "pack_price": str(pack_price),
            "tiers": [
                {
                    "name": t.name,
                    "p": str(t.probability),
                    "platform_value": str(t.platform_value),
                    "buyback_value": str(t.buyback_value),
                    "external_value": str(t.external_value) if t.external_value is not None else None,
                    "p_x_buyback": str(q(t.probability * t.buyback_value)),
                }
                for t in tiers
            ],
            "formula": "house_edge = 1 - Σ p_i·buyback_i / pack_price",
        },
    )
