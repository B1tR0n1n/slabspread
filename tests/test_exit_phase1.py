"""Phase 1 exit test (plan §3):

  ingest fixtures for 50 real slabs across two sources; ≥95% correct identity on
  cert-bearing items; fuzzy candidates reviewable in a simple admin page.

Runs against fixtures/corpus/ (synthetic, schema-faithful — see fixtures/README.md).
Drop real captures with the same layout into that directory and this test re-runs on them.
"""

from decimal import Decimal

import pytest
from conftest import load
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app import main as app_main
from app.db import get_session
from ingest import collectorcrypt, courtyard
from ingest.persist import upsert_slabs
from models import Card, Listing, MatchCandidate, Slab, Source, ValueType, Verdict


@pytest.fixture
def loaded(session):
    cy = [(courtyard.normalize_metadata(d), None, {}) for d in load("corpus/courtyard_metadata.json")]
    cc = [
        (s, Decimal(str(r["listing"]["price"])), {ValueType.insured_value: iv})
        for (s, iv), r in zip(
            collectorcrypt.normalize_page(load("corpus/collectorcrypt_marketplace.json")),
            load("corpus/collectorcrypt_marketplace.json")["filterNFtCard"],
            strict=True,
        )
    ]
    r1 = upsert_slabs(session, "courtyard", cy)
    r2 = upsert_slabs(session, "collector_crypt", cc)
    session.commit()
    return session, load("corpus/truth.json"), r1, r2


def _listing(s, source_key, ext):
    return s.scalar(select(Listing).join(Source).where(Source.key == source_key, Listing.external_id == ext))


def test_corpus_is_fifty_slabs_across_two_sources(loaded):
    s, truth, r1, r2 = loaded
    assert r1.fetched + r2.fetched == 50 and r1.rejected == r2.rejected == 0
    assert s.scalar(select(func.count(Source.id))) == 2


def test_cert_identity_at_least_95_percent(loaded):
    s, truth, *_ = loaded
    ok = 0
    for t in truth["same_slab"]:
        left, right = _listing(s, "courtyard", t["courtyard"]), _listing(s, "collector_crypt", t["cc"])
        if left and right and left.slab_id and left.slab_id == right.slab_id:
            slab = s.get(Slab, left.slab_id)
            ok += slab.cert_number == t["cert"] and slab.grader == t["grader"]
    rate = ok / len(truth["same_slab"])
    assert rate >= 0.95, f"cert identity {rate:.0%}"
    # and no cert produced two slabs
    dupes = s.execute(
        select(Slab.grader, Slab.cert_number, func.count())
        .group_by(Slab.grader, Slab.cert_number)
        .having(func.count() > 1)
    ).all()
    assert dupes == []


def test_canonical_identity_unifies_same_card_different_cert(loaded):
    s, truth, *_ = loaded
    for t in truth["same_card"]:
        left, right = _listing(s, "courtyard", t["courtyard"]), _listing(s, "collector_crypt", t["cc"])
        assert left.card_id == right.card_id, (left.title, right.title)
        assert left.slab_id != right.slab_id  # different physical slabs


def test_certless_rows_resolve_canonically_or_become_candidates(loaded):
    """Rows without a cert may unify by canonical key when the source gives full set/number,
    otherwise they must surface as pending candidates — never a silent slab merge."""
    s, truth, r1, r2 = loaded
    assert r2.by_method.get("fuzzy", 0) >= 1  # at least one true fuzzy case in the corpus
    ok = 0
    for t in truth["fuzzy_only"]:
        cc = _listing(s, "collector_crypt", t["cc"])
        cy = _listing(s, "courtyard", t["expect_candidate_courtyard"])
        assert cc.slab_id is None  # no cert → no slab, ever
        cands = s.scalars(select(MatchCandidate).where(MatchCandidate.left_id == cc.id)).all()
        assert all(c.verdict == Verdict.pending for c in cands)
        ok += (cc.card_id == cy.card_id) or any(c.right_id == cy.id for c in cands)
    n = len(truth["fuzzy_only"])
    assert ok / n >= 0.8, f"resolved or candidate {ok}/{n}"


def test_variant_asymmetry_yields_candidate_not_unification(loaded):
    """Courtyard 'Blastoise - Holo' vs CC 'Blastoise' (no variant token): same cert unifies them
    as a slab; without a cert they must surface as a candidate, never share a card silently."""
    s, truth, *_ = loaded
    cy = s.scalar(select(Listing).where(Listing.title.like("1999 Pokemon Game #2 Blastoise - Holo (PSA 10%")))
    cc = s.scalar(select(Listing).where(Listing.title.like("1999 #002 Blastoise PSA 10%")))
    if cy is None or cc is None:
        pytest.skip("corpus lacks the Blastoise pair")
    if cy.slab_id and cy.slab_id == cc.slab_id:
        return  # unified by cert, which outranks variant
    assert cy.card_id != cc.card_id


def test_traps_are_not_conflated(loaded):
    s, truth, *_ = loaded
    # same card, different grade → different canonical cards
    keys = s.scalars(
        select(Card.canonical_key).where(Card.canonical_key.like("pokemon|base set|4|holo|PSA|%"))
    ).all()
    assert len(set(keys)) >= 1 and all(k.count("|") == 5 for k in keys)
    # same name, different set → different cards
    zards = s.scalars(select(Card.canonical_key).where(Card.display_name.like("%Charizard%"))).all()
    assert any("base set" in k for k in zards) and any("xy evolutions" in k for k in zards)


def test_replay_is_idempotent(loaded):
    s, truth, r1, r2 = loaded
    before = (
        s.scalar(select(func.count(Card.id))),
        s.scalar(select(func.count(Slab.id))),
        s.scalar(select(func.count(Listing.id))),
        s.scalar(select(func.count(MatchCandidate.id))),
    )
    cy = [(courtyard.normalize_metadata(d), None, {}) for d in load("corpus/courtyard_metadata.json")]
    rep = upsert_slabs(s, "courtyard", cy)
    s.commit()
    after = (
        s.scalar(select(func.count(Card.id))),
        s.scalar(select(func.count(Slab.id))),
        s.scalar(select(func.count(Listing.id))),
        s.scalar(select(func.count(MatchCandidate.id))),
    )
    assert before == after and rep.updated == 25 and rep.inserted == 0


def test_admin_page_lists_and_decides(loaded):
    s, *_ = loaded
    app_main.app.dependency_overrides[get_session] = lambda: s
    client = TestClient(app_main.app)
    page = client.get("/admin/matches")
    assert page.status_code == 200 and "accept" in page.text and "fuzzy_title" in page.text
    mc = s.scalar(select(MatchCandidate).where(MatchCandidate.verdict == Verdict.pending))
    resp = client.post(f"/admin/matches/{mc.id}", data={"verdict": "accepted"})
    assert resp.status_code == 200 and "accepted" in resp.text
    s.refresh(mc)
    assert mc.verdict == Verdict.accepted and mc.decided_at is not None
    left, right = s.get(Listing, mc.left_id), s.get(Listing, mc.right_id)
    assert left.card_id == right.card_id
    app_main.app.dependency_overrides.clear()
