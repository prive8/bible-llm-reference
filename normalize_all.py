#!/usr/bin/env python3
"""
Normalize all Bible translations from Bolls flat JSON to nested structure with proper book names.
Uses positional + fingerprint matching (vcount, ccount, opening text) for high accuracy.
"""

import json, os

TRANSLATIONS = {
    'kjv': {'code': 'KJV', 'name': 'King James Version (1769) with Strong\'s Numbers'},
    'ylt': {'code': 'YLT', 'name': 'Young\'s Literal Translation (1898)'},
    'web': {'code': 'WEB', 'name': 'World English Bible'},
    'gnv': {'code': 'GNV', 'name': 'Geneva Bible (1599)'},
    'drb': {'code': 'DRB', 'name': 'Douay-Rheims Bible (1609/1610)'},
    'rsv': {'code': 'RSV', 'name': 'Revised Standard Version (1952)'},
    'lut': {'code': 'LUT', 'name': 'Luther Bibel (1912)'},
    'synod': {'code': 'SYNOD', 'name': 'Russian Synodal Translation (1876)'},
    'rv1960': {'code': 'RV1960', 'name': 'Reina-Valera 1960 (Spanish)'},
    'cuv': {'code': 'CUV', 'name': 'Chinese Union Version'},
    'ukrk': {'code': 'UKRK', 'name': 'Ukrainian Bible (Kulykh, 1903)'},
    'tisch': {'code': 'TISCH', 'name': 'Tischendorf Greek NT (8th ed., 1869-72) with Strong\'s'},
    'lxx': {'code': 'LXX', 'name': 'Septuagint (Greek)'},
    'wlca': {'code': 'WLCa', 'name': 'Westminster Leningrad Codex (Hebrew, with Strong\'s)'},
}

# Canonical 66-book fingerprints: (vcount, ccount, ch1_v1_start_15chars)
CANONICAL_FP = [
    (1, "Genesis", 1533, 50, "In the beginning"),
    (2, "Exodus", 1213, 40, "And these [are] the names"),
    (3, "Leviticus", 859, 27, "And Jehovah calleth"),
    (4, "Numbers", 1288, 36, "And Jehovah speaketh"),
    (5, "Deuteronomy", 959, 34, "These [are] the words"),
    (6, "Joshua", 658, 24, "And it cometh to pass after"),
    (7, "Judges", 618, 21, "And it cometh to pass after the death"),
    (8, "Ruth", 85, 4, "And it cometh to pass, in the days"),
    (9, "1 Samuel", 810, 31, "And there is a certain man"),
    (10, "2 Samuel", 695, 24, "And it cometh to pass, after the death"),
    (11, "1 Kings", 816, 22, "And king David [is] old"),
    (12, "2 Kings", 719, 25, "And Moab transgresseth"),
    (13, "1 Chronicles", 942, 29, "Adam, Sheth, Enosh"),
    (14, "2 Chronicles", 822, 36, "And strengthen himself"),
    (15, "Ezra", 280, 10, "And in the first year of Cyrus"),
    (16, "Nehemiah", 406, 13, "Words of Nehemiah"),
    (17, "Esther", 167, 10, "And it cometh to pass, in the days"),
    (18, "Job", 1070, 42, "A man there hath been"),
    (19, "Psalms", 2461, 150, "O the happiness"),
    (20, "Proverbs", 915, 31, "Proverbs of Solomon"),
    (21, "Ecclesiastes", 222, 12, "Words of a preacher"),
    (22, "Song of Solomon", 117, 8, "The Song of Songs"),
    (23, "Isaiah", 1292, 66, "The Visions of Isaiah"),
    (24, "Jeremiah", 1364, 52, "Words of Jeremiah"),
    (25, "Lamentations", 154, 5, "How hath she sat alone"),
    (26, "Ezekiel", 1273, 48, "And it cometh to pass in the thirtieth"),
    (27, "Daniel", 357, 12, "In the third year of the reign"),
    (28, "Hosea", 197, 14, "A word of Jehovah"),
    (29, "Joel", 73, 3, "A word of Jehovah"),
    (30, "Amos", 146, 9, "Words of Amos"),
    (31, "Obadiah", 21, 1, "Thus said the Lord Jehovah"),
    (32, "Jonah", 48, 4, "And there is a word of Jehovah"),
    (33, "Micah", 105, 7, "A word of Jehovah"),
    (34, "Nahum", 47, 3, "Burden of Nineveh"),
    (35, "Habakkuk", 56, 3, "The burden that Habakkuk"),
    (36, "Zephaniah", 53, 3, "A word of Jehovah"),
    (37, "Haggai", 38, 2, "In the second year of Darius"),
    (38, "Zechariah", 211, 14, "In the eighth month"),
    (39, "Malachi", 55, 4, "The burden of a word of Jehovah"),
    (40, "Matthew", 1071, 28, "A roll of the birth of Jesus"),
    (41, "Mark", 678, 16, "A beginning of the good news"),
    (42, "Luke", 1151, 24, "Seeing that many did take in hand"),
    (43, "John", 879, 21, "In the beginning was the Word"),
    (44, "Acts", 1007, 28, "The former account, indeed"),
    (45, "Romans", 433, 16, "Paul, a servant of Jesus"),
    (46, "1 Corinthians", 437, 16, "Paul, a called apostle"),
    (47, "2 Corinthians", 257, 13, "Paul, an apostle of Jesus"),
    (48, "Galatians", 149, 6, "Paul, an apostle -- not from"),
    (49, "Ephesians", 155, 6, "Paul, an apostle of Jesus"),
    (50, "Philippians", 104, 4, "Paul and Timotheus"),
    (51, "Colossians", 95, 4, "Paul, an apostle of Jesus"),
    (52, "1 Thessalonians", 89, 5, "Paul, and Silvanus, and Timoth"),
    (53, "2 Thessalonians", 47, 3, "Paul, and Silvanus, and Timoth"),
    (54, "1 Timothy", 113, 6, "Paul, an apostle of Jesus"),
    (55, "2 Timothy", 83, 4, "Paul, an apostle of Jesus"),
    (56, "Titus", 46, 3, "Paul, a servant of God"),
    (57, "Philemon", 25, 1, "Paul, a prisoner of Christ"),
    (58, "Hebrews", 303, 13, "In many parts, and many ways"),
    (59, "James", 108, 5, "James, of God and of the Lord"),
    (60, "1 Peter", 105, 5, "Peter, an apostle of Jesus"),
    (61, "2 Peter", 61, 3, "Simeon Peter, a servant"),
    (62, "1 John", 105, 5, "That which was from the beginning"),
    (63, "2 John", 13, 1, "The Elder to the choice Kyria"),
    (64, "3 John", 14, 1, "The Elder to Gaius"),
    (65, "Jude", 25, 1, "Judas, of Jesus Christ"),
    (66, "Revelation", 404, 22, "A revelation of Jesus Christ"),
]

