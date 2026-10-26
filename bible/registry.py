"""Tradition Registry and Canonical Passage Model (Foundation F1-F3).

Provides a unified multi-tradition catalog, canonical passage IDs,
cross-tradition versification alignment, and unified passage lookup.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

ROOT = Path(__file__).resolve().parent.parent
EDITIONS_FILE = ROOT / "data" / "editions.json"
VERSIFICATION_FILE = ROOT / "data" / "versification_map.json"


@dataclass
class Passage:
    """Canonical representation of a scriptural passage."""
    tradition: str
    canonical_id: str
    citation: str
    text: str
    edition_id: str
    language: str = "en"
    translation_name: str = ""
    strongs_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tradition": self.tradition,
            "canonical_id": self.canonical_id,
            "citation": self.citation,
            "text": self.text,
            "edition_id": self.edition_id,
            "language": self.language,
            "translation_name": self.translation_name,
            "strongs_tags": self.strongs_tags,
        }


def _safe_int(value: Any) -> Optional[int]:
    """Parse an int, returning None instead of raising.

    A canonical id component is sometimes legitimately absent (a
    chapter-level reference has no verse), and a malformed id should
    degrade to "no verse" rather than crash the caller. The id
    "bible:Psalms.151.None" - produced by interpolating a missing verse
    into an id string - used to raise ValueError from int() and take
    down an entire evaluation run.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _unpack_tanakh(parsed: tuple) -> tuple[str, int, Optional[int], Optional[int]]:
    """Normalize a ``parse_tanakh_ref`` result to (book, chapter, start, end).

    ``parse_tanakh_ref`` returns a 3-tuple: ``(book, chapter, verse_spec)``
    where ``verse_spec`` is either a single verse number or a
    ``(start, end)`` tuple for a range. The registry code unpacked FOUR
    values from it, so the unpack raised ValueError on every call — and
    the surrounding ``except Exception: pass`` swallowed it, so the
    entire Tanakh branch was dead. **21% of the Tanakh corpus (4,924 of
    23,206 citations) could not be parsed at all.**

    Longest-match-first book resolution (see
    ``bible/lookup._match_longest_corpus_book``) is a separate fix; this
    one is about the tuple shape.
    """
    book, chapter, verse_spec = parsed[0], parsed[1], parsed[2]
    if isinstance(verse_spec, tuple):
        v_start, v_end = verse_spec[0], verse_spec[1]
    else:
        v_start, v_end = verse_spec, verse_spec
    return book, chapter, v_start, v_end


def make_canonical_id(tradition: str, unit: str | int, chapter: Optional[int] = None, verse: Optional[int] = None) -> str:
    """Construct deterministic canonical passage ID.
    Examples:
        bible:Genesis.1.1
        quran:2.255
        tanakh:Genesis.1.1

    A missing chapter or verse is OMITTED, never interpolated as the
    literal string "None". Interpolating it produced ids like
    "bible:Psalms.151.None", which later crashed
    ``parse_canonical_id`` on ``int("None")``. That is reachable from
    the corpus: the KJV contains a book literally named "Psalm 151",
    and a chapter-level reference to it has no verse.
    """
    trad_clean = tradition.lower().strip()

    def join(prefix: str, unit_str: str, ch: Optional[int], vs: Optional[int]) -> str:
        parts = [unit_str]
        if ch is not None:
            parts.append(str(ch))
            if vs is not None:
                parts.append(str(vs))
        return f"{prefix}:{'.'.join(parts)}"

    if trad_clean in ("bible", "christianity"):
        return join("bible", str(unit).replace(" ", "_"), chapter, verse)
    elif trad_clean in ("quran", "islam"):
        # Quran ids are surah.ayah - there is no separate chapter.
        return join("quran", str(unit), chapter if verse is None else verse, None)
    elif trad_clean in ("tanakh", "torah", "judaism"):
        return join("tanakh", str(unit).replace(" ", "_"), chapter, verse)
    else:
        return join(trad_clean, str(unit).replace(" ", "_"), chapter, verse)


