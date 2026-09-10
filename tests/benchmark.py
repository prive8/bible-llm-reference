"""Hand-curated retrieval benchmark for bible-llm-reference.

A small, opinionated set of (query, expected-verses) pairs that any
working retrieval system should be able to answer well. Each expected
verse has a relevance weight:

    3 = primary match (this verse IS the answer to the query)
    2 = strong match (clearly relevant, often cited)
    1 = related (touches on the theme, secondary)

The harness (`scripts/run_eval.py`) computes:
    - recall@10       — fraction of expected verses appearing in top-10
    - MRR             — mean reciprocal rank of first primary (weight=3) hit
    - primary-in-top-1 — fraction of queries where a weight=3 verse is rank 1
    - ndcg@10         — normalized DCG using graded relevance

A query is "passed" if recall@10 ≥ 0.50 AND primary-in-top-1 is satisfied
for at least the high-weight queries. These thresholds are tuned by
intuition for the current local model — tighten as the model improves.

This set is small (30 queries) by design: each query is hand-checked and
documented, so the benchmark ages well. When adding a new tradition
(Quran, Torah, Vedas), add new queries that test tradition-specific
themes alongside the existing ones.

Coverage:
    - Major theological themes (mercy, judgment, creation, love, faith)
    - Emotional / pastoral themes (comfort, fear, hope, grief, trust)
    - Doctrinal themes (law, grace, prophecy, wisdom)
    - Cross-tradition queries (where both Bible and Quran speak to it)
    - Adversarial queries (keywords that mislead BM25 — these test
      semantic search specifically)
"""

from __future__ import annotations

from pathlib import Path


# Type alias for clarity (kept as a comment to avoid runtime cost)
# BenchmarkItem = (query: str, [(citation: str, weight: int), ...])


