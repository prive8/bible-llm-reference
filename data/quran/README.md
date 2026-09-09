# Quran Corpus (Phase 3.1)

Public-domain Quran translations and Arabic text in the project's canonical multi-tradition JSON schema (`docs/data-schema.md` §2).

## Source Attribution & License

- **Data source:** Ingested from [`fawazahmed0/quran-api`](https://github.com/fawazahmed0/quran-api) (licensed under **The Unlicense** / Public Domain).
- **Primary source repositories:** [Tanzil.net](http://tanzil.net) and the [King Fahd Complex for the Printing of the Holy Quran](https://qurancomplex.gov.sa/).
- **Editions included:**
  - `saheeh-international.json` — Saheeh International (1996), translated by Umm Muhammad (Emily Assami, Mary Kennedy, Amatullah Bantley). Tanzil.net (Public Domain).
  - `yusuf-ali.json` — Abdullah Yusuf Ali (1934 translation). Tanzil.net (Public Domain).
  - `pickthall.json` — Mohammed Marmaduke Pickthall (1930 translation, *The Meaning of the Glorious Koran*). Tanzil.net (Public Domain).
  - `mufti-taqi-usmani.json` — Mufti Muhammad Taqi Usmani translation. Tanzil.net (Public Domain).
  - `arberry.json` — Arthur John Arberry (1955 translation, *The Koran Interpreted*). Tanzil.net (Public Domain).
  - `uthmani.json` — Arabic Uthmani text (Hafs recitation), King Fahd Quran Complex / Tanzil.net (Public Domain).

## Schema

Each edition follows the unified tradition schema:

```json
{
  "tradition": "islam",
  "translation": "Saheeh International (1996)",
  "key": "saheeh-international",
  "language": "en",
  "structure": "surah_ayah",
  "license": "Public Domain (tanzil.net)",
  "source": "fawazahmed0/quran-api (tanzil.net)",
  "divisions": [
    {
      "id": 1,
      "name": "Al-Fatihah",
      "name_english": "The Opening",
      "name_transliteration": "al-fatihah",
      "revelation_period": "Meccan",
      "ayahs": [
        {
          "ayah": 1,
          "text": "In the name of Allah, the Entirely Merciful, the Especially Merciful"
        }
      ]
    }
  ]
}
```
