"""Okapi BM25 search engine for the bible package.

Stdlib-only (ADR-001 compliant). Provides fast, ranked keyword retrieval
across the canonical KJV and any translation in the corpus.

Features:
- Okapi BM25 scoring (k1=1.5, b=0.75) with Lucene-style non-negative IDF.
- Multilingual and Unicode-aware tokenization (Latin, Greek, Hebrew, Cyrillic,
  Arabic, CJK characters, etc.) with diacritic-insensitive normalization.
- Phrase match and all-terms-matched relevance boosts.
- Translation-pluggable (defaults to KJV, can search WEB, YLT, etc.).
- CLI interface: `python -m bible search "query" [--translation T] [--limit N] [--strongs] [--json]`
"""

from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Any, Optional

from bible.lookup import (
    extract_strongs_nums,
    list_translations,
    load_kjv,
    load_translation_books,
    lookup_strongs,
    strip_strongs_tags,
)

def format_strongs_summary(nums: list[str]) -> str:
    """Format a list of Strong's numbers into a concise summary line."""
    if not nums:
        return ""
    entries = []
    for n in nums[:6]:
        entry = lookup_strongs(n)
        if entry:
            lemma = entry.get("lemma") or entry.get("xlit") or entry.get("translit") or ""
            gloss = (entry.get("strongs_def") or entry.get("kjv_def") or "")[:35]
            entries.append(f"{n} ({lemma}: {gloss})")
        else:
            entries.append(n)
    if len(nums) > 6:
        entries.append(f"... (+{len(nums) - 6} more)")
    return ", ".join(entries)

# ---------------------------------------------------------------------------
# Multilingual tokenization & normalization
# ---------------------------------------------------------------------------

def normalize_unicode(text: str) -> str:
    """Normalize text and strip combining diacritics (niqqud, accents, etc.).

    This allows queries without diacritics to match pointed Hebrew or
    polytonic Greek, while keeping base characters intact.
    """
    nfd = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in nfd if unicodedata.combining(c) == 0)
    return unicodedata.normalize("NFC", stripped).lower()


def tokenize(text: str) -> list[str]:
    """Tokenize verse text into searchable terms.

    Strips Strong's tags and punctuation, handles Unicode letters and numbers,
    and indexes individual CJK characters for non-segmented scripts.
    """
    clean = strip_strongs_tags(text)
    norm = normalize_unicode(clean)

    tokens: list[str] = []
    # Match individual CJK characters OR Unicode word sequences
    for m in re.finditer(r"[\u4e00-\u9fff]|[\w']+", norm, re.UNICODE):
        tok = m.group(0).strip("'")
        # Keep word tokens longer than 1 char, or single CJK characters
        if tok and (len(tok) > 1 or "\u4e00" <= tok <= "\u9fff"):
            tokens.append(tok)
    return tokens


# ---------------------------------------------------------------------------
# Document representation & BM25 Index
# ---------------------------------------------------------------------------

class VerseDoc:
    __slots__ = (
        "idx", "book", "chapter", "verse", "reference",
        "raw_text", "text", "tokens", "token_counts", "length"
    )

    def __init__(
        self,
        idx: int,
        book: str,
        chapter: int,
        verse: int,
        raw_text: str,
    ):
        self.idx = idx
        self.book = book
        self.chapter = chapter
        self.verse = verse
        self.reference = f"{book} {chapter}:{verse}"
        self.raw_text = raw_text
        self.text = strip_strongs_tags(raw_text)
        self.tokens = tokenize(raw_text)
        self.token_counts = Counter(self.tokens)
        self.length = len(self.tokens)