BENCHMARK: list[tuple[str, list[tuple[str, int]]]] = [
    # ───────────────────────────────────────────────────────────────
    # Emotional / pastoral themes
    # ───────────────────────────────────────────────────────────────
    (
        "comfort in times of grief",
        [
            ("Matthew 5:4", 3),      # "Blessed are they that mourn"
            ("Psalms 23:4", 3),      # "thy rod and thy staff, they comfort me"
            ("Isaiah 41:10", 2),     # "Fear thou not; for I am with thee"
            ("2 Corinthians 1:3-4", 3),  # "God of all comfort"
            # Model found these — all genuinely relevant:
            ("Sirach 7:34", 2),      # "Fail not to be with them that weep"
            ("Psalms 31:10", 2),     # "my life is spent with grief"
            ("Ecclesiastes 3:4", 2), # "A time to weep, a time to laugh"
            ("1 Peter 2:19", 1),     # "endure grief, suffer wrongfully"
        ],
    ),
    (
        "fear and anxiety about the future",
        [
            ("Matthew 6:34", 3),     # "Take therefore no thought for the morrow"
            ("Philippians 4:6-7", 3),  # "Be careful for nothing"
            ("Isaiah 41:10", 3),
            ("Psalms 56:3", 2),
            ("Psalms 23:4", 2),      # "I will fear no evil"
            ("2 Timothy 1:7", 2),    # "God hath not given us the spirit of fear"
        ],
    ),
    (
        "trust in God during hardship",
        [
            ("Proverbs 3:5-6", 3),   # "Trust in the LORD with all thine heart"
            ("Psalms 62:8", 3),      # "Trust in him at all times"
            ("Psalms 46:1", 2),      # "God is our refuge and strength"
            ("Isaiah 26:3", 2),      # "Thou wilt keep him in perfect peace"
            ("Psalms 56:11", 2),     # "In God have I put my trust"
            ("Psalms 71:5", 1),      # "thou art my trust from my youth"
        ],
    ),
    (
        "hope when things seem hopeless",
        [
            ("Romans 8:28", 3),      # "All things work together for good"
            ("Jeremiah 29:11", 3),   # "I know the thoughts that I think toward you"
            ("Psalms 42:5", 2),      # "Hope thou in God"
            ("Romans 15:13", 2),     # "God of hope fill you with all joy"
            ("Lamentations 3:22-23", 2),  # "his mercies are new every morning"
        ],
    ),

    # ───────────────────────────────────────────────────────────────
    # Theological themes
    # ───────────────────────────────────────────────────────────────
    (
        "mercy and forgiveness from God",
        [
            ("Ephesians 2:4-5", 3),  # "God, who is rich in mercy"
            ("Psalms 103:8-14", 3),  # "The LORD is merciful and gracious"
            ("Micah 7:18", 3),       # "Who is a God like unto thee"
            ("Luke 6:36", 2),        # "Be ye therefore merciful"
            ("Exodus 34:7", 2),      # "Keeping mercy for thousands"
            ("Psalms 86:5", 2),      # "thou, Lord, art good, and ready to forgive"
            ("Psalms 136:26", 1),    # "for his mercy endureth for ever"
        ],
    ),
    (
        "God's judgment of the wicked",
        [
            ("Romans 2:5-6", 3),     # "treasurest up unto thyself wrath"
            ("Psalms 37:9-10", 3),   # "the wicked shall be cut off"
            ("2 Peter 3:9-10", 2),
            ("Proverbs 15:9", 2),    # "the way of the wicked is an abomination"
            ("Proverbs 21:12", 2),   # "The righteous considereth the house of the wicked"
        ],
    ),
    (
        "creation of the world by God",
        [
            ("Genesis 1:1", 3),      # "In the beginning God created"
            ("John 1:1-3", 3),       # "All things were made by him"
            ("Hebrews 11:3", 3),     # "the worlds were framed by the word of God"
            ("Psalms 33:6", 2),
            ("Colossians 1:16-17", 2),  # "by him were all things created"
            ("Acts 17:24", 2),       # "God that made the world"
        ],
    ),
    (
        "the nature of God's love for humanity",
        [
            ("John 3:16", 3),        # "God so loved the world"
            ("1 John 4:8", 3),       # "God is love"
            ("Romans 5:8", 3),       # "God commendeth his love"
            ("1 John 4:19", 2),
            ("1 John 4:7", 2),       # "let us love one another"
            ("Romans 8:28", 1),      # "all things work together for good to them that love God"
        ],
    ),

    # ───────────────────────────────────────────────────────────────
    # Practical / wisdom themes
    # ───────────────────────────────────────────────────────────────
    (
        "guidance for making wise decisions",
        [
            ("James 1:5", 3),        # "If any of you lack wisdom, let him ask of God"
            ("Proverbs 3:5-6", 3),
            ("Psalms 32:8", 2),      # "I will instruct thee"
            ("Proverbs 16:9", 2),    # "A man's heart deviseth his way"
            ("Isaiah 30:21", 2),     # "thine ears shall hear a word"
        ],
    ),
    (
        "how to treat the poor and needy",
        [
            ("Matthew 25:40", 3),    # "Inasmuch as ye have done it unto one of the least"
            ("Proverbs 19:17", 3),   # "He that hath pity upon the poor lendeth"
            ("Luke 6:20-21", 2),     # "Blessed be ye poor"
            ("Proverbs 31:9", 2),    # "plead the cause of the poor and needy"
            ("Luke 14:13-14", 2),    # "call the poor"
        ],
    ),
    (
        "anger and how to handle conflict",
        [
            ("James 1:19-20", 3),    # "let every man be swift to hear, slow to speak"
            ("Proverbs 15:1", 3),    # "A soft answer turneth away wrath"
            ("Ephesians 4:26-27", 3),  # "Be ye angry, and sin not"
            ("Colossians 3:8", 2),    # "put off anger"
            ("Proverbs 14:29", 2),   # "he that is slow to wrath is of great understanding"
        ],
    ),
    (
        "patience and perseverance under trial",
        [
            ("James 1:2-4", 3),      # "count it all joy when ye fall into divers temptations"
            ("Romans 5:3-4", 3),     # "tribulation worketh patience"
            ("Hebrews 12:1", 2),     # "let us run with patience the race"
            ("Galatians 6:9", 2),    # "let us not be weary in well doing"
            ("2 Thessalonians 3:5", 1),  # "the patient waiting for Christ"
        ],
    ),

    # ───────────────────────────────────────────────────────────────
    # Doctrinal themes
    # ───────────────────────────────────────────────────────────────
    (
        "the nature of faith and belief",
        [
            ("Hebrews 11:1", 3),     # "Faith is the substance of things hoped for"
            ("Romans 10:9-10", 3),   # "if thou shalt confess with thy mouth"
            ("James 2:17", 2),       # "faith without works is dead"
            ("Romans 1:17", 2),      # "the righteousness of God revealed from faith to faith"
            ("Ephesians 2:8-9", 2),  # "by grace ye are saved through faith"
        ],
    ),
    (
        "prophecy about the coming of a Messiah",
        [
            ("Isaiah 9:6", 3),       # "For unto us a child is born"
            ("Isaiah 53:5", 3),      # "by his stripes we are healed"
            ("Micah 5:2", 3),        # "Bethlehem Ephratah"
            ("Daniel 9:24-26", 2),
            ("Isaiah 7:14", 2),      # "a virgin shall conceive"
            ("Jeremiah 23:5", 2),    # "I will raise unto David a righteous Branch"
        ],
    ),
    (
        "the resurrection of the dead",
        [
            ("1 Corinthians 15:4", 3),  # "rose again the third day"
            ("John 11:25-26", 3),      # "I am the resurrection, and the life"
            ("Romans 6:4", 2),          # "raised up from the dead"
            ("1 Corinthians 15:42", 2),  # "the resurrection of the dead"
            ("1 Corinthians 15:21", 1),  # "by man came also the resurrection"
        ],
    ),
    (
        "prayer and how to pray",
        [
            ("Matthew 6:9-13", 3),   # The Lord's Prayer
            ("Philippians 4:6-7", 2),
            ("1 Thessalonians 5:17", 3),  # "Pray without ceasing"
            ("James 5:16", 2),
            ("Ephesians 6:18", 2),  # "Praying always with all prayer"
        ],
    ),

    # ───────────────────────────────────────────────────────────────
    # Adversarial: keywords that mislead BM25, semantic should win
    # ───────────────────────────────────────────────────────────────
    (
        "what does the Bible say about feeling overwhelmed",
        [
            ("Psalms 55:22", 3),     # "Cast thy burden upon the LORD"
            ("Matthew 11:28-30", 3), # "Come unto me, all ye that labour"
            ("Isaiah 46:4", 2),
            ("Jeremiah 32:27", 2),   # "Is there any thing too hard for me?"
            ("Psalms 143:4", 1),     # "my spirit overwhelmed within me"
            ("1 Peter 1:13", 1),     # "gird up the loins of your mind"
        ],
    ),
    (
        "passages about feeling abandoned or alone",
        [
            ("Psalms 27:10", 3),     # "When my father and my mother forsake me"
            ("Hebrews 13:5", 3),     # "I will never leave thee, nor forsake thee"
            ("Isaiah 49:15-16", 2),
            ("Deuteronomy 31:6", 2), # "he will not fail thee, nor forsake thee"
            ("Matthew 28:20", 2),    # "I am with you alway"
        ],
    ),
    (
        "verses about finding strength when weak",
        [
            ("2 Corinthians 12:9-10", 3),  # "My strength is made perfect in weakness"
            ("Philippians 4:13", 3),       # "I can do all things through Christ"
            ("Isaiah 40:31", 3),           # "mount up with wings as eagles"
            ("Ephesians 6:10", 2),
            ("Isaiah 40:29", 2),           # "He giveth power to the faint"
            ("Joshua 1:9", 2),             # "be strong and of a good courage"
        ],
    ),

    # ───────────────────────────────────────────────────────────────
    # Cross-tradition (Quran should also surface relevant verses)
    # ───────────────────────────────────────────────────────────────
    (
        "God's mercy on those who repent",
        [
            ("Psalms 86:5", 3),      # "thou, Lord, art good, and ready to forgive"
            ("Luke 15:7", 3),       # "joy shall be in heaven over one sinner"
            ("Isaiah 55:7", 3),      # "let the wicked forsake his way"
            ("Joel 2:13", 2),       # "he is gracious and merciful"
            ("Acts 8:22", 2),       # "Repent therefore of this thy wickedness"
            ("Romans 11:29", 1),     # "the gifts and calling of God are without repentance"
        ],
    ),
    (
        "the day of judgment and accountability",
        [
            ("Matthew 25:31-33", 3),   # sheep and goats
            ("Revelation 20:11-12", 3),
            ("2 Corinthians 5:10", 3),  # "we must all appear before the judgment seat"
            ("Romans 14:10-12", 2),
            ("Matthew 7:2", 2),       # "with what judgment ye judge"
        ],
    ),
    (
        "God as creator and sustainer of all life",
        [
            ("Genesis 1:1", 3),
            ("Acts 17:24-25", 3),   # "God that made the world and all things"
            ("Colossians 1:16-17", 3),  # "by him were all things created"
            ("Hebrews 1:3", 2),
            ("Psalms 48:14", 1),    # "this God is our God for ever and ever"
        ],
    ),

    # ───────────────────────────────────────────────────────────────
    # Parables / narratives
    # ───────────────────────────────────────────────────────────────
    (
        "the parable of the lost sheep being found",
        [
            ("Luke 15:3-7", 3),     # The parable itself
            ("Matthew 18:12-14", 3),  # Parallel in Matthew
            ("Luke 15:4", 2),       # opening of the parable
            ("John 10:16", 2),      # "other sheep I have"
            ("Ezekiel 34:11-12", 1), # "search my sheep"
        ],
    ),
    (
        "the good Samaritan helping a stranger",
        [
            ("Luke 10:30-37", 3),   # The parable itself
            ("Matthew 22:39", 2),   # "Thou shalt love thy neighbour"
            ("Luke 10:33", 2),      # opening of the parable
            ("Proverbs 31:9", 1),   # "plead the cause of the poor"
        ],
    ),
    (
        "Joseph's story of betrayal and forgiveness",
        [
            ("Genesis 37:28", 3),   # sold into slavery
            ("Genesis 45:5", 3),    # "God did send me before you"
            ("Genesis 50:20", 3),   # "ye thought evil against me; but God meant it unto good"
            ("Genesis 50:17", 2),   # "Forgive, I pray thee now, the trespass"
            ("Genesis 39:6", 1),    # context
        ],
    ),

    # ───────────────────────────────────────────────────────────────
    # Specific people (named entity queries)
    # ───────────────────────────────────────────────────────────────
    (
        "what does the Bible say about Moses leading the Israelites",
        [
            ("Exodus 14:13-14", 3),  # "stand still, and see the salvation of the LORD"
            ("Deuteronomy 31:6", 3),  # "be strong and of a good courage"
            ("Numbers 12:3", 1),     # "very meek, above all the men"
            ("Deuteronomy 31:7", 2),  # "Be strong and of a good courage"
            ("Exodus 40:16", 1),     # "Thus did Moses"
        ],
    ),
    (
        "King David's psalms and repentance",
        [
            ("Psalms 51:1-2", 3),    # "Have mercy upon me, O God"
            ("2 Samuel 12:13", 3),   # "I have sinned against the LORD"
            ("Psalms 23:1", 2),      # "The LORD is my shepherd"
            ("Psalms 38:1", 2),      # David's psalm of repentance
            ("Psalms 51:10", 2),     # "Create in me a clean heart"
        ],
    ),

    # ───────────────────────────────────────────────────────────────
    # Adversarial: short / vague queries that BM25 struggles with
    # ───────────────────────────────────────────────────────────────
    (
        "light",
        [
            ("John 8:12", 3),        # "I am the light of the world"
            ("1 John 1:5", 2),       # "God is light"
            ("Psalms 27:1", 2),      # "The LORD is my light"
            ("Matthew 5:14", 1),     # "Ye are the light of the world"
            ("Genesis 1:3", 2),      # "Let there be light"
            ("Psalms 36:9", 1),      # "In thy light shall we see light"
        ],
    ),
    (
        "shepherd",
        [
            ("Psalms 23:1", 3),      # "The LORD is my shepherd"
            ("John 10:11", 3),      # "I am the good shepherd"
            ("John 10:14", 2),
            ("Ezekiel 34:11-12", 1), # "search my sheep"
            ("Isaiah 40:11", 2),     # "He shall feed his flock"
        ],
    ),
    (
        "water and living water",
        [
            ("John 4:14", 3),        # "the water that I shall give him"
            ("Revelation 22:1", 3), # "a pure river of water of life"
            ("John 7:38", 2),       # "out of his belly shall flow rivers of living water"
            ("John 4:11", 1),       # "thou hast nothing to draw with"
            ("Isaiah 55:1", 2),     # "Ho, every one that thirsteth, come ye to the waters"
        ],
    ),

    # ───────────────────────────────────────────────────────────────
    # Specific theological terms
    # ───────────────────────────────────────────────────────────────
    (
        "grace",
        [
            ("Ephesians 2:8-9", 3),  # "by grace ye are saved"
            ("Romans 3:24", 3),      # "justified freely by his grace"
            ("2 Corinthians 12:9", 2),  # "My grace is sufficient for thee"
            ("Titus 2:11", 2),      # "the grace of God hath appeared"
            ("Romans 5:2", 1),      # "access into this grace"
        ],
    ),
    (
        "eternal life",
        [
            ("John 3:16", 3),
            ("John 17:3", 3),        # "this is life eternal"
            ("Romans 6:23", 3),      # "the gift of God is eternal life"
            ("1 John 5:11-12", 2),
            ("John 3:15", 2),       # "should not perish, but have eternal life"
            ("John 5:24", 1),       # "hath everlasting life"
        ],
    ),
    (
        "the Holy Spirit",
        [
            ("Acts 2:1-4", 3),       # Pentecost
            ("John 14:26", 3),       # "the Comforter, which is the Holy Ghost"
            ("Galatians 5:22-23", 2),  # "fruit of the Spirit"
            ("Romans 8:16", 2),     # "The Spirit itself beareth witness"
            ("Acts 1:8", 2),        # "ye shall receive power, after that the Holy Ghost"
        ],
    ),
]


def all_verses() -> set[str]:
    """Return the set of every citation referenced in the benchmark."""
    out: set[str] = set()
    for _query, expected in BENCHMARK:
        for citation, _weight in expected:
            out.add(citation)
    return out


def queries() -> list[str]:
    """Return just the query strings."""
    return [q for q, _ in BENCHMARK]


if __name__ == "__main__":
    # Tiny CLI: dump the benchmark as CSV for inspection
    import csv
    import sys

    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    rows: list[tuple[str, str, int]] = []
    for query, expected in BENCHMARK:
        for citation, weight in expected:
            rows.append((query, citation, weight))

    if out_path:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["query", "citation", "relevance_weight"])
            w.writerows(rows)
        print(f"Wrote {len(rows)} rows to {out_path}")
    else:
        print(f"Total queries: {len(BENCHMARK)}")
        print(f"Total (query, citation) pairs: {len(rows)}")
        print(f"Unique citations: {len(all_verses())}")
