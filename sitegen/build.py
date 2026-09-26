"""Build the public site into `settings.site_out_dir`:  python -m sitegen.build

Pages: House Edge Index, Valuation Gap, Methodology, plus sitemap.xml and robots.txt.
Every page carries the disclosures the plan requires; pack pages carry the 18+ notice;
affiliate links appear only for platforms present in `settings.affiliate_links`, with the
disclosure banner above the fold on those pages.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from models import Card, Pack, PackOdds, Sale, Source, Valuation, ValueType
from sitegen.aggregate import GapPair, OddsRow, house_edge_series, valuation_gap

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = Path(__file__).resolve().parent / "templates"


def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=select_autoescape(["html"]))
    env.globals.update(
        site_name=settings.site_name,
        base_url=settings.site_base_url.rstrip("/"),
        analytics=settings.analytics_snippet,
        built_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )
    return env


# --------------------------------------------------------------------------------------
# Data extraction (DB → plain records)
# --------------------------------------------------------------------------------------


def odds_rows(s: Session) -> list[OddsRow]:
    rows = s.execute(
        select(PackOdds, Pack, Source.key)
        .join(Pack, Pack.id == PackOdds.pack_id)
        .join(Source, Source.id == Pack.source_id)
    ).all()
    out = []
    for o, p, src in rows:
        pct = Decimal(str(p.buyback_pct if p.buyback_pct is not None else settings.buyback_pct.get(src, 0)))
        out.append(
            OddsRow(
                platform=src,
                pack_slug=p.slug,
                pack_name=p.name,
                pack_price=Decimal(p.price),
                buyback_pct=pct,
                as_of=o.as_of,
                tier=o.tier,
                probability=Decimal(o.probability),
                value_low=Decimal(o.value_low) if o.value_low is not None else None,
                value_high=Decimal(o.value_high) if o.value_high is not None else None,
                provenance=o.provenance,
                value_mean=Decimal(o.value_mean) if o.value_mean is not None else None,
                sample_n=o.sample_n,
                stated_ev=Decimal(o.stated_ev) if o.stated_ev is not None else None,
            )
        )
    return out


def gap_pairs(
    s: Session, *, window_days: int = 30, min_sales: int = 3, now: datetime | None = None
) -> list[GapPair]:
    """Cards with both a platform value and ≥ min_sales real sales in the window."""
    now = now or datetime.utcnow()
    since = now - timedelta(days=window_days)
    pairs = []
    for card in s.scalars(select(Card)).all():
        sales = [
            Decimal(x.price)
            for x in s.scalars(select(Sale).where(Sale.card_id == card.id, Sale.sold_at >= since))
        ]
        if len(sales) < min_sales:
            continue
        ext = Decimal(median(sales))
        vals = s.execute(
            select(Valuation, Source.key)
            .join(Source)
            .where(
                Valuation.card_id == card.id,
                Valuation.value_type.in_([ValueType.platform_fmv, ValueType.insured_value]),
            )
            .order_by(Valuation.as_of.desc())
        ).all()
        seen = set()
        for v, src in vals:
            if src in seen:
                continue
            seen.add(src)
            pairs.append(GapPair(src, card.canonical_key, Decimal(v.value), ext))
    return pairs


# --------------------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------------------


def build(s: Session, out_dir: str | Path | None = None, *, now: datetime | None = None) -> list[Path]:
    out = Path(out_dir or settings.site_out_dir)
    out.mkdir(parents=True, exist_ok=True)
    env = _env()
    written: list[Path] = []

    # House Edge Index -----------------------------------------------------------------
    points = house_edge_series(odds_rows(s))
    latest: dict[tuple[str, str], object] = {}
    for p in points:
        latest[(p.platform, p.pack_slug)] = p  # sorted ascending by as_of → last wins
    series = {}
    for p in points:
        series.setdefault(f"{p.platform} · {p.pack_name}", []).append(
            {"x": p.as_of.isoformat(), "y": float(p.ev.house_edge)}
        )
    affiliate_platforms = {k for k in settings.affiliate_links if any(p.platform == k for p in points)}
    page = env.get_template("index.html").render(
        latest=sorted(latest.values(), key=lambda p: p.ev.house_edge),
        series_json=json.dumps(series),
        affiliate_links={k: v for k, v in settings.affiliate_links.items() if k in affiliate_platforms},
        has_affiliate=bool(affiliate_platforms),
        pack_content=True,
    )
    written.append(_write(out / "index.html", page))

    # Valuation gap --------------------------------------------------------------------
    gaps = valuation_gap(gap_pairs(s, now=now))
    page = env.get_template("valuation-gap.html").render(gaps=gaps, has_affiliate=False, pack_content=False)
    written.append(_write(out / "valuation-gap.html", page))

    # Methodology (from docs/methodology.md) --------------------------------------------
    md = (ROOT / "docs" / "methodology.md").read_text()
    body = markdown.markdown(md, extensions=["tables", "fenced_code"])
    page = env.get_template("methodology.html").render(body=body, has_affiliate=False, pack_content=False)
    written.append(_write(out / "methodology.html", page))

    # sitemap + robots -----------------------------------------------------------------
    base = settings.site_base_url.rstrip("/")
    urls = "".join(
        f"<url><loc>{html.escape(base)}/{n}</loc></url>"
        for n in ["", "valuation-gap.html", "methodology.html"]
    )
    written.append(
        _write(
            out / "sitemap.xml",
            f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        )
    )
    written.append(_write(out / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"))
    return written


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


if __name__ == "__main__":
    from app.db import session_scope

    with session_scope() as sess:
        for p in build(sess):
            print("wrote", p)
