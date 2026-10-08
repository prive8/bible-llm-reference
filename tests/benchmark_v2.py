"""Benchmark V2: Expanded Multi-Tradition Evaluation Benchmark with Dev/Held-out Split.

Provides 90 queries (15 per persona across all 6 personas) designed for
retrieval evaluation across Christian, Islamic, and Jewish canons.
Includes dev/held_out splits to prevent overfitting.
"""

from __future__ import annotations

# Benchmark Item: (query: str, persona: str, split: "dev" | "held_out", expected: list[tuple[str, int]])
# Relevance weights: 3 = primary, 2 = strong, 1 = related

BENCHMARK_V2: list[tuple[str, str, str, list[tuple[str, int]]]] = [
    # =========================================================================
    # SARAH (Lay-faithful / Pastoral / Daily devotion) — 15 queries
    # =========================================================================
    (
        "comfort in times of grief", "sarah", "dev",
        [("Matthew 5:4", 3), ("Psalms 23:4", 3), ("2 Corinthians 1:3-4", 3), ("Isaiah 41:10", 2), ("Psalms 34:18", 2)]
    ),
    (
        "feeling overwhelmed and anxious", "sarah", "dev",
        [("Philippians 4:6-7", 3), ("1 Peter 5:7", 3), ("Matthew 11:28-30", 3), ("Psalms 55:22", 2), ("Psalms 94:19", 2)]
    ),
    (
        "daily gratitude and thanksgiving", "sarah", "dev",
        [("1 Thessalonians 5:18", 3), ("Psalms 100:4", 3), ("Psalms 107:1", 3), ("Colossians 3:15", 2), ("Psalms 118:24", 2)]
    ),
    (
        "praying for healing and strength in sickness", "sarah", "dev",
        [("James 5:14-15", 3), ("Jeremiah 17:14", 3), ("Psalms 103:2-3", 3), ("Exodus 23:25", 2), ("Psalms 41:3", 2)]
    ),
    (
        "forgiving someone who hurt you deeply", "sarah", "dev",
        [("Colossians 3:13", 3), ("Ephesians 4:32", 3), ("Matthew 6:14-15", 3), ("Luke 6:37", 2), ("Mark 11:25", 2)]
    ),
    (
        "raising children in faith and love", "sarah", "dev",
        [("Proverbs 22:6", 3), ("Ephesians 6:4", 3), ("Deuteronomy 6:6-7", 3), ("Colossians 3:21", 2), ("Psalms 127:3", 2)]
    ),
    (
        "finding peace during sleepless nights", "sarah", "dev",
        [("Psalms 4:8", 3), ("Proverbs 3:24", 3), ("Psalms 63:6", 2), ("Psalms 127:2", 2), ("Psalms 91:5", 1)]
    ),
    (
        "trusting God when the future is uncertain", "sarah", "dev",
        [("Proverbs 3:5-6", 3), ("Jeremiah 29:11", 3), ("Romans 8:28", 3), ("Psalms 37:5", 2), ("Hebrews 11:1", 2)]
    ),
    (
        "overcoming feelings of loneliness and abandonment", "sarah", "held_out",
        [("Deuteronomy 31:6", 3), ("Psalms 27:10", 3), ("Isaiah 49:15", 3), ("Joshua 1:9", 2), ("Matthew 28:20", 2)]
    ),
    (
        "patience while waiting for answered prayer", "sarah", "held_out",
        [("Psalms 27:14", 3), ("Galatians 6:9", 3), ("Lamentations 3:25-26", 3), ("Romans 12:12", 2), ("Habakkuk 2:3", 2)]
    ),
    (
        "morning prayer of consecration and hope", "sarah", "held_out",
        [("Psalms 143:8", 3), ("Lamentations 3:22-23", 3), ("Psalms 5:3", 3), ("Psalms 90:14", 2), ("Isaiah 33:2", 1)]
    ),
    (
        "finding joy amidst sorrow and trials", "sarah", "held_out",
        [("James 1:2-3", 3), ("Romans 15:13", 3), ("Nehemiah 8:10", 2), ("Psalms 30:5", 3), ("John 16:22", 2)]
    ),
    (
        "comfort for elderly and aging believers", "sarah", "held_out",
        [("Isaiah 46:4", 3), ("Psalms 71:9", 3), ("Psalms 92:14", 2), ("Proverbs 16:31", 2), ("2 Corinthians 4:16", 2)]
    ),
    (
        "protection from harm and evil", "sarah", "held_out",
        [("Psalms 91:1-4", 3), ("2 Thessalonians 3:3", 3), ("Psalms 121:7-8", 3), ("Proverbs 18:10", 2), ("Psalms 23:4", 2)]
    ),
    (
        "love and unity in marriage and family", "sarah", "held_out",
        [("1 Corinthians 13:4-7", 3), ("Ephesians 4:2-3", 3), ("Colossians 3:14", 3), ("Ecclesiastes 4:9-12", 2), ("Proverbs 31:10", 1)]
    ),

    # =========================================================================
    # MARCUS (Wisdom-seeker / Philosophical / Ethics) — 15 queries
    # =========================================================================
    (
        "the purpose and meaning of human suffering", "marcus", "dev",
        [("Romans 5:3-5", 3), ("Job 23:10", 3), ("James 1:2-4", 3), ("1 Peter 1:6-7", 2), ("2 Corinthians 4:17", 2)]
    ),
    (
        "justice balanced with mercy and compassion", "marcus", "dev",
        [("Micah 6:8", 3), ("Zechariah 7:9", 3), ("James 2:13", 3), ("Hosea 6:6", 2), ("Matthew 23:23", 2)]
    ),
    (
        "humility versus arrogance and hubris", "marcus", "dev",
        [("Proverbs 16:18", 3), ("James 4:6", 3), ("Philippians 2:3", 3), ("Proverbs 11:2", 2), ("Micah 6:8", 2)]
    ),
    (
        "free will and moral responsibility", "marcus", "dev",
        [("Deuteronomy 30:19", 3), ("Galatians 6:7-8", 3), ("Joshua 24:15", 3), ("Romans 2:6", 2), ("Sirach 15:14-17", 2)]
    ),
    (
        "the fleeting nature of time and human life", "marcus", "dev",
        [("Ecclesiastes 1:2", 3), ("James 4:14", 3), ("Psalms 90:10-12", 3), ("Psalms 103:15-16", 2), ("Isaiah 40:6-8", 2)]
    ),
    (
        "danger of greed and pursuit of wealth", "marcus", "dev",
        [("1 Timothy 6:10", 3), ("Luke 12:15", 3), ("Proverbs 11:28", 3), ("Ecclesiastes 5:10", 2), ("Matthew 6:24", 2)]
    ),
    (
        "pursuit of truth and intellectual integrity", "marcus", "dev",
        [("John 8:32", 3), ("Proverbs 23:23", 3), ("Philippians 4:8", 3), ("1 Thessalonians 5:21", 2), ("Proverbs 12:19", 1)]
    ),
    (
        "controlling anger and the tongue", "marcus", "dev",
        [("James 1:19-20", 3), ("Proverbs 15:1", 3), ("Proverbs 16:32", 3), ("Ephesians 4:26", 2), ("James 3:5-6", 2)]
    ),
    (
        "wisdom contrasted with mere knowledge or folly", "marcus", "held_out",
        [("Proverbs 4:7", 3), ("James 3:17", 3), ("Job 28:28", 3), ("Ecclesiastes 7:12", 2), ("1 Corinthians 3:19", 2)]
    ),
    (
        "duty, moral obligation, and righteousness", "marcus", "held_out",
        [("Ecclesiastes 12:13", 3), ("Romans 13:8", 3), ("Luke 17:10", 2), ("Deuteronomy 10:12", 2), ("Matthew 5:6", 2)]
    ),
    (
        "true friendship and loyalty", "marcus", "held_out",
        [("Proverbs 17:17", 3), ("Proverbs 18:24", 3), ("John 15:13", 3), ("Ecclesiastes 4:9-10", 2), ("Proverbs 27:17", 2)]
    ),
    (
        "contemplation of death and mortality (memento mori)", "marcus", "held_out",
        [("Ecclesiastes 7:2", 3), ("Psalms 90:12", 3), ("Genesis 3:19", 3), ("Hebrews 9:27", 2), ("Job 14:1-2", 2)]
    ),
    (
        "qualities of a noble leader and ruler", "marcus", "held_out",
        [("Proverbs 29:2", 3), ("Mark 10:42-45", 3), ("2 Samuel 23:3", 3), ("Exodus 18:21", 2), ("Proverbs 16:12", 2)]
    ),
    (
        "inner integrity when no one is watching", "marcus", "held_out",
        [("Proverbs 10:9", 3), ("Psalms 51:6", 3), ("Luke 16:10", 3), ("2 Corinthians 8:21", 2), ("Psalms 15:1-2", 2)]
    ),
    (
        "the vanity of worldly ambition and fame", "marcus", "held_out",
        [("Ecclesiastes 2:11", 3), ("Mark 8:36", 3), ("1 John 2:16-17", 3), ("Jeremiah 9:23-24", 2), ("Galatians 6:14", 1)]
    ),

    # =========================================================================
    # AISHA (Scholar / Theological Precision / Doctrine) — 15 queries
    # =========================================================================
    (
        "nature of faith versus justification by works", "aisha", "dev",
        [("Romans 3:28", 3), ("James 2:24", 3), ("Ephesians 2:8-9", 3), ("Galatians 2:16", 2), ("James 2:17", 2)]
    ),
    (
        "covenant theology and the new covenant", "aisha", "dev",
        [("Jeremiah 31:31-34", 3), ("Hebrews 8:8-13", 3), ("Luke 22:20", 3), ("Genesis 17:7", 2), ("Exodus 24:8", 2)]
    ),
    (
        "uncompromising monotheism: the Shema and Tawhid", "aisha", "dev",
        [("Deuteronomy 6:4", 3), ("Quran 112:1-4", 3), ("Isaiah 45:5-6", 3), ("Mark 12:29", 2), ("Quran 2:255", 2)]
    ),
    (
        "eschatological day of judgment and resurrection", "aisha", "dev",
        [("Matthew 25:31-46", 3), ("Revelation 20:11-15", 3), ("Quran 82:1-19", 3), ("Daniel 12:2", 2), ("Quran 99:1-8", 2)]
    ),
    (
        "the divine attribute of mercy and the thirteen attributes", "aisha", "dev",
        [("Exodus 34:6-7", 3), ("Quran 1:1-3", 3), ("Psalms 103:8", 3), ("Quran 7:156", 2), ("Hosea 6:6", 2)]
    ),
    (
        "predestination, divine foreknowledge, and sovereignty", "aisha", "dev",
        [("Romans 9:18-21", 3), ("Ephesians 1:4-5", 3), ("Quran 57:22", 3), ("Isaiah 46:9-10", 2), ("Quran 54:49", 2)]
    ),
    (
        "the nature of holiness and divine transcendence", "aisha", "dev",
        [("Isaiah 6:3", 3), ("Leviticus 19:2", 3), ("Quran 59:23", 3), ("1 Peter 1:15-16", 2), ("1 Timothy 6:16", 2)]
    ),
    (
        "original human condition and the fall", "aisha", "dev",
        [("Genesis 3:1-19", 3), ("Romans 5:12", 3), ("Quran 7:19-25", 3), ("Psalms 51:5", 2), ("Quran 20:121-122", 2)]
    ),
    (
        "the theology of atonement and sacrificial offering", "aisha", "held_out",
        [("Leviticus 17:11", 3), ("Hebrews 9:22", 3), ("Isaiah 53:5", 3), ("Romans 3:25", 2), ("1 John 2:2", 2)]
    ),
    (
        "creation ex nihilo versus primordial ordering", "aisha", "held_out",
        [("Genesis 1:1-2", 3), ("John 1:1-3", 3), ("Hebrews 11:3", 3), ("Colossians 1:16", 2), ("Quran 21:30", 2)]
    ),
    (
        "concept of revelation (Wahy) and inspired scripture", "aisha", "held_out",
        [("2 Timothy 3:16", 3), ("2 Peter 1:20-21", 3), ("Quran 42:51", 3), ("Quran 2:2", 2), ("Exodus 20:1", 2)]
    ),
    (
        "kingdom of God and messianic expectations", "aisha", "held_out",
        [("Mark 1:15", 3), ("Isaiah 9:6-7", 3), ("Luke 17:20-21", 3), ("Daniel 7:13-14", 2), ("Psalms 2:7-8", 2)]
    ),
    (
        "the role and status of the Mosaic Law", "aisha", "held_out",
        [("Romans 7:12", 3), ("Matthew 5:17-18", 3), ("Galatians 3:24", 3), ("Psalms 19:7", 2), ("Deuteronomy 4:8", 2)]
    ),
    (
        "nature of the soul, spirit, and breath of life", "aisha", "held_out",
        [("Genesis 2:7", 3), ("Ecclesiastes 12:7", 3), ("Quran 17:85", 3), ("1 Thessalonians 5:23", 2), ("Quran 15:29", 2)]
    ),
    (
        "theological definition of sin: rebellion, missing mark, or transgression", "aisha", "held_out",
        [("1 John 3:4", 3), ("Romans 3:23", 3), ("Psalms 51:4", 3), ("Quran 4:31", 2), ("Isaiah 59:2", 2)]
    ),

    # =========================================================================
    # JORDAN (RAG Builder / Edge Cases / Specific Named Entities) — 15 queries
    # =========================================================================
    (
        "Melchizedek king of Salem priest of the Most High", "jordan", "dev",
        [("Genesis 14:18-20", 3), ("Hebrews 7:1-3", 3), ("Psalms 110:4", 3), ("Hebrews 5:6", 2)]
    ),
    (
        "Moses at the burning bush in Horeb", "jordan", "dev",
        [("Exodus 3:1-6", 3), ("Acts 7:30-32", 3), ("Quran 20:9-14", 3), ("Exodus 3:14", 2)]
    ),
    (
        "David and Goliath valley of Elah", "jordan", "dev",
        [("1 Samuel 17:40-51", 3), ("1 Samuel 17:4", 3), ("Quran 2:251", 3), ("Psalms 144:1", 1)]
    ),
    (
        "Elijah and the prophets of Baal on Mount Carmel", "jordan", "dev",
        [("1 Kings 18:20-40", 3), ("1 Kings 18:38", 3), ("James 5:17-18", 2), ("Quran 37:123-132", 2)]
    ),
    (
        "Queen of Sheba visiting King Solomon", "jordan", "dev",
        [("1 Kings 10:1-10", 3), ("2 Chronicles 9:1-9", 3), ("Quran 27:22-44", 3), ("Matthew 12:42", 2)]
    ),
    (
        "Job's loss and suffering in the land of Uz", "jordan", "dev",
        [("Job 1:13-22", 3), ("Job 2:7-10", 3), ("Quran 21:83-84", 3), ("James 5:11", 2)]
    ),
    (
        "Noah building the ark and the great deluge", "jordan", "dev",
        [("Genesis 6:13-22", 3), ("Genesis 7:1-12", 3), ("Quran 11:36-48", 3), ("Hebrews 11:7", 2)]
    ),
    (
        "Jonah swallowed by the great fish and prayer from the belly", "jordan", "dev",
        [("Jonah 1:17", 3), ("Jonah 2:1-10", 3), ("Matthew 12:40", 3), ("Quran 21:87-88", 3), ("Quran 37:139-148", 2)]
    ),
    (
        "Mary and the Annunciation by angel Gabriel", "jordan", "held_out",
        [("Luke 1:26-38", 3), ("Quran 19:16-21", 3), ("Quran 3:42-47", 3), ("Matthew 1:18-25", 2)]
    ),
    (
        "John the Baptist preaching in the Judean wilderness", "jordan", "held_out",
        [("Matthew 3:1-12", 3), ("Mark 1:1-8", 3), ("Luke 3:1-18", 3), ("John 1:19-28", 2), ("Quran 19:12-15", 2)]
    ),
    (
        "Joseph sold into Egypt by his brothers and the coat of many colors", "jordan", "held_out",
        [("Genesis 37:18-36", 3), ("Genesis 45:1-8", 3), ("Quran 12:15-20", 3), ("Acts 7:9-10", 2)]
    ),
    (
        "Daniel in the lions' den under King Darius", "jordan", "held_out",
        [("Daniel 6:10-23", 3), ("Hebrews 11:33", 2), ("Daniel 6:16", 3)]
    ),
    (
        "Isaiah's prophecy of the suffering servant", "jordan", "held_out",
        [("Isaiah 53:1-12", 3), ("Isaiah 52:13-15", 3), ("Acts 8:32-35", 3), ("1 Peter 2:24", 2)]
    ),
    (
        "The parting of the Red Sea during the Exodus", "jordan", "held_out",
        [("Exodus 14:15-31", 3), ("Quran 26:60-67", 3), ("Psalms 106:9", 2), ("Hebrews 11:29", 2)]
    ),
    (
        "Solomon's judgment between two mothers over the baby", "jordan", "held_out",
        [("1 Kings 3:16-28", 3), ("1 Kings 3:9", 2), ("2 Chronicles 1:10", 2)]
    ),

    # =========================================================================
    # YUKI (Comparative Researcher / Cross-Canon Parallels) — 15 queries
    # =========================================================================
    (
        "creation of the cosmos and living things across Bible and Quran", "yuki", "dev",
        [("Genesis 1:1-2", 3), ("Quran 7:54", 3), ("John 1:1-3", 3), ("Quran 21:30", 3), ("Quran 32:4", 2)]
    ),
    (
        "the golden rule and the universal ethic of reciprocity", "yuki", "dev",
        [("Matthew 7:12", 3), ("Luke 6:31", 3), ("Leviticus 19:18", 3), ("Tobit 4:15", 2)]
    ),
    (
        "almsgiving and charity as spiritual obligation across traditions", "yuki", "dev",
        [("Matthew 6:1-4", 3), ("Quran 2:261-267", 3), ("Deuteronomy 15:7-11", 3), ("Proverbs 19:17", 2), ("Quran 2:271", 2)]
    ),
    (
        "fasting as a spiritual discipline for humility and repentance", "yuki", "dev",
        [("Matthew 6:16-18", 3), ("Quran 2:183-185", 3), ("Isaiah 58:6-7", 3), ("Psalms 35:13", 2), ("Joel 2:12", 2)]
    ),
    (
        "hospitality to the stranger and sojourner across Jewish and Muslim texts", "yuki", "dev",
        [("Genesis 18:1-8", 3), ("Quran 51:24-27", 3), ("Leviticus 19:33-34", 3), ("Hebrews 13:2", 2), ("Quran 4:36", 2)]
    ),
    (
        "the story and sacrifice of Abraham's son across Genesis and Quran", "yuki", "dev",
        [("Genesis 22:1-14", 3), ("Quran 37:100-111", 3), ("Hebrews 11:17-19", 2), ("James 2:21", 2)]
    ),
    (
        "divine light symbolism: God as light of heaven and earth", "yuki", "dev",
        [("1 John 1:5", 3), ("Quran 24:35", 3), ("Psalms 27:1", 3), ("John 8:12", 2), ("Isaiah 60:19", 2)]
    ),
    (
        "parables of the sower and the mustard seed across texts", "yuki", "dev",
        [("Matthew 13:3-9", 3), ("Matthew 13:31-32", 3), ("Quran 48:29", 3), ("Mark 4:26-29", 2)]
    ),
    (
        "the flood narrative: righteous survivor and divine renewal", "yuki", "held_out",
        [("Genesis 8:1-19", 3), ("Quran 11:40-44", 3), ("Genesis 9:11-17", 3), ("Quran 23:27-30", 2)]
    ),
    (
        "angels as divine messengers and ministers", "yuki", "held_out",
        [("Psalms 103:20", 3), ("Hebrews 1:14", 3), ("Quran 35:1", 3), ("Luke 1:19", 2), ("Quran 2:97-98", 2)]
    ),
    (
        "repentance and the unmerited return of the sinner", "yuki", "held_out",
        [("Luke 15:11-24", 3), ("Quran 39:53-54", 3), ("Ezekiel 18:21-23", 3), ("Hosea 14:1-2", 2), ("Quran 4:110", 2)]
    ),
    (
        "prayer postures and reverent bowing before the Lord", "yuki", "held_out",
        [("Psalms 95:6", 3), ("Quran 22:77", 3), ("1 Kings 8:54", 2), ("Matthew 26:39", 2), ("Quran 3:43", 2)]
    ),
    (
        "pilgrimage as spiritual ascent and holy journey", "yuki", "held_out",
        [("Psalms 84:5-7", 3), ("Quran 2:196-200", 3), ("Deuteronomy 16:16", 2), ("Quran 22:27-29", 3)]
    ),
    (
        "justice and defense versus aggression and warfare limits", "yuki", "held_out",
        [("Quran 2:190", 3), ("Romans 12:19-21", 3), ("Deuteronomy 20:10-12", 2), ("Quran 22:39-40", 2), ("Matthew 5:38-39", 2)]
    ),
    (
        "divine wisdom personified and pre-existing creation", "yuki", "held_out",
        [("Proverbs 8:22-31", 3), ("Sirach 24:1-12", 3), ("John 1:1-3", 3), ("Wisdom 7:22-26", 2), ("Colossians 1:15-17", 2)]
    ),

    # =========================================================================
    # PRIYA (Interfaith Dialogue / Shared Patriarchs & Mutual Ethics) — 15 queries
    # =========================================================================
    (
        "Abraham as father of faith and friend of God", "priya", "dev",
        [("Genesis 12:1-3", 3), ("Quran 4:125", 3), ("James 2:23", 3), ("Romans 4:1-3", 2), ("Quran 16:120-123", 2)]
    ),
    (
        "Moses as liberator and lawgiver in Jewish and Islamic tradition", "priya", "dev",
        [("Exodus 20:1-17", 3), ("Quran 28:29-35", 3), ("Deuteronomy 34:10", 3), ("Quran 7:142-144", 2)]
    ),
    (
        "care and defense for the widow, orphan, and poor", "priya", "dev",
        [("James 1:27", 3), ("Quran 93:9-11", 3), ("Exodus 22:22-24", 3), ("Quran 2:215", 2), ("Isaiah 1:17", 2)]
    ),
    (
        "stewardship of the earth and care for nature as God's creation", "priya", "dev",
        [("Genesis 2:15", 3), ("Quran 6:165", 3), ("Psalms 24:1", 3), ("Quran 7:56", 2), ("Proverbs 12:10", 1)]
    ),
    (
        "speaking truth to power and confronting unjust rulers", "priya", "dev",
        [("Exodus 5:1", 3), ("Quran 20:43-44", 3), ("2 Samuel 12:1-7", 3), ("Amos 5:24", 2), ("Acts 4:19-20", 2)]
    ),
    (
        "forgiveness of enemies and returning good for evil", "priya", "dev",
        [("Matthew 5:44", 3), ("Quran 41:34", 3), ("Proverbs 25:21-22", 3), ("Romans 12:20", 2), ("Quran 42:40", 2)]
    ),
    (
        "honoring parents with kindness and obedience across traditions", "priya", "dev",
        [("Exodus 20:12", 3), ("Quran 17:23-24", 3), ("Ephesians 6:1-3", 3), ("Quran 31:14", 2), ("Proverbs 23:22", 2)]
    ),
    (
        "honesty in commerce: just weights and measures", "priya", "dev",
        [("Leviticus 19:35-36", 3), ("Quran 83:1-3", 3), ("Proverbs 11:1", 3), ("Quran 17:35", 2), ("Deuteronomy 25:13-16", 2)]
    ),
    (
        "peacemaking, reconciliation, and resolving disputes", "priya", "held_out",
        [("Matthew 5:9", 3), ("Quran 49:9-10", 3), ("Romans 12:18", 3), ("Psalms 34:14", 2), ("Hebrews 12:14", 2)]
    ),
    (
        "unity of humanity: all nations descended from common origin", "priya", "held_out",
        [("Acts 17:26", 3), ("Quran 49:13", 3), ("Genesis 1:27", 3), ("Malachi 2:10", 2)]
    ),
    (
        "remembering God continually (remembrance and Dhikr)", "priya", "held_out",
        [("1 Thessalonians 5:17", 3), ("Quran 2:152", 3), ("Psalms 16:8", 3), ("Quran 13:28", 2), ("Deuteronomy 8:18", 2)]
    ),
    (
        "the sin of hypocrisy and saying what one does not practice", "priya", "held_out",
        [("Matthew 23:3", 3), ("Quran 61:2-3", 3), ("Isaiah 29:13", 3), ("Romans 2:21-23", 2), ("Quran 2:44", 2)]
    ),
    (
        "treating travelers and refugees with dignity and support", "priya", "held_out",
        [("Deuteronomy 10:18-19", 3), ("Quran 9:6", 3), ("Matthew 25:35", 3), ("Leviticus 24:22", 2), ("Quran 2:177", 2)]
    ),
    (
        "fostering humility in religious practice without public ostentation", "priya", "held_out",
        [("Matthew 6:5-6", 3), ("Quran 107:4-7", 3), ("Luke 18:10-14", 3), ("Quran 7:55", 2), ("Proverbs 27:2", 1)]
    ),
    (
        "hope in the ultimate triumph of righteousness over oppression", "priya", "held_out",
        [("Psalms 37:9-11", 3), ("Quran 21:105", 3), ("Habakkuk 2:14", 3), ("Revelation 21:4", 2), ("Quran 28:5", 2)]
    ),
]