class BM25Index:
    """In-memory Okapi BM25 index over a single Bible translation."""

    def __init__(self, translation_name: str, docs: list[VerseDoc], k1: float = 1.5, b: float = 0.75):
        self.translation_name = translation_name
        self.docs = docs
        self.k1 = k1
        self.b = b
        self.N = len(docs)
        self.avgdl = sum(d.length for d in docs) / max(self.N, 1)

        # Inverted index: term -> list of (doc_idx, term_frequency)
        self.inverted_index: dict[str, list[tuple[int, int]]] = defaultdict(list)
        # Document frequency: term -> number of docs containing term
        self.df: dict[str, int] = defaultdict(int)

        for doc in self.docs:
            for term, count in doc.token_counts.items():
                self.inverted_index[term].append((doc.idx, count))
                self.df[term] += 1

        # Precompute IDF for terms in vocabulary
        self.idf: dict[str, float] = {}
        for term, df_val in self.df.items():
            # Lucene-style BM25 IDF: ln((N - df + 0.5) / (df + 0.5) + 1.0)
            self.idf[term] = math.log((self.N - df_val + 0.5) / (df_val + 0.5) + 1.0)

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search the corpus for query terms and return top ranked verses."""
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        q_terms = list(set(q_tokens))
        scores: dict[int, float] = defaultdict(float)
        matched_terms: dict[int, set[str]] = defaultdict(set)

        for term in q_terms:
            idf = self.idf.get(term, 0.0)
            if idf <= 0.0:
                continue

            postings = self.inverted_index.get(term, [])
            for doc_idx, tf in postings:
                doc = self.docs[doc_idx]
                # Okapi BM25 formula
                num = tf * (self.k1 + 1.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc.length / self.avgdl))
                scores[doc_idx] += idf * (num / denom)
                matched_terms[doc_idx].add(term)

        if not scores:
            return []

        # Exact phrase and coverage boosts
        norm_query_str = " ".join(q_tokens)
        phrase_search = len(q_tokens) > 1

        results = []
        for doc_idx, raw_score in scores.items():
            doc = self.docs[doc_idx]
            final_score = raw_score

            # Coverage boost: all terms present
            if len(matched_terms[doc_idx]) == len(q_terms) and len(q_terms) > 1:
                final_score *= 1.2

            # Exact phrase boost: consecutive terms appear in order in doc
            if phrase_search:
                doc_norm_str = " ".join(doc.tokens)
                if norm_query_str in doc_norm_str:
                    final_score += (raw_score * 0.5) + (2.0 * len(q_tokens))

            results.append({
                "book": doc.book,
                "chapter": doc.chapter,
                "verse": doc.verse,
                "reference": doc.reference,
                "text": doc.text,
                "raw_text": doc.raw_text,
                "score": round(final_score, 4),
                "translation": self.translation_name,
            })

        # Sort primarily by score descending, secondarily by shorter verse text
        results.sort(key=lambda r: (-r["score"], len(r["text"])))
        return results[:limit]


# ---------------------------------------------------------------------------
# Index builders & cache
# ---------------------------------------------------------------------------

@lru_cache(maxsize=16)
def get_bm25_index(translation: str = "KJV") -> BM25Index:
    """Build or retrieve a cached BM25 index for the specified translation."""
    norm_name = translation.strip().upper()
    docs: list[VerseDoc] = []
    idx = 0

    if norm_name == "KJV":
        kjv = load_kjv()
        for book in kjv["books"]:
            bname = book["name"]
            for ch in book["chapters"]:
                cnum = ch["chapter"]
                for v in ch["verses"]:
                    docs.append(VerseDoc(idx, bname, cnum, v["verse"], v["text"]))
                    idx += 1
        return BM25Index("KJV", docs)

    # Other translations from translations/*.json
    # Find matching translation file stem (case-insensitive)
    avail = list_translations()
    matched_stem = next((stem for stem in avail if stem.upper() == norm_name), None)
    if not matched_stem:
        raise ValueError(
            f"Translation '{translation}' not found. Available: {['KJV'] + avail}"
        )

    book_map = load_translation_books(matched_stem)
    for bname, book in book_map.items():
        for ch in book.get("chapters", []):
            cnum = ch["chapter"]
            for v in ch.get("verses", []):
                docs.append(VerseDoc(idx, bname, cnum, v["verse"], v["text"]))
                idx += 1

    return BM25Index(matched_stem, docs)


# ---------------------------------------------------------------------------
# High-level runner & CLI formatting
# ---------------------------------------------------------------------------

def run_search(
    query: str,
    translation: str = "KJV",
    limit: int = 10,
    as_json: bool = False,
    with_strongs: bool = False,
) -> list[dict[str, Any]]:
    """Execute a BM25 search and print or return results."""
    idx = get_bm25_index(translation)
    results = idx.search(query, limit=limit)

    if with_strongs:
        for r in results:
            nums = extract_strongs_nums(r["raw_text"], book=r["book"])
            r["strongs"] = nums

    if as_json:
        # Strip internal raw_text field before serialization
        clean_results = [
            {k: v for k, v in r.items() if k != "raw_text"}
            for r in results
        ]
        print(json.dumps(clean_results, indent=2, ensure_ascii=False))
        return results

    # Text presentation
    if not results:
        print(f"No results found for {query!r} in {translation}.")
        return []

    print(f"\nSearch results for {query!r} ({translation}, top {len(results)}):\n")
    for i, r in enumerate(results, 1):
        print(f"{i:2d}. [{r['reference']}] ({translation}, score: {r['score']:.2f})")
        print(f"    {r['text']}")
        if with_strongs and r.get("strongs"):
            summary = format_strongs_summary(r["strongs"])
            if summary:
                print(f"    Strong's: {summary}")
        print()

    return results


def main():
    """CLI entry point for `python -m bible search`."""
    import argparse

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        prog="bible search",
        description="Search Bible text using Okapi BM25 ranking.",
    )
    parser.add_argument("query", help="Query string or phrase (e.g. 'faith without works')")
    parser.add_argument(
        "-t", "--translation",
        default="KJV",
        help="Translation to search (default: KJV; e.g. WEB, YLT, RSV)",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=10,
        help="Maximum results to return (default: 10)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON",
    )
    parser.add_argument(
        "-s", "--strongs",
        action="store_true",
        help="Include Strong's concordance tags if available",
    )

    args = parser.parse_args()
    run_search(
        args.query,
        translation=args.translation,
        limit=args.limit,
        as_json=args.json,
        with_strongs=args.strongs,
    )


if __name__ == "__main__":
    main()
