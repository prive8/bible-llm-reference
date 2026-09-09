#!/usr/bin/env python3
"""Ingestion script for Phase 3.1: Quran translations and Arabic source text.

Downloads raw edition JSONs from fawazahmed0/quran-api (Unlicense) and transforms
them into the project canonical multi-tradition format (docs/data-schema.md §2):
  data/quran/{edition}.json

Stdlib-only (urllib.request, json).
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "quran"

# ---------------------------------------------------------------------------
# Canonical 114 Surahs Metadata (public domain, historical consensus)
# ---------------------------------------------------------------------------

SURAHS_METADATA = [
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

SURAH_BY_ID = {meta[0]: meta for meta in SURAHS_METADATA}

# ---------------------------------------------------------------------------
# Shortlist of Editions to Ingest
# ---------------------------------------------------------------------------

EDITIONS = [
    {
        "key": "saheeh-international",
        "api_name": "eng-ummmuhammad",
        "translation_name": "Saheeh International (1996)",
        "language": "en",
        "license": "Public Domain (tanzil.net)",
    },
    {
        "key": "yusuf-ali",
        "api_name": "eng-abdullahyusufal",
        "translation_name": "Abdullah Yusuf Ali (1934)",
        "language": "en",
        "license": "Public Domain (tanzil.net)",
    },
    {
        "key": "pickthall",
        "api_name": "eng-mohammedmarmadu",
        "translation_name": "Mohammed Marmaduke Pickthall (1930)",
        "language": "en",
        "license": "Public Domain (tanzil.net)",
    },
    {
        "key": "mufti-taqi-usmani",
        "api_name": "eng-muftitaqiusmani",
        "translation_name": "Mufti Taqi Usmani",
        "language": "en",
        "license": "Public Domain (tanzil.net)",
    },
    {
        "key": "arberry",
        "api_name": "eng-ajarberry",
        "translation_name": "A. J. Arberry (1955)",
        "language": "en",
        "license": "Public Domain (tanzil.net)",
    },
    {
        "key": "uthmani",
        "api_name": "ara-quranuthmanihaf",
        "translation_name": "Quran Uthmani Hafs (Arabic)",
        "language": "ar",
        "license": "King Fahad Quran Complex / Tanzil (Public Domain)",
    },
]


def fetch_edition_raw(api_name: str) -> list[dict]:
    """Fetch raw ayahs from CDN or fallback raw GitHub URL."""
    urls = [
        f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/{api_name}.min.json",
        f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/{api_name}.json",
        f"https://raw.githubusercontent.com/fawazahmed0/quran-api/1/editions/{api_name}.min.json",
    ]
    last_err = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BibleLLM-Ingest/0.5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "quran" in data:
                    return data["quran"]
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to fetch edition {api_name}: {last_err}")


def repack_to_schema(raw_ayahs: list[dict], meta_info: dict) -> dict:
    """Repack flat list of {chapter, verse, text} into canonical schema."""
    # Group ayahs by surah
    surah_buckets: dict[int, list[dict]] = {i: [] for i in range(1, 115)}
    for item in raw_ayahs:
        ch = item["chapter"]
        v = item["verse"]
        text = item["text"].strip()
        surah_buckets[ch].append({"ayah": v, "text": text})

    divisions = []
    for surah_id in range(1, 115):
        meta = SURAH_BY_ID[surah_id]
        divisions.append({
            "id": surah_id,
            "name": meta[1],
            "name_english": meta[2],
            "name_transliteration": meta[3],
            "revelation_period": meta[4],
            "ayahs": surah_buckets[surah_id],
        })

    return {
        "tradition": "islam",
        "translation": meta_info["translation_name"],
        "key": meta_info["key"],
        "language": meta_info["language"],
        "structure": "surah_ayah",
        "license": meta_info["license"],
        "source": "fawazahmed0/quran-api (tanzil.net)",
        "divisions": divisions,
    }


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ingesting Quran editions into {DATA_DIR}...")

    for edition in EDITIONS:
        key = edition["key"]
        target = DATA_DIR / f"{key}.json"
        print(f"  Fetching {key} ({edition['translation_name']})...")
        raw_ayahs = fetch_edition_raw(edition["api_name"])
        canonical = repack_to_schema(raw_ayahs, edition)

        total_ayahs = sum(len(d["ayahs"]) for d in canonical["divisions"])
        print(f"  Writing {target.name} ({len(canonical['divisions'])} surahs, {total_ayahs} ayahs)...")
        with open(target, "w", encoding="utf-8") as f:
            json.dump(canonical, f, ensure_ascii=False, indent=2)

    print("Quran ingestion complete.")


if __name__ == "__main__":
    main()
