"""Normalizers against the *real* captured responses in fixtures/real/."""

from decimal import Decimal

from conftest import load

from engines.identity import canonical_key
from ingest import collectorcrypt, courtyard, phygitals


def test_courtyard_metadata_carries_cert_and_canonical_fields():
    s = courtyard.normalize_metadata(load("real/courtyard/metadata_psa66499345.json"))
    assert (s.grader, s.cert_number, s.grade_num) == ("PSA", "66499345", Decimal(8))
    assert s.grade_label == "8 NM-MT"
    assert (s.number, s.name, s.year, s.language) == ("2", "Blastoise", 1999, "English")
    assert s.variant_tokens == ("Holo",)
    assert canonical_key(s) == "pokemon|base set|2|holo|PSA|8"
    assert s.image_url.endswith("PSA%2066499345/nft_image.jpg")


def test_courtyard_orderbook_asset_yields_fmv():
    s, fmv = courtyard.normalize_orderbook_asset(load("real/courtyard/orderbook_asset_psa91000615.json"))
    assert (s.grader, s.cert_number, s.grade_num) == ("PSA", "91000615", Decimal(10))
    assert fmv == Decimal(732)
    assert canonical_key(s) == "pokemon|swsh black star promo|182|full art|PSA|10"


def test_collectorcrypt_rows():
    rows = collectorcrypt.normalize_page(load("real/collectorcrypt/marketplace_page.json"))
    pika, (center, iv), synthetic = rows[0][0], rows[1], rows[2][0]
    assert (pika.grader, pika.grade_num, pika.number, pika.name) == ("PSA", Decimal(9), "051", "Pikachu")
    assert pika.cert_number is None  # `serial` is the card number, not the cert
    assert canonical_key(pika) == "pokemon|temporal forces|51|-|PSA|9"
    assert canonical_key(center) == "pokemon|base set|85|-|PSA|10"
    assert iv == Decimal(600)
    assert canonical_key(synthetic) is None  # no set → cannot be canonical


def test_collectorcrypt_accepts_gradingid_when_present():
    row = load("real/collectorcrypt/marketplace_page.json")["filterNFtCard"][0] | {"gradingID": "12345678"}
    s, _ = collectorcrypt.normalize_row(row)
    assert s.cert_number == "12345678" and s.has_cert


def test_phygitals_listing_is_raw_with_micro_usdc_price():
    rows = phygitals.normalize_page(load("real/phygitals/marketplace_listings.json"))
    magikarp, ask = rows[0]
    assert not magikarp.is_graded and magikarp.cert_number is None
    assert ask == Decimal("0.3")
    assert canonical_key(magikarp) == "pokemon|151|129|-|raw|raw"
    pupitar, _ = rows[1]
    assert canonical_key(pupitar) == "pokemon|paldea evolved|111|-|raw|raw"  # mojibake 'Pok�mon' handled
