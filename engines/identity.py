"""Card identity — plan §3.

Three strategies in priority order:
  1. cert       (grader, cert_number)  → exact slab match
  2. canonical  (game, set, number, variant, grader, grade) → same card at same grade
  3. fuzzy      title similarity → a *candidate* with a confidence, never auto-trusted

Everything here is a pure function over `NormalizedSlab`, the shape every ingest
normalizer emits. The resolver returns *what it found and why*, so the admin page
can show a human the full reasoning.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from rapidfuzz import fuzz

# --------------------------------------------------------------------------------------
# Normalized input
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class NormalizedSlab:
    """One graded (or raw) card as a source describes it, after field-level cleanup."""

    source: str
    external_id: str
    title: str
    game: str | None = None
    set_name: str | None = None
    number: str | None = None
    name: str | None = None
    year: int | None = None
    language: str | None = None
    variant_tokens: tuple[str, ...] = ()
    grader: str | None = None
    cert_number: str | None = None
    grade_label: str | None = None
    grade_num: Decimal | None = None
    image_url: str | None = None
    raw: dict = field(default_factory=dict, compare=False, hash=False)

    @property
    def is_graded(self) -> bool:
        return self.grader is not None and self.grade_num is not None

    @property
    def has_cert(self) -> bool:
        return bool(self.grader and self.cert_number)


# --------------------------------------------------------------------------------------
# Field normalizers
# --------------------------------------------------------------------------------------

GRADER_ALIASES: dict[str, str] = {
    "psa": "PSA",
    "professional sports authenticator": "PSA",
    "professional sports authenticator (psa)": "PSA",
    "bgs": "BGS",
    "beckett": "BGS",
    "beckett grading services": "BGS",
    "cgc": "CGC",
    "cgc cards": "CGC",
    "sgc": "SGC",
    "tag": "TAG",
    "ace": "ACE",
}

GAME_ALIASES: dict[str, str] = {
    "pokemon": "pokemon",
    "pokémon": "pokemon",
    "pokemon tcg": "pokemon",
    "mtg": "mtg",
    "magic": "mtg",
    "magic: the gathering": "mtg",
    "yugioh": "yugioh",
    "yu-gi-oh": "yugioh",
    "yu-gi-oh!": "yugioh",
    "one piece": "one_piece",
    "lorcana": "lorcana",
    "baseball": "baseball",
    "basketball": "basketball",
    "football": "football",
    "hockey": "hockey",
    "soccer": "soccer",
}

# Set-name aliases across platforms. Keep small and explicit; every entry is a claim.
SET_ALIASES: dict[str, str] = {
    "pokemon game": "base set",
    "base": "base set",
    "base set": "base set",
    "pokemon base set": "base set",
    "pokemon tef en-temporal forces": "temporal forces",
    "tef en-temporal forces": "temporal forces",
    "sv05 temporal forces": "temporal forces",
    "pokemon swsh black star promo": "swsh black star promo",
    "swsh black star promos": "swsh black star promo",
    "sv 151": "151",
    "scarlet & violet 151": "151",
    "scarlet and violet 151": "151",
    "pokemon 151": "151",
    "hs undaunted": "hgss undaunted",
    "heartgold soulsilver undaunted": "hgss undaunted",
}

# Sets whose name alone identifies the game. Used only when a source gives no game field
# (Phygitals). Anything not listed stays game-less and is rejected rather than guessed.
POKEMON_SETS: frozenset[str] = frozenset(
    {
        "base set",
        "jungle",
        "fossil",
        "team rocket",
        "gym heroes",
        "gym challenge",
        "neo genesis",
        "neo discovery",
        "neo revelation",
        "neo destiny",
        "legendary collection",
        "expedition",
        "aquapolis",
        "skyridge",
        "ruby & sapphire",
        "sandstorm",
        "dragon",
        "team magma vs team aqua",
        "hidden legends",
        "firered & leafgreen",
        "team rocket returns",
        "deoxys",
        "emerald",
        "unseen forces",
        "delta species",
        "legend maker",
        "holon phantoms",
        "crystal guardians",
        "dragon frontiers",
        "power keepers",
        "diamond & pearl",
        "mysterious treasures",
        "secret wonders",
        "great encounters",
        "majestic dawn",
        "legends awakened",
        "stormfront",
        "platinum",
        "rising rivals",
        "supreme victors",
        "arceus",
        "heartgold soulsilver",
        "hgss undaunted",
        "unleashed",
        "undaunted",
        "triumphant",
        "call of legends",
        "black & white",
        "emerging powers",
        "noble victories",
        "next destinies",
        "dark explorers",
        "dragons exalted",
        "boundaries crossed",
        "plasma storm",
        "plasma freeze",
        "plasma blast",
        "legendary treasures",
        "xy",
        "flashfire",
        "furious fists",
        "phantom forces",
        "primal clash",
        "roaring skies",
        "ancient origins",
        "breakthrough",
        "breakpoint",
        "generations",
        "fates collide",
        "steam siege",
        "evolutions",
        "xy evolutions",
        "sun & moon",
        "guardians rising",
        "burning shadows",
        "shining legends",
        "crimson invasion",
        "ultra prism",
        "forbidden light",
        "celestial storm",
        "dragon majesty",
        "lost thunder",
        "team up",
        "detective pikachu",
        "unbroken bonds",
        "unified minds",
        "hidden fates",
        "cosmic eclipse",
        "sword & shield",
        "rebel clash",
        "darkness ablaze",
        "champions path",
        "champion's path",
        "vivid voltage",
        "shining fates",
        "battle styles",
        "chilling reign",
        "evolving skies",
        "celebrations",
        "fusion strike",
        "brilliant stars",
        "astral radiance",
        "pokemon go",
        "lost origin",
        "silver tempest",
        "crown zenith",
        "scarlet & violet",
        "paldea evolved",
        "obsidian flames",
        "151",
        "paradox rift",
        "paldean fates",
        "temporal forces",
        "twilight masquerade",
        "shrouded fable",
        "stellar crown",
        "surging sparks",
        "prismatic evolutions",
        "journey together",
        "destined rivals",
        "black bolt",
        "white flare",
        "mega evolution",
        "swsh black star promo",
        "sm black star promo",
        "xy black star promo",
        "sv black star promo",
        "wizards black star promo",
    }
)


def infer_game_from_set(set_name: str | None) -> str | None:
    q = normalize_set(set_name)
    return "pokemon" if q in POKEMON_SETS else None


_GRADE_WORDS = {
    "gem mint",
    "gem-mt",
    "gem mt",
    "gem",
    "mint",
    "mt",
    "nm-mt",
    "nm mt",
    "nm",
    "near mint",
    "pristine",
    "black label",
    "ex-mt",
    "ex",
    "vg-ex",
    "vg",
    "good",
    "fair",
    "poor",
    "authentic",
}

_NUM_RE = re.compile(r"(?<![\d.])(10(?:\.0)?|[0-9](?:\.[05])?)(?![\d.])")

# Tokens that change *which card* it is. Anything else in an untyped attribute
# ("Vaporeon Vmax Premium Collection", "Common") is descriptive and stays out of the key.
VARIANT_VOCAB: frozenset[str] = frozenset(
    {
        "holo",
        "reverse holo",
        "non holo",
        "full art",
        "alt art",
        "alternate art",
        "secret rare",
        "hyper rare",
        "rainbow rare",
        "gold",
        "illustration rare",
        "special illustration rare",
        "1st edition",
        "first edition",
        "shadowless",
        "unlimited",
        "promo",
        "staff",
        "prerelease",
        "error",
        "misprint",
        "signed",
        "refractor",
        "auto",
        "autograph",
        "rookie",
        "rc",
        "parallel",
        "numbered",
        "japanese",
        "korean",
    }
)


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def squash(s: str | None) -> str:
    """Lowercase, accent-free, single-spaced, punctuation-light."""
    if not s:
        return ""
    s = strip_accents(s).lower().replace("�", "e")  # mojibake seen in Phygitals "Pok�mon"
    s = re.sub(r"[^\w\s#&'/.-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


_GRADER_TOKEN = re.compile(r"\b(psa|bgs|beckett|cgc|sgc|tag|ace)\b")


def normalize_grader(s: str | None) -> str | None:
    if not s:
        return None
    q = squash(s)
    if q in GRADER_ALIASES:
        return GRADER_ALIASES[q]
    m = _GRADER_TOKEN.search(q)
    if m:
        return GRADER_ALIASES[m.group(1)]
    return q.upper() or None


def normalize_game(s: str | None) -> str | None:
    if not s:
        return None
    return GAME_ALIASES.get(squash(s), squash(s).replace(" ", "_") or None)


_GAME_PREFIX = re.compile(r"^(pokemon|magic|mtg|yugioh|yu-gi-oh!?|one piece|lorcana)\s+(tcg\s+)?")


def normalize_set(s: str | None) -> str | None:
    """Alias table first; then drop a leading game word ("Pokemon Neo Destiny" → "neo destiny")
    and try the table again. Collector Crypt prefixes every set with the game; Courtyard does not."""
    if not s:
        return None
    q = squash(s)
    if q in SET_ALIASES:
        return SET_ALIASES[q]
    q = _GAME_PREFIX.sub("", q)
    return SET_ALIASES.get(q, q) or None


def normalize_number(s: str | None) -> str | None:
    """'#051' → '51'; 'TG12/TG30' → 'tg12'; '182' → '182'."""
    if s is None:
        return None
    q = squash(str(s)).lstrip("#").split("/")[0].strip()
    if not q:
        return None
    m = re.fullmatch(r"([a-z]*)0*(\d+)([a-z]*)", q)
    return f"{m.group(1)}{m.group(2)}{m.group(3)}" if m else q


def parse_grade(label: str | None) -> tuple[Decimal | None, str | None]:
    """Return (numeric grade, qualifier) from labels seen in the wild.

    '8 NM-MT' → (8, 'NM-MT'); 'GEM-MT 10' → (10, 'GEM-MT'); 'PSA 10' → (10, None);
    'CGC 10.0' → (10, None); 'Ungraded' / 'Raw' / None → (None, None).
    """
    if not label:
        return None, None
    q = squash(label)
    if q in {"ungraded", "raw", "n/a", "none"}:
        return None, None
    m = _NUM_RE.search(q)
    if not m:
        return None, label.strip() or None
    num = Decimal(m.group(1))
    qualifier = _NUM_RE.sub("", q)
    qualifier = re.sub(r"\b(psa|bgs|cgc|sgc|tag|ace)\b", "", qualifier).strip(" -")
    return num, (qualifier.upper() or None)


def normalize_cert(s: str | None) -> str | None:
    if s is None:
        return None
    q = re.sub(r"\s+", "", str(s))
    return q or None


# --------------------------------------------------------------------------------------
# Canonical key
# --------------------------------------------------------------------------------------


def known_variants(tokens: tuple[str, ...]) -> set[str]:
    return {squash(t) for t in tokens if squash(t) in VARIANT_VOCAB}


def canonical_key(slab: NormalizedSlab) -> str | None:
    """`game|set|number|variant|grader|grade` — the identity of "this card at this grade".

    Returns None when the record lacks enough to be canonical (no game or set).
    Raw cards get grader/grade of `raw`.
    """
    game = normalize_game(slab.game)
    set_name = normalize_set(slab.set_name)
    if not game or not set_name:
        return None
    number = normalize_number(slab.number) or "-"
    variant = "+".join(sorted(known_variants(slab.variant_tokens))) or "-"
    if slab.is_graded:
        grader = slab.grader
        grade = f"{slab.grade_num.normalize():f}"
    else:
        grader, grade = "raw", "raw"
    return f"{game}|{set_name}|{number}|{variant}|{grader}|{grade}"


# --------------------------------------------------------------------------------------
# Fuzzy scoring
# --------------------------------------------------------------------------------------


def _title_for_fuzzy(slab: NormalizedSlab) -> str:
    parts = [slab.title, slab.name, slab.set_name, slab.number and f"#{slab.number}"]
    return squash(" ".join(p for p in parts if p))


def fuzzy_score(a: NormalizedSlab, b: NormalizedSlab) -> tuple[float, dict]:
    """0..1 similarity with an explanation dict. Pure; no thresholds applied here.

    Title similarity carries the score; hard field disagreements (grader, grade,
    year, number) subtract, because "same title, different grade" is a different card.
    """
    title_sim = fuzz.token_set_ratio(_title_for_fuzzy(a), _title_for_fuzzy(b)) / 100.0
    penalties: dict[str, float] = {}

    if a.is_graded and b.is_graded:
        if a.grader != b.grader:
            penalties["grader_mismatch"] = 0.5
        if a.grade_num != b.grade_num:
            penalties["grade_mismatch"] = 0.5
    elif a.is_graded != b.is_graded:
        penalties["graded_vs_raw"] = 0.5

    if a.year and b.year and a.year != b.year:
        penalties["year_mismatch"] = 0.3

    na, nb = normalize_number(a.number), normalize_number(b.number)
    if na and nb and na != nb:
        penalties["number_mismatch"] = 0.4

    ga, gb = normalize_game(a.game), normalize_game(b.game)
    if ga and gb and ga != gb:
        penalties["game_mismatch"] = 0.6

    score = max(0.0, min(1.0, title_sim - sum(penalties.values())))
    return score, {"title_similarity": round(title_sim, 3), "penalties": penalties}


# --------------------------------------------------------------------------------------
# Resolver
# --------------------------------------------------------------------------------------


class Method(StrEnum):
    cert = "cert"
    canonical = "canonical"
    fuzzy = "fuzzy"
    none = "none"


@dataclass(frozen=True)
class Resolution:
    method: Method
    cert_key: tuple[str, str] | None = None  # (grader, cert)
    canonical: str | None = None
    candidates: tuple[tuple[str, float, dict], ...] = ()  # (other external_id, score, why)


def resolve(
    slab: NormalizedSlab,
    known: list[NormalizedSlab],
    *,
    record_min: float,
) -> Resolution:
    """Decide how `slab` identifies against `known`.

    Cert wins outright. Canonical is next. Otherwise every `known` record that scores
    ≥ `record_min` becomes a candidate — ranked, explained, and left for a human.
    """
    if slab.has_cert:
        key = (slab.grader, normalize_cert(slab.cert_number))
        for k in known:
            if k.has_cert and (k.grader, normalize_cert(k.cert_number)) == key:
                return Resolution(Method.cert, cert_key=key, canonical=canonical_key(slab))
        # No prior slab with this cert: still identified by cert, just new.
        return Resolution(Method.cert, cert_key=key, canonical=canonical_key(slab))

    ck = canonical_key(slab)
    if ck and any(canonical_key(k) == ck for k in known):
        return Resolution(Method.canonical, canonical=ck)

    scored = []
    for k in known:
        score, why = fuzzy_score(slab, k)
        if score >= record_min:
            scored.append((k.external_id, score, why))
    scored.sort(key=lambda t: -t[1])
    if scored:
        return Resolution(Method.fuzzy, canonical=ck, candidates=tuple(scored))
    return Resolution(Method.none, canonical=ck)
