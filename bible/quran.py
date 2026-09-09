"""Quran data loading, reference parsing, and adapter for the bible package.

Adheres to docs/data-schema.md §2 (multi-tradition canonical schema) and
docs/phase3-scope-quran.md (Phase 3.1 scope).

Exposes:
    parse_quran_ref(raw: str) -> Optional[tuple[int, int | tuple[int, int]]]
    list_quran_translations() -> list[str]
    load_quran_edition(key: str) -> dict
    get_quran_verses(edition: str, surah: int, ayah_or_range: int | tuple[int, int]) -> list[dict]
    run_quran(ref: str, translations: list[str] = None, as_json: bool = False)
"""

from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).resolve().parent.parent
QURAN_DATA_DIR = ROOT / "data" / "quran"

# ---------------------------------------------------------------------------
# Canonical 114 Surahs Metadata (public domain, historical consensus)
# (id, canonical_name, english_name, transliteration, revelation_period, total_ayahs)
# ---------------------------------------------------------------------------

SURAHS = [
    (1, "Al-Fatihah", "The Opening", "al-fatihah", "Meccan", 7),
    (2, "Al-Baqarah", "The Cow", "al-baqarah", "Medinan", 286),
    (3, "Ali 'Imran", "Family of Imran", "ali-imran", "Medinan", 200),
    (4, "An-Nisa", "The Women", "an-nisa", "Medinan", 176),
    (5, "Al-Ma'idah", "The Table Spread", "al-maidah", "Medinan", 120),
    (6, "Al-An'am", "The Cattle", "al-anam", "Meccan", 165),
    (7, "Al-A'raf", "The Heights", "al-araf", "Meccan", 206),
    (8, "Al-Anfal", "The Spoils of War", "al-anfal", "Medinan", 75),
    (9, "At-Tawbah", "The Repentance", "at-tawbah", "Medinan", 129),
    (10, "Yunus", "Jonah", "yunus", "Meccan", 109),
    (11, "Hud", "Hud", "hud", "Meccan", 123),
    (12, "Yusuf", "Joseph", "yusuf", "Meccan", 111),
    (13, "Ar-Ra'd", "The Thunder", "ar-rad", "Medinan", 43),
    (14, "Ibrahim", "Abraham", "ibrahim", "Meccan", 52),
    (15, "Al-Hijr", "The Rocky Tract", "al-hijr", "Meccan", 99),
    (16, "An-Nahl", "The Bee", "an-nahl", "Meccan", 128),
    (17, "Al-Isra", "The Night Journey", "al-isra", "Meccan", 111),
    (18, "Al-Kahf", "The Cave", "al-kahf", "Meccan", 110),
    (19, "Maryam", "Mary", "maryam", "Meccan", 98),
    (20, "Taha", "Ta-Ha", "taha", "Meccan", 135),
    (21, "Al-Anbiya", "The Prophets", "al-anbiya", "Meccan", 112),
    (22, "Al-Hajj", "The Pilgrimage", "al-hajj", "Medinan", 78),
    (23, "Al-Mu'minun", "The Believers", "al-muminun", "Meccan", 118),
    (24, "An-Nur", "The Light", "an-nur", "Medinan", 64),
    (25, "Al-Furqan", "The Criterion", "al-furqan", "Meccan", 77),
    (26, "Ash-Shu'ara", "The Poets", "ash-shuara", "Meccan", 227),
    (27, "An-Naml", "The Ant", "an-naml", "Meccan", 93),
    (28, "Al-Qasas", "The Stories", "al-qasas", "Meccan", 88),
    (29, "Al-'Ankabut", "The Spider", "al-ankabut", "Meccan", 69),
    (30, "Ar-Rum", "The Romans", "ar-rum", "Meccan", 60),
    (31, "Luqman", "Luqman", "luqman", "Meccan", 34),
    (32, "As-Sajdah", "The Prostration", "as-sajdah", "Meccan", 30),
    (33, "Al-Ahzab", "The Combined Forces", "al-ahzab", "Medinan", 73),
    (34, "Saba", "Sheba", "saba", "Meccan", 54),
    (35, "Fatir", "Originator", "fatir", "Meccan", 45),
    (36, "Ya-Sin", "Ya-Sin", "ya-sin", "Meccan", 83),
    (37, "As-Saffat", "Those who set the Ranks", "as-saffat", "Meccan", 182),
    (38, "Sad", "The Letter Sad", "sad", "Meccan", 88),
    (39, "Az-Zumar", "The Troops", "az-zumar", "Meccan", 75),
    (40, "Ghafir", "The Forgiver", "ghafir", "Meccan", 85),
    (41, "Fussilat", "Explained in Detail", "fussilat", "Meccan", 54),
    (42, "Ash-Shura", "The Consultation", "ash-shura", "Meccan", 53),
    (43, "Az-Zukhruf", "The Ornaments of Gold", "az-zukhruf", "Meccan", 89),
    (44, "Ad-Dukhan", "The Smoke", "ad-dukhan", "Meccan", 59),
    (45, "Al-Jathiyah", "The Crouching", "al-jathiyah", "Meccan", 37),
    (46, "Al-Ahqaf", "The Wind-Curved Sandhills", "al-ahqaf", "Meccan", 35),
    (47, "Muhammad", "Muhammad", "muhammad", "Medinan", 38),
    (48, "Al-Fath", "The Victory", "al-fath", "Medinan", 29),
    (49, "Al-Hujurat", "The Rooms", "al-hujurat", "Medinan", 18),
    (50, "Qaf", "The Letter Qaf", "qaf", "Meccan", 45),
    (51, "Adh-Dhariyat", "The Winnowing Winds", "adh-dhariyat", "Meccan", 60),
    (52, "At-Tur", "The Mount", "at-tur", "Meccan", 49),
    (53, "An-Najm", "The Star", "an-najm", "Meccan", 62),
    (54, "Al-Qamar", "The Moon", "al-qamar", "Meccan", 55),
    (55, "Ar-Rahman", "The Beneficent", "ar-rahman", "Medinan", 78),
    (56, "Al-Waqi'ah", "The Inevitable", "al-waqiah", "Meccan", 96),
    (57, "Al-Hadid", "The Iron", "al-hadid", "Medinan", 29),
    (58, "Al-Mujadila", "The Pleading Woman", "al-mujadila", "Medinan", 22),
    (59, "Al-Hashr", "The Exile", "al-hashr", "Medinan", 24),
    (60, "Al-Mumtahanah", "She that is to be examined", "al-mumtahanah", "Medinan", 13),
    (61, "As-Saff", "The Ranks", "as-saff", "Medinan", 14),
    (62, "Al-Jumu'ah", "The Congregation", "al-jumuah", "Medinan", 11),
    (63, "Al-Munafiqun", "The Hypocrites", "al-munafiqun", "Medinan", 11),
    (64, "At-Taghabun", "The Mutual Disillusion", "at-taghabun", "Medinan", 18),
    (65, "At-Talaq", "The Divorce", "at-talaq", "Medinan", 12),
    (66, "At-Tahrim", "The Prohibition", "at-tahrim", "Medinan", 12),
    (67, "Al-Mulk", "The Sovereignty", "al-mulk", "Meccan", 30),
    (68, "Al-Qalam", "The Pen", "al-qalam", "Meccan", 52),
    (69, "Al-Haqqah", "The Reality", "al-haqqah", "Meccan", 52),
    (70, "Al-Ma'arij", "The Ascending Stairways", "al-maarij", "Meccan", 44),
    (71, "Nuh", "Noah", "nuh", "Meccan", 28),
    (72, "Al-Jinn", "The Jinn", "al-jinn", "Meccan", 28),
    (73, "Al-Muzzammil", "The Enshrouded One", "al-muzzammil", "Meccan", 20),
    (74, "Al-Muddaththir", "The Cloaked One", "al-muddaththir", "Meccan", 56),
    (75, "Al-Qiyamah", "The Resurrection", "al-qiyamah", "Meccan", 40),
    (76, "Al-Insan", "The Man", "al-insan", "Medinan", 31),
    (77, "Al-Mursalat", "The Emissaries", "al-mursalat", "Meccan", 50),
    (78, "An-Naba", "The Tidings", "an-naba", "Meccan", 40),
    (79, "An-Nazi'at", "Those who drag forth", "an-naziat", "Meccan", 46),
    (80, "'Abasa", "He Frowned", "abasa", "Meccan", 42),
    (81, "At-Takwir", "The Overthrowing", "at-takwir", "Meccan", 29),
    (82, "Al-Infitar", "The Cleaving", "al-infitar", "Meccan", 19),
    (83, "Al-Mutaffifin", "The Defrauding", "al-mutaffifin", "Meccan", 36),
    (84, "Al-Inshiqaq", "The Splitting Open", "al-inshiqaq", "Meccan", 25),
    (85, "Al-Buruj", "The Mansions of the Stars", "al-buruj", "Meccan", 22),
    (86, "At-Tariq", "The Nightcomer", "at-tariq", "Meccan", 17),
    (87, "Al-A'la", "The Most High", "al-ala", "Meccan", 19),
    (88, "Al-Ghashiyah", "The Overwhelming", "al-ghashiyah", "Meccan", 26),
    (89, "Al-Fajr", "The Dawn", "al-fajr", "Meccan", 30),
    (90, "Al-Balad", "The City", "al-balad", "Meccan", 20),
    (91, "Ash-Shams", "The Sun", "ash-shams", "Meccan", 15),
    (92, "Al-Layl", "The Night", "al-layl", "Meccan", 21),
    (93, "Ad-Duhaa", "The Morning Hours", "ad-duhaa", "Meccan", 11),
    (94, "Ash-Sharh", "The Relief", "ash-sharh", "Meccan", 8),
    (95, "At-Tin", "The Fig", "at-tin", "Meccan", 8),
    (96, "Al-'Alaq", "The Clot", "al-alaq", "Meccan", 19),
    (97, "Al-Qadr", "The Power", "al-qadr", "Meccan", 5),
    (98, "Al-Bayyinah", "The Clear Proof", "al-bayyinah", "Medinan", 8),
    (99, "Az-Zalzalah", "The Earthquake", "az-zalzalah", "Medinan", 8),
    (100, "Al-'Adiyat", "The Courser", "al-adiyat", "Meccan", 11),
    (101, "Al-Qari'ah", "The Calamity", "al-qariah", "Meccan", 11),
    (102, "At-Takathur", "The Rivalry in World Increase", "at-takathur", "Meccan", 8),
    (103, "Al-'Asr", "The Declining Day", "al-asr", "Meccan", 3),
    (104, "Al-Humazah", "The Traducer", "al-humazah", "Meccan", 9),
    (105, "Al-Fil", "The Elephant", "al-fil", "Meccan", 5),
    (106, "Quraysh", "Quraysh", "quraysh", "Meccan", 4),
    (107, "Al-Ma'un", "The Small Kindnesses", "al-maun", "Meccan", 7),
    (108, "Al-Kawthar", "The Abundance", "al-kawthar", "Meccan", 3),
    (109, "Al-Kafirun", "The Disbelievers", "al-kafirun", "Meccan", 6),
    (110, "An-Nasr", "The Divine Support", "an-nasr", "Medinan", 3),
    (111, "Al-Masad", "The Palm Fiber", "al-masad", "Meccan", 5),
    (112, "Al-Ikhlas", "The Sincerity", "al-ikhlas", "Meccan", 4),
    (113, "Al-Falaq", "The Daybreak", "al-falaq", "Meccan", 5),
    (114, "An-Nas", "Mankind", "an-nas", "Meccan", 6),
]