# Build (vcount, ccount) -> canonical position lookup
VC_CC_LOOKUP = {}
for i, (num, name, vc, cc, start) in enumerate(CANONICAL_FP):
    key = (vc, cc)
    if key not in VC_CC_LOOKUP:
        VC_CC_LOOKUP[key] = []
    VC_CC_LOOKUP[key].append((i+1, name, start))

def match_book(pos, vcount, ccount, ch1_v1):
    """Match a book to canonical using position + fingerprint."""
    if 1 <= pos <= 66:
        exp_num, exp_name, exp_vc, exp_cc, exp_start = CANONICAL_FP[pos-1]
        if abs(vcount - exp_vc) <= 2 and ccount == exp_cc:
            return exp_name

    key = (vcount, ccount)
    if key in VC_CC_LOOKUP:
        candidates = VC_CC_LOOKUP[key]
        # Text match
        for c_pos, c_name, c_start in candidates:
            if ch1_v1.startswith(c_start[:15]) or c_start[:15] in ch1_v1:
                return c_name
        # Collision: pick closest to position
        if len(candidates) > 1:
            return min(candidates, key=lambda x: abs(x[0] - pos) if pos > 0 else x[0])[1]
        return candidates[0][1]

    return f"Unknown ({vcount}v,{ccount}c)"

def normalize(data, translation_name, is_66_book=True):
    """Normalize flat verse list or re-name already-nested books."""
    if isinstance(data, dict) and 'books' in data:
        # Already nested - just re-name books
        books = data['books']
    else:
        # Flat list
        verses = data
        books_raw = {}
        for v in verses:
            b = v['book']
            if b not in books_raw:
                books_raw[b] = []
            books_raw[b].append(v)

        books_data = {}
        for b in books_raw:
            books_data[b] = {}
            for v in books_raw[b]:
                ch = v['chapter']
                if ch not in books_data[b]:
                    books_data[b][ch] = []
                books_data[b][ch].append({'verse': v['verse'], 'text': v['text']})

        books = []
        for book_num in sorted(books_data.keys()):
            chapters_list = [{'chapter': ch_num, 'verses': sorted(books_data[book_num][ch_num], key=lambda x: x['verse'])} 
                            for ch_num in sorted(books_data[book_num].keys())]
            books.append({'chapters': chapters_list})

    # Now rename books
    output_books = []
    for i, book in enumerate(books):
        vc = sum(len(ch['verses']) for ch in book['chapters'])
        cc = len(book['chapters'])
        ch1_v1 = book['chapters'][0]['verses'][0]['text'][:30] if book['chapters'] else ''

        if is_66_book:
            matched_name = match_book(i+1, vc, cc, ch1_v1)
        else:
            matched_name = f"Book {i+1}"

        output_books.append({'name': matched_name, 'chapters': book['chapters']})

    return {'translation': translation_name, 'books': output_books}

# Special handling for non-66-book translations
NON_66 = {'TISCH', 'LXX', 'WLCa', 'SYNOD', 'WEB'}

for key, info in TRANSLATIONS.items():
    code = info['code']
    name = info['name']
    path = f'translations/{code}.json'

    if not os.path.exists(path):
        print(f"  {code}: not found")
        continue

    with open(path) as f:
        data = json.load(f)

    is_66 = code not in NON_66
    output = normalize(data, name, is_66)

    total = sum(len(ch['verses']) for book in output['books'] for ch in book['chapters'])
    print(f"  {code}: {len(output['books'])} books, {total} verses")

    with open(path, 'w') as f:
        json.dump(output, f)

print("\nDone.")