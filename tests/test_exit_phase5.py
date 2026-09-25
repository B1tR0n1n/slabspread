"""Phase 5 exit test (plan §7):

  a stranger can read the House Edge Index and reproduce one tier's number from the
  methodology page.

We play the stranger: parse the inputs table the page publishes for one pack, apply the
formula stated in methodology.md, and check it equals the house edge the page shows.
Plus: disclosures, 18+ notice, footer, sitemap/OG, derived-only valuation gap.
"""

import re
from datetime import datetime, timedelta
from decimal import Decimal as D

import pytest

from config import settings
from models import Card, Pack, PackOdds, Sale, Source, Valuation, ValueType
from sitegen import aggregate, build

NOW = datetime(2026, 9, 25, 12, 0)


@pytest.fixture
def seeded(session):
    cc = Source(key="collector_crypt", name="Collector Crypt", chain="solana")
    session.add(cc)
    session.flush()
    pack = Pack(
        source_id=cc.id,
        slug="elite",
        name="Elite Pack",
        price=D("50"),
        currency="USDC",
        buyback_pct=D("0.85"),
    )
    session.add(pack)
    session.flush()
    # two snapshots: yesterday and today; today's odds are CC's documented example
    for day, common_hi in [(1, D("40")), (0, D("30"))]:
        as_of = NOW - timedelta(days=day)
        for tier, p, lo, hi in [
            ("epic", "0.01", "1000", "3000"),
            ("rare", "0.04", "200", "400"),
            ("uncommon", "0.15", "40", "80"),
            ("common", "0.80", "20", str(common_hi)),
        ]:
            session.add(
                PackOdds(
                    pack_id=pack.id,
                    tier=tier,
                    probability=D(p),
                    value_low=D(lo),
                    value_high=D(hi),
                    as_of=as_of,
                    provenance="api_json",
                )
            )
    # six cards with platform values and real sales → valuation gap
    for i in range(6):
        card = Card(
            canonical_key=f"pokemon|base set|{i}|-|PSA|10",
            game="pokemon",
            set_name="base set",
            number=str(i),
            grader="PSA",
            grade_num=D(10),
            display_name=f"card {i}",
        )
        session.add(card)
        session.flush()
        session.add(
            Valuation(
                source_id=cc.id,
                card_id=card.id,
                value_type=ValueType.insured_value,
                value=D(100 + 10 * i),
                as_of=NOW,
            )
        )
        for j in range(3):
            session.add(
                Sale(
                    source_id=cc.id,
                    external_id=f"s{i}{j}",
                    card_id=card.id,
                    price=D(100),
                    currency="USDC",
                    sold_at=NOW - timedelta(days=j + 1),
                )
            )
    session.commit()
    return session


def test_stranger_reproduces_house_edge_from_published_inputs(seeded, tmp_path):
    build.build(seeded, tmp_path, now=NOW)
    index = (tmp_path / "index.html").read_text()
    # The page states the formula and publishes each tier's p and buyback value.
    assert "house_edge = 1 − Σ pᵢ × buybackᵢ / price" in index
    rows = re.findall(
        r"<tr><td>(\w+)</td>" + r'<td class="num">([\d.]+)</td>' * 3,
        index,
    )
    assert len(rows) == 4
    ev_buyback = sum(D(p) * D(buyback) for _, p, _, buyback in rows)
    price = D("50")
    reproduced = ((1 - ev_buyback / price) * 100).quantize(D("0.01"))
    shown = D(re.search(r'class="num (?:ok|bad)">(-?[\d.]+)%', index).group(1))
    assert reproduced == shown
    # hand check of today's snapshot: midpoints 2000/300/60/25 × 0.85 → 1700/255/51/21.25
    # EV_buyback = 17 + 10.2 + 7.65 + 17 = 51.85 → edge = 1 − 51.85/50 = −3.70%
    assert shown == D("-3.70")


def test_pages_carry_required_disclosures(seeded, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "affiliate_links", {"collector_crypt": "https://example.com/ref"})
    build.build(seeded, tmp_path, now=NOW)
    index = (tmp_path / "index.html").read_text()
    head, _, body = index.partition("<h1>")
    assert "Disclosure:" in head and "referral links" in head  # above the fold, before content
    assert "18+" in head and "not a way to make money" in head
    assert 'rel="sponsored noopener"' in index
    for name in ["index.html", "valuation-gap.html", "methodology.html"]:
        page = (tmp_path / name).read_text()
        assert "Nothing on this site is financial advice" in page
        assert 'property="og:title"' in page and 'rel="canonical"' in page
    gap = (tmp_path / "valuation-gap.html").read_text()
    assert "Disclosure:" not in gap and "18+" not in gap  # no affiliate links or pack content there
    sitemap = (tmp_path / "sitemap.xml").read_text()
    assert "valuation-gap.html" in sitemap and "methodology.html" in sitemap
    assert (tmp_path / "robots.txt").read_text().startswith("User-agent: *")


def test_methodology_page_renders_markdown_with_worked_example(seeded, tmp_path):
    build.build(seeded, tmp_path, now=NOW)
    m = (tmp_path / "methodology.html").read_text()
    assert "<h2" in m and "house_edge" in m and "Worked example" in m and "<table>" in m


def test_valuation_gap_is_aggregate_only(seeded, tmp_path):
    build.build(seeded, tmp_path, now=NOW)
    gap = (tmp_path / "valuation-gap.html").read_text()
    assert "collector_crypt" in gap and '<td class="num">6</td>' in gap
    # platform values 100..150 over real median 100 → ratios 1.0..1.5, median 1.25, 5/6 above
    assert "1.2500" in gap and "83.3%" in gap
    for raw in ["110", "120", "130", "140", "150"]:  # individual platform values never appear
        assert f">{raw}<" not in gap
    # aggregate helper omits small groups
    pairs = [aggregate.GapPair("x", f"k{i}", D(2), D(1)) for i in range(4)]
    assert aggregate.valuation_gap(pairs) == []


def test_house_edge_series_tracks_snapshots(seeded):
    pts = aggregate.house_edge_series(build.odds_rows(seeded))
    assert [p.as_of for p in pts] == sorted(p.as_of for p in pts) and len(pts) == 2
    assert pts[0].ev.house_edge != pts[1].ev.house_edge  # the common band changed between days