SURAH_BY_ID = {s[0]: s for s in SURAHS}

# Build normalization dictionary of surah aliases -> surah_id
SURAH_ALIASES: dict[str, int] = {}


def _clean_str(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


for surah_id, name, english_name, translit, _, _ in SURAHS:
    SURAH_ALIASES[str(surah_id)] = surah_id
    SURAH_ALIASES[_clean_str(name)] = surah_id
    SURAH_ALIASES[_clean_str(english_name)] = surah_id
    SURAH_ALIASES[_clean_str(translit)] = surah_id

    # Strip common article prefixes (al-, an-, ar-, as-, ash-, at-, az-, adh-)
    for prefix in ("al", "an", "ar", "as", "ash", "at", "az", "adh"):
        cleaned_prefix = _clean_str(prefix)
        c_name = _clean_str(name)
        if c_name.startswith(cleaned_prefix):
            stripped = c_name[len(cleaned_prefix):]
            if stripped:
                SURAH_ALIASES[stripped] = surah_id

    # Strip "the " from English names
    c_eng = _clean_str(english_name)
    if c_eng.startswith("the"):
        stripped_eng = c_eng[3:]
        if stripped_eng:
            SURAH_ALIASES[stripped_eng] = surah_id

# Common named verses
NAMED_VERSES: dict[str, tuple[int, int]] = {
    _clean_str("verse of the throne"): (2, 255),
    _clean_str("throne verse"): (2, 255),
    _clean_str("ayat al kursi"): (2, 255),
    _clean_str("ayatul kursi"): (2, 255),
    _clean_str("ayat al-kursi"): (2, 255),
    _clean_str("kursi"): (2, 255),
    _clean_str("light verse"): (24, 35),
    _clean_str("verse of light"): (24, 35),
    _clean_str("ayat an nur"): (24, 35),
}


def resolve_surah(s: str) -> Optional[int]:
    """Resolve a raw string to a canonical surah ID (1-114)."""
    cleaned = _clean_str(s)
    if cleaned in SURAH_ALIASES:
        return SURAH_ALIASES[cleaned]
    return None


# ---------------------------------------------------------------------------
# Reference parsing
# ---------------------------------------------------------------------------

def parse_quran_ref(raw: str) -> Optional[tuple[int, Union[int, tuple[int, int]]]]:
    """Parse a Quran reference into (surah_id, ayah | (ayah_start, ayah_end)).

    Supported formats:
        - "Quran 2:255"
        - "Surah 2:255"
        - "Al-Baqarah 2:255"
        - "Al-Baqarah 255"
        - "2:255"
        - "2:255-256" (ranges)
        - "Al-Baqarah 2:255-256"
        - "Ayat al-Kursi" (named verses)
    """
    if not raw or not isinstance(raw, str):
        return None

    clean = raw.strip()
    norm_named = _clean_str(clean)
    if norm_named in NAMED_VERSES:
        return NAMED_VERSES[norm_named]

    # Strip leading "quran", "surah", "surat"
    clean = re.sub(r"^(?:quran|surah|surat)\s+", "", clean, flags=re.IGNORECASE).strip()

    # Pattern 1: Name SurahNum:Ayah[-AyahEnd] (e.g. Al-Baqarah 2:255 or Al-Baqarah 2:255-256)
    m1 = re.match(r"^([A-Za-z0-9\'\- ]+?)\s+(\d+):(\d+)(?:[-–—](\d+))?$", clean)
    if m1:
        name, s_num, a1, a2 = m1.group(1).strip(), int(m1.group(2)), int(m1.group(3)), m1.group(4)
        surah_id = resolve_surah(name)
        if surah_id and surah_id == s_num and 1 <= surah_id <= 114:
            total_ayahs = SURAH_BY_ID[surah_id][5]
            if a2:
                start, end = a1, int(a2)
                if 1 <= start <= end <= total_ayahs:
                    return (surah_id, (start, end))
            elif 1 <= a1 <= total_ayahs:
                return (surah_id, a1)

    # Pattern 2: Num:Ayah[-AyahEnd] (e.g. 2:255 or 2:255-256)
    m2 = re.match(r"^(\d+):(\d+)(?:[-–—](\d+))?$", clean)
    if m2:
        s_num, a1, a2 = int(m2.group(1)), int(m2.group(2)), m2.group(3)
        if 1 <= s_num <= 114:
            total_ayahs = SURAH_BY_ID[s_num][5]
            if a2:
                start, end = a1, int(a2)
                if 1 <= start <= end <= total_ayahs:
                    return (s_num, (start, end))
            elif 1 <= a1 <= total_ayahs:
                return (s_num, a1)

    # Pattern 3: Name Ayah[-AyahEnd] or Name:Ayah (e.g. Al-Baqarah 255 or Al-Baqarah:255)
    m3 = re.match(r"^([A-Za-z\'\- ]+?)[:\s]+(\d+)(?:[-–—](\d+))?$", clean)
    if m3:
        name, a1, a2 = m3.group(1).strip(), int(m3.group(2)), m3.group(3)
        surah_id = resolve_surah(name)
        if surah_id and 1 <= surah_id <= 114:
            total_ayahs = SURAH_BY_ID[surah_id][5]
            if a2:
                start, end = a1, int(a2)
                if 1 <= start <= end <= total_ayahs:
                    return (surah_id, (start, end))
            elif 1 <= a1 <= total_ayahs:
                return (surah_id, a1)

    return None


# ---------------------------------------------------------------------------
# Data loading & retrieval
# ---------------------------------------------------------------------------

def list_quran_translations() -> list[str]:
    """List available Quran translation edition keys."""
    if not QURAN_DATA_DIR.exists():
        return []
    return sorted(p.stem for p in QURAN_DATA_DIR.glob("*.json"))


@lru_cache(maxsize=16)
def load_quran_edition(key: str) -> dict:
    """Load a Quran edition JSON into memory and cache it."""
    clean_key = key.strip().lower()
    path = QURAN_DATA_DIR / f"{clean_key}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Quran edition '{key}' not found at {path}. Available: {list_quran_translations()}"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_quran_verses(
    edition_key: str,
    surah_id: int,
    ayah_spec: Union[int, tuple[int, int]],
) -> list[dict]:
    """Retrieve ayahs for a given edition and surah."""
    edition_data = load_quran_edition(edition_key)
    divisions = edition_data.get("divisions", [])

    if not (1 <= surah_id <= len(divisions)):
        return []

    surah_obj = divisions[surah_id - 1]
    surah_name = surah_obj.get("name", f"Surah {surah_id}")
    surah_eng = surah_obj.get("name_english", "")
    all_ayahs = surah_obj.get("ayahs", [])

    if isinstance(ayah_spec, tuple):
        start_ayah, end_ayah = ayah_spec
    else:
        start_ayah, end_ayah = ayah_spec, ayah_spec

    results = []
    for item in all_ayahs:
        ayah_num = item["ayah"]
        if start_ayah <= ayah_num <= end_ayah:
            results.append({
                "surah": surah_id,
                "ayah": ayah_num,
                "text": item["text"],
                "surah_name": surah_name,
                "surah_english": surah_eng,
                "edition": edition_key,
                "translation": edition_data.get("translation", edition_key),
                "language": edition_data.get("language", "en"),
            })
    return results


# ---------------------------------------------------------------------------
# CLI presentation
# ---------------------------------------------------------------------------

def run_quran(
    ref_str: str,
    translations: Optional[list[str]] = None,
    as_json: bool = False,
) -> None:
    """Execute Quran lookup CLI command."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parsed = parse_quran_ref(ref_str)
    if not parsed:
        msg = f"Error: Could not parse Quran reference: {ref_str!r}"
        if as_json:
            print(json.dumps({"error": msg}))
        else:
            print(msg, file=sys.stderr)
            print("Examples of valid references: 'Al-Baqarah 2:255', '2:255', 'Quran 112:1-4', 'Ayat al-Kursi'")
        sys.exit(1)

    surah_id, ayah_spec = parsed
    surah_meta = SURAH_BY_ID[surah_id]
    s_name, s_eng = surah_meta[1], surah_meta[2]

    # Default to Arabic Uthmani + Saheeh International English per acceptance criteria
    if not translations:
        translations = ["uthmani", "saheeh-international"]

    available = list_quran_translations()
    active_editions = []
    for t in translations:
        t_clean = t.strip().lower()
        if t_clean in available:
            active_editions.append(t_clean)
        else:
            print(f"Warning: Edition '{t}' not found. Available: {available}", file=sys.stderr)

    if not active_editions:
        active_editions = ["saheeh-international"]

    # Gather rows
    # Structure: ayah_num -> {edition_key: text}
    ayah_map: dict[int, dict] = {}
    for ed in active_editions:
        verses = get_quran_verses(ed, surah_id, ayah_spec)
        for v in verses:
            a = v["ayah"]
            if a not in ayah_map:
                ayah_map[a] = {"surah": surah_id, "ayah": a, "texts": {}}
            ayah_map[a]["texts"][ed] = {
                "text": v["text"],
                "translation": v["translation"],
                "language": v["language"],
            }

    if as_json:
        output_json = {
            "query": ref_str,
            "surah": {
                "id": surah_id,
                "name": s_name,
                "name_english": s_eng,
                "transliteration": surah_meta[3],
                "revelation_period": surah_meta[4],
            },
            "ayahs": [
                {
                    "ayah": a_num,
                    "citation": f"Quran {surah_id}:{a_num} ({s_name})",
                    "translations": {
                        ed: ayah_map[a_num]["texts"][ed]["text"]
                        for ed in active_editions
                        if ed in ayah_map[a_num]["texts"]
                    },
                }
                for a_num in sorted(ayah_map.keys())
            ],
        }
        print(json.dumps(output_json, ensure_ascii=False, indent=2))
        return

    # Text presentation
    for a_num in sorted(ayah_map.keys()):
        citation = f"Quran {surah_id}:{a_num} ({s_name} / {s_eng})"
        print("=" * 78)
        print(f"  {citation}")
        print("=" * 78)

        for ed in active_editions:
            if ed in ayah_map[a_num]["texts"]:
                info = ayah_map[a_num]["texts"][ed]
                ed_name = info["translation"]
                text = info["text"]
                print(f"[{ed_name}]")
                print(f"{text}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Quran lookup and parallel translations CLI")
    parser.add_argument("reference", help="Quran citation (e.g. 'Al-Baqarah 2:255', '2:255', 'Ayat al-Kursi')")
    parser.add_argument("-t", "--translation", "--translations", dest="translations",
                        help="Comma-separated list of editions (default: uthmani,saheeh-international)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()
    editions = [t.strip() for t in args.translations.split(",")] if args.translations else None
    run_quran(args.reference, translations=editions, as_json=args.json)


if __name__ == "__main__":
    main()
