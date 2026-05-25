#!/usr/bin/env python3
"""
Bible LLM Reference Tool
Ask questions about the Bible and get answers with verse citations.
Loads full KJV as context, searches relevant passages, queries LLM.
"""

import json
import re
import sys
import os
from datetime import datetime

# Load Bible corpus once
BIBLE_PATH = os.path.join(os.path.dirname(__file__), 'kjv.json')
print(f"Loading Bible corpus...", flush=True)
with open(BIBLE_PATH) as f:
    BIBLE = json.load(f)
print(f"Loaded {len(BIBLE['books'])} books", flush=True)

def search_bible(query, max_verses=50):
    """Search all verses for keyword matches. Returns list of (book, chapter, verse, text)."""
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    results = []
    
    for book in BIBLE['books']:
        for chapter in book['chapters']:
            ch_num = chapter['chapter']
            for verse in chapter['verses']:
                text_lower = verse['text'].lower()
                # Score by how many query words appear
                score = sum(1 for w in query_words if w in text_lower)
                if score > 0:
                    results.append({
                        'book': book['name'],
                        'chapter': ch_num,
                        'verse': verse['verse'],
                        'text': verse['text'],
                        'score': score
                    })
    
    # Sort by score descending, then by text length (shorter = more specific match)
    results.sort(key=lambda x: (x['score'], len(x['text'])), reverse=True)
    return results[:max_verses]

def format_citation(r):
    """Format a verse as a citation string."""
    return f"{r['book']} {r['chapter']}:{r['verse']}"

def build_context(verses):
    """Build a context string from a list of verses."""
    lines = []
    for v in verses:
        lines.append(f"[{format_citation(v)}] {v['text']}")
    return '\n'.join(lines)

def format_results(verses, query):
    """Format search results as readable output."""
    world_news = [v for v in verses if v['score'] >= 2]
    others = [v for v in verses if v['score'] == 1]
    
    output = []
    output.append(f"\n{'='*60}")
    output.append(f"BIBLE REFERENCE: {query}")
    output.append(f"{'='*60}\n")
    
    if world_news:
        output.append(f"PRIMARY MATCHES ({len(world_news)} verses):")
        for v in world_news[:20]:
            output.append(f"  [{format_citation(v)}] {v['text']}")
        output.append("")
    
    if others:
        output.append(f"RELATED VERSES ({len(others)} verses):")
        for v in others[:30]:
            output.append(f"  [{format_citation(v)}] {v['text']}")
    
    return '\n'.join(output)

def main():
    if len(sys.argv) < 2:
        print("Usage: python bible-query.py 'your question about the Bible'")
        print("Example: python bible-query.py 'What does the Bible say about Christ as a human?'")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    print(f"\nSearching: {query}", flush=True)
    
    verses = search_bible(query, max_verses=80)
    print(f"Found {len(verses)} relevant verses", flush=True)
    
    if not verses:
        print("No matches found. Try different keywords.")
        sys.exit(1)
    
    # Print formatted results
    output = format_results(verses, query)
    print(output)
    
    # Build context for LLM
    context = build_context(verses[:30])
    
    print(f"\n{'='*60}")
    print("CONTEXT FOR LLM (paste to Gemini/OpenAI):")
    print(f"{'='*60}")
    print(f"\nQuery: {query}")
    print(f"\nRelevant Bible passages:\n{context}")
    print(f"\n{'='*60}")
    print("\nNOTE: To get AI analysis, copy the context above and ask a question.")

if __name__ == '__main__':
    main()