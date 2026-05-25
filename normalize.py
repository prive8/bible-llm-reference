#!/usr/bin/env python3
"""
Normalize Bolls flat-verse JSON to nested structure.
Usage: python3 normalize.py <input.json> <output.json> [book_name_map.json]
"""

import json
import sys

# Book number to name mapping (standard 66 + apocrypha + extras)
BOOK_NAMES = {
    1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers",
    5: "Deuteronomy", 6: "Joshua", 7: "Judges", 8: "Ruth",
    9: "1 Samuel", 10: "2 Samuel", 11: "1 Kings", 12: "2 Kings",
    13: "1 Chronicles", 14: "2 Chronicles", 15: "Ezra", 16: "Nehemiah",
    17: "Esther", 18: "Job", 19: "Psalms", 20: "Proverbs",
    21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
    24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel",
    28: "Hosea", 29: "Joel", 30: "Amos", 31: "Obadiah",
    32: "Jonah", 33: "Micah", 34: "Nahum", 35: "Habakkuk",
    36: "Zephaniah", 37: "Haggai", 38: "Zechariah", 39: "Malachi",
    # Apocrypha / Deuterocanonical
    40: "Tobit", 41: "Judith", 42: "Wisdom of Solomon",
    43: "Sirach", 44: "Baruch", 45: "1 Esdras", 46: "2 Esdras",
    47: "Prayer of Manasseh", 48: "1 Maccabees", 49: "2 Maccabees",
    50: "3 Maccabees", 51: "4 Maccabees", 52: "Psalm 151",
    53: "Prayer of Azariah", 54: "Susanna", 55: "Bel and the Dragon",
    56: "1 Esdras (Greek)", 57: "2 Esdras (Greek)",
    # New Testament
    58: "Matthew", 59: "Mark", 60: "Luke", 61: "John",
    62: "Acts", 63: "Romans", 64: "1 Corinthians", 65: "2 Corinthians",
    66: "Galatians", 67: "Ephesians", 68: "Philippians",
    69: "Colossians", 70: "1 Thessalonians", 71: "2 Thessalonians",
    72: "1 Timothy", 73: "2 Timothy", 74: "Titus", 75: "Philemon",
    76: "Hebrews", 77: "James", 78: "1 Peter", 79: "2 Peter",
    80: "1 John", 81: "2 John", 82: "3 John", 83: "Jude",
    84: "Revelation",
}

def normalize(input_path, output_path, translation_name, custom_book_names=None):
    with open(input_path) as f:
        data = json.load(f)

    # Already nested?
    if isinstance(data, dict) and 'books' in data:
        # Re-wrap with proper translation name
        data['translation'] = translation_name
        with open(output_path, 'w') as f:
            json.dump(data, f)
        print(f"  Already nested, just renamed: {output_path}")
        return

    # Flat list of verses
    verses = data

    books_data = {}
    for v in verses:
        b = v['book']
        if b not in books_data:
            books_data[b] = {}
        ch = v['chapter']
        if ch not in books_data[b]:
            books_data[b][ch] = []
        books_data[b][ch].append({'verse': v['verse'], 'text': v['text']})

    output = {
        'translation': translation_name,
        'books': []
    }

    for book_num in sorted(books_data.keys()):
        book_name = (custom_book_names or BOOK_NAMES).get(book_num, f"Book {book_num}")
        chapters_list = []
        for ch_num in sorted(books_data[book_num].keys()):
            chapters_list.append({
                'chapter': ch_num,
                'verses': books_data[book_num][ch_num]
            })
        output['books'].append({
            'name': book_name,
            'chapters': chapters_list
        })

    total = sum(len(ch['verses']) for book in output['books'] for ch in book['chapters'])
    print(f"  {len(output['books'])} books, {total} verses -> {output_path}")

    with open(output_path, 'w') as f:
        json.dump(output, f)

if __name__ == '__main__':
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    translation_name = sys.argv[3] if len(sys.argv) > 3 else "Unknown"
    normalize(input_path, output_path, translation_name)