#!/usr/bin/env python3
"""Produce a flat JSONL ready for LLM training / embedding."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
with open(ROOT / "kjv.json") as f:
    bible = json.load(f)

out = ROOT / "kjv_training.jsonl"
with open(out, "w", encoding="utf-8") as f:
    for book in bible["books"]:
        for ch in book["chapters"]:
            for v in ch["verses"]:
                rec = {
                    "id": f"{book['name']}.{ch['chapter']}.{v['verse']}",
                    "book": book["name"],
                    "chapter": ch["chapter"],
                    "verse": v["verse"],
                    "text": v["text"],
                    "translation": "KJV",
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"Wrote {out}")