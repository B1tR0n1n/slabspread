from decimal import Decimal

from engines.identity import (
    NormalizedSlab,
    canonical_key,
    fuzzy_score,
    normalize_grader,
    normalize_number,
    normalize_set,
    parse_grade,
    resolve,
)


def test_parse_grade_labels_seen_in_the_wild():
    assert parse_grade("8 NM-MT") == (Decimal(8), "NM-MT")
    assert parse_grade("GEM-MT 10") == (Decimal(10), "GEM-MT")
    assert parse_grade("MINT 9") == (Decimal(9), "MINT")
    assert parse_grade("PSA 10") == (Decimal(10), None)
    assert parse_grade("CGC 10.0")[0] == Decimal("10.0")
    assert parse_grade("BGS 9.5 GEM MINT") == (Decimal("9.5"), "GEM MINT")
    assert parse_grade("Ungraded") == (None, None)
    assert parse_grade(None) == (None, None)


def test_normalizers():
    assert normalize_grader("Professional Sports Authenticator (PSA)") == "PSA"
    assert normalize_grader("Beckett") == "BGS"
    assert normalize_number("#051") == "51"
    assert normalize_number("TG12/TG30") == "tg12"
    assert normalize_number("H6") == "h6"
    assert normalize_set("Pokemon Game") == "base set"
    assert normalize_set("Pokémon Swsh Black Star Promo") == "swsh black star promo"


def _slab(**kw) -> NormalizedSlab:
    base = dict(
        source="t",
        external_id="x",
        title="t",
        game="Pokemon",
        set_name="Pokemon Game",
        number="4",
        grader="PSA",
        grade_num=Decimal(10),
        grade_label="GEM MINT 10",
    )
    return NormalizedSlab(**{**base, **kw})


def test_canonical_key_ignores_descriptive_tokens_but_keeps_variants():
    a = _slab(variant_tokens=("Holo", "Vaporeon Vmax Premium Collection"))
    b = _slab(variant_tokens=("Holo",))
    c = _slab(variant_tokens=())
    assert canonical_key(a) == canonical_key(b) == "pokemon|base set|4|holo|PSA|10"
    assert canonical_key(c) != canonical_key(a)


def test_canonical_key_distinguishes_grade_and_raw():
    assert canonical_key(_slab()) != canonical_key(_slab(grade_num=Decimal(9)))
    raw = _slab(grader=None, grade_num=None, grade_label="Ungraded")
    assert canonical_key(raw).endswith("|raw|raw")


def test_canonical_key_none_without_game_or_set():
    assert canonical_key(_slab(set_name=None)) is None


def test_fuzzy_penalises_hard_field_disagreement():
    same = _slab(title="1999 Pokemon Game #4 Charizard Holo PSA 10")
    other_grade = _slab(title="1999 Pokemon Game #4 Charizard Holo PSA 9", grade_num=Decimal(9))
    other_number = _slab(title="1999 Pokemon Game #2 Blastoise Holo PSA 10", number="2")
    s_same, _ = fuzzy_score(same, _slab(title="1999 Base Set Charizard #4 Holo (PSA 10)"))
    s_grade, why = fuzzy_score(same, other_grade)
    s_num, _ = fuzzy_score(same, other_number)
    assert s_same > 0.8
    assert s_grade < s_same and "grade_mismatch" in why["penalties"]
    assert s_num < s_same


def test_resolve_priority_cert_then_canonical_then_fuzzy():
    known = [
        _slab(external_id="k1", cert_number="111", title="1999 Pokemon Game #4 Charizard PSA 10"),
        _slab(external_id="k2", number="2", title="1999 Pokemon Game #2 Blastoise PSA 10"),
    ]
    assert resolve(_slab(cert_number="111"), known, record_min=0.5).method == "cert"
    assert resolve(_slab(cert_number="999"), known, record_min=0.5).method == "cert"  # new slab, still cert
    assert resolve(_slab(), known, record_min=0.5).method == "canonical"
    r = resolve(_slab(set_name="Neo Genesis", title="Neo Genesis Charizard #4 PSA 10"), known, record_min=0.5)
    assert r.method == "fuzzy" and r.candidates
    assert resolve(_slab(game="mtg", set_name="alpha", title="zzz"), known, record_min=0.5).method == "none"
