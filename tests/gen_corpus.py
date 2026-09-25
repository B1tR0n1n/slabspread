"""Generate fixtures/corpus/: 50 schema-faithful slab records + ground truth.

SYNTHETIC. Shapes copy fixtures/real/ exactly; card names/sets are real Pokémon cards but
certs, prices, token ids and wallets are invented. Deterministic (seeded). Run:

    python tests/gen_corpus.py

Design of the corpus (what the exit test needs to exercise):
  * 25 Courtyard tokenURI records, all with cert (`Serial`).
  * 25 Collector Crypt marketplace rows: 20 with `gradingID` (cert), 5 without.
  * 15 physical slabs appear on BOTH sources with the same cert  → cert identity.
  * 5 cards appear on both at the same grade with different certs → canonical identity.
  * 5 CC rows without cert have noisy titles, and their slab exists on Courtyard → fuzzy candidates.
  * Includes a "same card, different grade" trap and a "same name, different set" trap.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "fixtures" / "corpus"
rng = random.Random(20260925)

# (year, courtyard_set, cc_set, number, name, variant_untyped, game)
CARDS = [
    (1999, "Pokemon Game", "Pokemon Game", "2", "Blastoise", "Holo", "Pokemon"),
    (1999, "Pokemon Game", "Pokemon Game", "4", "Charizard", "Holo", "Pokemon"),
    (1999, "Pokemon Game", "Pokemon Game", "15", "Venusaur", "Holo", "Pokemon"),
    (1999, "Pokemon Game", "Pokemon Game", "58", "Pikachu", "", "Pokemon"),
    (1999, "Pokemon Game", "Pokemon Game", "85", "Pokemon Center", "", "Pokemon"),
    (
        2021,
        "Pokémon Swsh Black Star Promo",
        "Pokemon SWSH Black Star Promos",
        "182",
        "Vaporeon Vmax",
        "Full Art",
        "Pokémon",
    ),
    (
        2021,
        "Pokémon Swsh Black Star Promo",
        "Pokemon SWSH Black Star Promos",
        "183",
        "Jolteon Vmax",
        "Full Art",
        "Pokémon",
    ),
    (
        2023,
        "Scarlet & Violet 151",
        "Pokemon 151",
        "199",
        "Charizard ex",
        "Special Illustration Rare",
        "Pokemon",
    ),
    (2023, "Scarlet & Violet 151", "Pokemon 151", "129", "Magikarp", "", "Pokemon"),
    (2023, "Scarlet & Violet 151", "Pokemon 151", "6", "Charizard", "Reverse Holo", "Pokemon"),
    (2024, "SV05 Temporal Forces", "Pokemon Tef EN-Temporal Forces", "51", "Pikachu", "", "Pokemon"),
    (
        2024,
        "SV05 Temporal Forces",
        "Pokemon Tef EN-Temporal Forces",
        "218",
        "Iron Leaves ex",
        "Illustration Rare",
        "Pokemon",
    ),
    (2016, "XY Evolutions", "Pokemon XY Evolutions", "11", "Charizard", "Holo", "Pokemon"),
    (2016, "XY Evolutions", "Pokemon XY Evolutions", "2", "Blastoise", "Holo", "Pokemon"),
    (2000, "Neo Genesis", "Pokemon Neo Genesis", "9", "Lugia", "Holo", "Pokemon"),
    (2002, "Neo Destiny", "Pokemon Neo Destiny", "107", "Shining Charizard", "", "Pokemon"),
    (2003, "Skyridge", "Pokemon Skyridge", "H6", "Crystal Charizard", "", "Pokemon"),
    (2010, "HGSS Undaunted", "Pokemon HS Undaunted", "89", "Umbreon Prime", "", "Pokemon"),
    (2019, "Hidden Fates", "Pokemon Hidden Fates", "SV49", "Charizard GX", "Shiny", "Pokemon"),
    (2020, "Champions Path", "Pokemon Champions Path", "74", "Charizard Vmax", "Rainbow Rare", "Pokemon"),
]

GRADES = [
    ("PSA", "10 GEM MINT", "GEM-MT 10"),
    ("PSA", "9 MINT", "MINT 9"),
    ("PSA", "8 NM-MT", "NM-MT 8"),
    ("CGC", "10 GEM MINT", "GEM MINT 10"),
]


def cert() -> str:
    return str(rng.randint(40_000_000, 99_999_999))


def cy_record(card, grader, cy_grade, c, token_seed) -> dict:
    year, cyset, _, num, name, var, game = card
    label = f"{year} {cyset} #{num} {name}{(' - ' + var) if var else ''} ({grader} {cy_grade})"
    attrs = [
        {"trait_type": "Grader", "value": grader},
        {"trait_type": "Serial", "value": c},
        {"trait_type": "Grade", "value": cy_grade},
        {"trait_type": "Category", "value": game},
        {"trait_type": "Year", "value": str(year)},
        {"trait_type": "Set", "value": cyset},
        {"trait_type": "Title/Subject", "value": name},
        {"trait_type": "Language", "value": "English"},
        {"trait_type": "Card Number", "value": num},
    ]
    if var:
        attrs.append({"value": var})
    attrs.append({"trait_type": "Event", "value": "Pokemon Platinum Pack"})
    return {
        "collection_name": "Graded Cards",
        "name": label,
        "image": f"https://static.courtyard.io/graded-cards-renders/{grader}%20{c}/nft_image.jpg",
        "token_info": {
            "token_id": str(token_seed),
            "contract_address": "0x251BE3A17Af4892035C37ebf5890F4a4D889dcAD",
            "chain": "polygon",
        },
        "item_info": {"storage": {"vaulted": True, "insured": True, "location": "Courtyard US"}},
        "attributes": attrs,
        "product_type": "GRADED_CARD",
    }


def cc_row(card, grader, cc_grade, grade_num, c: str | None, idx: int, noisy: bool) -> dict:
    year, _, ccset, num, name, var, _ = card
    shown = name
    if noisy:
        shown = rng.choice(
            [name.upper(), name.replace("Charizard", "Zard"), f"{name} {var}".strip(), name.replace(" ", "")]
        )
    item = f"{year} #{num.zfill(3) if num.isdigit() else num} {shown} {grader} {grade_num} {ccset.replace('Pokemon ', '')}"
    row = {
        "id": f"2026{idx:08d}",
        "itemName": item,
        "nftAddress": "".join(
            rng.choice("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz") for _ in range(44)
        ),
        "category": "Pokemon",
        "type": "Card",
        "year": year,
        "grade": cc_grade,
        "gradeNum": None,
        "gradingCompany": grader,
        "set": ccset,
        "serial": num.zfill(3) if num.isdigit() else num,
        "insuredValue": str(rng.choice([32, 60, 150, 600, 1200, 4500])),
        "blockchain": "Solana",
        "listing": {
            "createdAt": "2026-07-31T03:36:22.354Z",
            "currency": "USDC",
            "price": rng.choice([37, 70, 165, 654, 1300, 4900]),
            "marketplace": "CC",
        },
        "offers": [],
        "owner": {"wallet": "EofCkTaFXUjdwpQdbTnjMsZD1nqjGTenUGFsfEdkraYN"},
        "images": {"front": f"https://d1xpxki1g4htqu.cloudfront.net/corpus{idx}"},
    }
    if c:
        row["gradingID"] = c
    return row


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cy, cc, truth = [], [], {"same_slab": [], "same_card": [], "fuzzy_only": [], "traps": []}
    token = 10**70

    # 20 Courtyard slabs; the first 15 also appear on CC with the same cert
    for i, card in enumerate(CARDS):
        grader, cy_g, cc_g = GRADES[i % len(GRADES)]
        gnum = cy_g.split()[0]
        c = cert()
        token += 7919
        cy.append(cy_record(card, grader, cy_g, c, token))
        if i < 15:
            cc.append(cc_row(card, grader, cc_g, gnum, c, len(cc), noisy=False))
            truth["same_slab"].append(
                {"cert": c, "grader": grader, "courtyard": str(token), "cc": cc[-1]["nftAddress"]}
            )

    # 5 same card, same grade, different cert (canonical identity). Variant-less cards on purpose:
    # CC rows carry no variant token, so a Courtyard "Holo" record vs a CC record of the same
    # card is a *candidate*, not a canonical match (decisions.md).
    for card in [CARDS[i] for i in (3, 4, 8, 10, 15)]:
        grader, cy_g, cc_g = GRADES[0]
        c1, c2 = cert(), cert()
        token += 7919
        cy.append(cy_record(card, grader, cy_g, c1, token))
        cc.append(cc_row(card, grader, cc_g, "10", c2, len(cc), noisy=False))
        truth["same_card"].append({"courtyard": str(token), "cc": cc[-1]["nftAddress"]})

    # 5 CC rows without cert, noisy names, same grade as the Courtyard slab → fuzzy candidates
    for i, card in enumerate(CARDS[15:20], start=15):
        grader, cy_g, cc_g = GRADES[i % len(GRADES)]
        gnum = cy_g.split()[0]
        cc.append(cc_row(card, grader, cc_g, gnum, None, len(cc), noisy=True))
        truth["fuzzy_only"].append(
            {"cc": cc[-1]["nftAddress"], "expect_candidate_courtyard": cy[i]["token_info"]["token_id"]}
        )

    # traps: same card different grade must NOT be same_card; same name different set must NOT match
    truth["traps"].append(
        {
            "kind": "same_card_different_grade",
            "courtyard": cy[0]["token_info"]["token_id"],
            "cc_set_grade": "PSA 9",
        }
    )
    truth["traps"].append(
        {"kind": "same_name_different_set", "a": "Charizard base set #4", "b": "Charizard XY Evolutions #11"}
    )

    (OUT / "courtyard_metadata.json").write_text(json.dumps(cy, indent=1))
    (OUT / "collectorcrypt_marketplace.json").write_text(
        json.dumps({"filterNFtCard": cc, "findTotal": len(cc)}, indent=1)
    )
    (OUT / "truth.json").write_text(json.dumps(truth, indent=1))
    print(f"wrote {len(cy)} courtyard + {len(cc)} collector crypt records to {OUT}")


if __name__ == "__main__":
    main()
