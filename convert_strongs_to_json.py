#!/usr/bin/env python3
"""Convert the Open Scriptures .js Strong's files → clean JSON."""
import json, re
from pathlib import Path

def convert(js_path: Path, out_path: Path):
    text = js_path.read_text(encoding="utf-8")
    text = re.sub(r"^var\s+\w+\s*=\s*", "", text.strip())
    text = re.sub(r";\s*$", "", text)
    data = json.loads(text)  # usually works; fallback regex if needed
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=None), encoding="utf-8")
    print(f"Wrote {len(data)} entries → {out_path}")

ROOT = Path(__file__).parent
convert(ROOT / "strongs_data/hebrew/strongs-hebrew-dictionary.js",
        ROOT / "strongs_data/hebrew/strongs-hebrew.json")
convert(ROOT / "strongs_data/greek/strongs-greek-dictionary.js",
        ROOT / "strongs_data/greek/strongs-greek.json")