def parse_canonical_id(canonical_id: str) -> dict[str, Any]:
    """Parse a canonical passage ID into its components."""
    if ":" not in canonical_id:
        raise ValueError(f"Invalid canonical ID format (missing ':'): {canonical_id}")
    prefix, location = canonical_id.split(":", 1)
    parts = location.split(".")
    
    if prefix in ("bible", "tanakh"):
        book = parts[0].replace("_", " ")
        chapter = _safe_int(parts[1]) if len(parts) > 1 else None
        verse = _safe_int(parts[2]) if len(parts) > 2 else None
        return {
            "tradition": "christianity" if prefix == "bible" else "judaism",
            "prefix": prefix,
            "book": book,
            "chapter": chapter,
            "verse": verse,
        }
    elif prefix == "quran":
        surah = _safe_int(parts[0])
        ayah = _safe_int(parts[1]) if len(parts) > 1 else None
        return {
            "tradition": "islam",
            "prefix": prefix,
            "surah": surah,
            "ayah": ayah,
        }
    else:
        return {
            "tradition": prefix,
            "prefix": prefix,
            "parts": parts,
        }


class TraditionRegistry:
    """Central registry for multi-tradition scripture editions and passages."""

    def __init__(self, editions_path: Optional[Path] = None, versification_path: Optional[Path] = None):
        self.editions_path = editions_path or EDITIONS_FILE
        self.versification_path = versification_path or VERSIFICATION_FILE
        self._editions: dict[str, dict[str, Any]] = {}
        self._book_mappings: dict[str, str] = {}
        self._alignments: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.editions_path.exists():
            with open(self.editions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for ed in data.get("editions", []):
                    self._editions[ed["id"]] = ed

        if self.versification_path.exists():
            with open(self.versification_path, "r", encoding="utf-8") as f:
                vdata = json.load(f)
                self._book_mappings = vdata.get("book_name_mappings", {})
                self._alignments = vdata.get("alignments", [])

    def get_edition(self, edition_id: str) -> Optional[dict[str, Any]]:
        return self._editions.get(edition_id)

    def list_editions(self, tradition: Optional[str] = None, redistributable_only: bool = False) -> list[dict[str, Any]]:
        eds = list(self._editions.values())
        if tradition:
            trad_clean = tradition.lower().strip()
            if trad_clean == "bible":
                trad_clean = "christianity"
            elif trad_clean == "quran":
                trad_clean = "islam"
            elif trad_clean in ("tanakh", "torah"):
                trad_clean = "judaism"
            eds = [e for e in eds if e["tradition"].lower() == trad_clean]
        if redistributable_only:
            eds = [e for e in eds if e.get("redistributable", False)]
        return eds

    def align_canonical_id(self, canonical_id: str, target_tradition: str) -> Optional[str]:
        """Map canonical ID between Christian Bible and Jewish Tanakh traditions."""
        parsed = parse_canonical_id(canonical_id)
        src_prefix = parsed["prefix"]
        target_prefix = "tanakh" if target_tradition in ("judaism", "tanakh", "torah") else "bible"

        if src_prefix == target_prefix:
            return canonical_id

        if src_prefix not in ("bible", "tanakh") or target_prefix not in ("bible", "tanakh"):
            return None

        book = parsed["book"]
        chapter = parsed["chapter"]
        verse = parsed["verse"]

        # 1. Map book name if aliased
        target_book = self._book_mappings.get(book, book)

        # 2. Check chapter/verse alignment table
        if chapter is not None and verse is not None:
            for align in self._alignments:
                if src_prefix == "bible":
                    c = align.get("christian", {})
                    h = align.get("hebrew", {})
                    if c.get("book") == book and c.get("chapter") == chapter:
                        if c.get("verse_start") <= verse <= c.get("verse_end"):
                            offset = verse - c.get("verse_start")
                            target_ch = h.get("chapter")
                            target_v = h.get("verse_start") + offset
                            return f"{target_prefix}:{target_book.replace(' ', '_')}.{target_ch}.{target_v}"
                elif src_prefix == "tanakh":
                    c = align.get("christian", {})
                    h = align.get("hebrew", {})
                    if h.get("book") == book and h.get("chapter") == chapter:
                        if h.get("verse_start") <= verse <= h.get("verse_end"):
                            offset = verse - h.get("verse_start")
                            target_ch = c.get("chapter")
                            target_v = c.get("verse_start") + offset
                            return f"{target_prefix}:{target_book.replace(' ', '_')}.{target_ch}.{target_v}"

        if chapter is not None and verse is not None:
            return f"{target_prefix}:{target_book.replace(' ', '_')}.{chapter}.{verse}"
        elif chapter is not None:
            return f"{target_prefix}:{target_book.replace(' ', '_')}.{chapter}"
        return f"{target_prefix}:{target_book.replace(' ', '_')}"

    def parse_reference(self, reference: str, preferred_tradition: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Attempt to parse a reference string across registered traditions."""
        ref = reference.strip()

        # 1. Check if reference is already a canonical ID
        if ":" in ref and any(ref.startswith(f"{p}:") for p in ("bible", "quran", "tanakh")):
            parsed = parse_canonical_id(ref)
            return {
                "canonical_id": ref,
                "tradition": parsed["tradition"],
                "citation": ref,
                "parsed": parsed,
            }

        # 2. Check Quran
        try:
            from bible.quran import parse_quran_ref
            q_parsed = parse_quran_ref(ref)
            if q_parsed:
                s_id, a_spec = q_parsed
                if isinstance(a_spec, tuple):
                    v_start, v_end = a_spec
                else:
                    v_start, v_end = a_spec, a_spec
                can_id = make_canonical_id("islam", s_id, v_start)
                return {
                    "canonical_id": can_id,
                    "tradition": "islam",
                    "citation": f"Quran {s_id}:{v_start}" if v_start == v_end else f"Quran {s_id}:{v_start}-{v_end}",
                    "surah": s_id,
                    "ayah_start": v_start,
                    "ayah_end": v_end,
                }
        except Exception:
            pass

        # 3. Check Tanakh
        if preferred_tradition in ("judaism", "tanakh", "torah"):
            try:
                from bible.tanakh import parse_tanakh_ref
                t_parsed = parse_tanakh_ref(ref)
                if t_parsed:
                    b_name, ch, v_start, v_end = _unpack_tanakh(t_parsed)
                    can_id = make_canonical_id("judaism", b_name, ch, v_start)
                    return {
                        "canonical_id": can_id,
                        "tradition": "judaism",
                        "citation": f"{b_name} {ch}:{v_start}" if v_start == v_end else f"{b_name} {ch}:{v_start}-{v_end}",
                        "book": b_name,
                        "chapter": ch,
                        "verse_start": v_start,
                        "verse_end": v_end,
                    }
            except Exception:
                pass

        # 4. Check Christian Bible
        try:
            from bible.lookup import parse_ref
            b_parsed = parse_ref(ref)
            if b_parsed:
                b_name, ch, v_start, v_end = b_parsed
                can_id = make_canonical_id("christianity", b_name, ch, v_start)
                return {
                    "canonical_id": can_id,
                    "tradition": "christianity",
                    "citation": f"{b_name} {ch}:{v_start}" if v_start == v_end else f"{b_name} {ch}:{v_start}-{v_end}",
                    "book": b_name,
                    "chapter": ch,
                    "verse_start": v_start,
                    "verse_end": v_end,
                }
        except Exception:
            pass

        # 5. Fallback Tanakh check if not already preferred
        try:
            from bible.tanakh import parse_tanakh_ref
            t_parsed = parse_tanakh_ref(ref)
            if t_parsed:
                b_name, ch, v_start, v_end = _unpack_tanakh(t_parsed)
                can_id = make_canonical_id("judaism", b_name, ch, v_start)
                return {
                    "canonical_id": can_id,
                    "tradition": "judaism",
                    "citation": f"{b_name} {ch}:{v_start}" if v_start == v_end else f"{b_name} {ch}:{v_start}-{v_end}",
                    "book": b_name,
                    "chapter": ch,
                    "verse_start": v_start,
                    "verse_end": v_end,
                }
        except Exception:
            pass

        return None

    def get_passages(
        self,
        reference: str,
        traditions: Optional[list[str]] = None,
        editions: Optional[list[str]] = None,
    ) -> list[Passage]:
        """Lookup passage across traditions and editions.
        If traditions is 'all' or contains multiple traditions, aligns the reference
        and gathers parallel verses across Christian Bible, Tanakh, etc.
        """
        parsed = self.parse_reference(reference)
        if not parsed:
            return []

        results: list[Passage] = []
        target_traditions = [t.lower() for t in traditions] if traditions else [parsed["tradition"]]
        if "all" in target_traditions:
            target_traditions = ["christianity", "islam", "judaism"]

        # Christian Bible passages
        if "christianity" in target_traditions or "bible" in target_traditions:
            bible_ref = reference
            if parsed["tradition"] == "judaism":
                aligned_id = self.align_canonical_id(parsed["canonical_id"], "christianity")
                if aligned_id:
                    p = parse_canonical_id(aligned_id)
                    bible_ref = f"{p['book']} {p['chapter']}:{p['verse']}"

            try:
                from bible.lookup import parse_ref, get_kjv_verses, get_verses, list_translations, strip_strongs_tags

                b_info = parse_ref(bible_ref)
                if b_info:
                    book_name, ch_num, v_start, v_end = b_info
                    ve = v_end or v_start
                    avail_eds = editions or (["KJV"] + list_translations())
                    for ed in avail_eds:
                        ed_clean = ed.strip()
                        if ed_clean.upper() == "KJV":
                            rows = get_kjv_verses(book_name, ch_num, v_start, ve)
                            for r in rows:
                                can_id = make_canonical_id("christianity", book_name, ch_num, r["verse"])
                                results.append(Passage(
                                    tradition="christianity",
                                    canonical_id=can_id,
                                    citation=f"{book_name} {ch_num}:{r['verse']}",
                                    text=strip_strongs_tags(r["text"]),
                                    edition_id="kjv",
                                    translation_name="KJV",
                                    language="en",
                                ))
                        else:
                            rows = get_verses(ed_clean, book_name, ch_num, v_start, ve)
                            for r in rows:
                                can_id = make_canonical_id("christianity", book_name, ch_num, r["verse"])
                                results.append(Passage(
                                    tradition="christianity",
                                    canonical_id=can_id,
                                    citation=f"{book_name} {ch_num}:{r['verse']}",
                                    text=r["text"],
                                    edition_id=ed_clean.lower(),
                                    translation_name=ed_clean,
                                    language="en",
                                ))
            except Exception:
                pass

        # Judaism passages (Tanakh)
        if "judaism" in target_traditions or "tanakh" in target_traditions:
            tanakh_ref = reference
            if parsed["tradition"] == "christianity":
                aligned_id = self.align_canonical_id(parsed["canonical_id"], "judaism")
                if aligned_id:
                    p = parse_canonical_id(aligned_id)
                    tanakh_ref = f"{p['book']} {p['chapter']}:{p['verse']}"

            try:
                from bible.tanakh import parse_tanakh_ref, get_tanakh_verses_scoped, list_tanakh_translations
                t_info = parse_tanakh_ref(tanakh_ref)
                if t_info:
                    b_name, ch_num, v_spec = t_info
                    avail_eds = editions or list_tanakh_translations()
                    for ed_key in avail_eds:
                        try:
                            v_rows = get_tanakh_verses_scoped(ed_key, b_name, ch_num, v_spec)
                            for vr in v_rows:
                                can_id = make_canonical_id("judaism", b_name, ch_num, vr["verse"])
                                results.append(Passage(
                                    tradition="judaism",
                                    canonical_id=can_id,
                                    citation=f"{b_name} {ch_num}:{vr['verse']}",
                                    text=vr["text"],
                                    edition_id=f"tanakh-{ed_key}",
                                    translation_name=ed_key,
                                    language="he" if "hebrew" in ed_key else "en",
                                ))
                        except Exception:
                            continue
            except Exception:
                pass

        # Islam passages (Quran)
        if "islam" in target_traditions or "quran" in target_traditions:
            if parsed["tradition"] == "islam":
                try:
                    from bible.quran import parse_quran_ref, get_quran_verses, list_quran_translations
                    avail_eds = editions or ["uthmani", "saheeh-international", "pickthall"]
                    q_info = parse_quran_ref(parsed["citation"])
                    if q_info:
                        s_id, a_spec = q_info
                        for ed_key in avail_eds:
                            try:
                                v_rows = get_quran_verses(ed_key, s_id, a_spec)
                                for vr in v_rows:
                                    can_id = make_canonical_id("islam", s_id, vr["ayah"])
                                    results.append(Passage(
                                        tradition="islam",
                                        canonical_id=can_id,
                                        citation=f"Quran {s_id}:{vr['ayah']}",
                                        text=vr["text"],
                                        edition_id=f"quran-{ed_key}",
                                        translation_name=ed_key,
                                        language="ar" if "uthmani" in ed_key else "en",
                                    ))
                            except Exception:
                                continue
                except Exception:
                    pass

        return results


# Module-level default registry singleton
_default_registry: Optional[TraditionRegistry] = None


def get_registry() -> TraditionRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = TraditionRegistry()
    return _default_registry
