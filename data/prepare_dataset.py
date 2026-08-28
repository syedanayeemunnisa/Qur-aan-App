"""Quran dataset preparation script.

Downloads authentic Quranic text, translations, and transliteration
from trusted open-source APIs, merges them into a single JSON dataset,
and exports to SQLite.

Usage:
    python prepare_dataset.py                # Download + build
    python prepare_dataset.py --validate     # Validate existing dataset
    python prepare_dataset.py --export-csv   # Export to CSV
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from quran_dataset import QuranDataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATA_DIR = Path(__file__).resolve().parent
OUTPUT_JSON = DATA_DIR / "quran_dataset.json"


# ── API sources ─────────────────────────────────────────────────────

# fawazahmed0/quran-api — free, no rate limit, CDN-backed
# Uses GitHub CDN: https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/
QURAN_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions"

# Edition codes for translations
# Each edition name maps to a .json file at {QURAN_API_BASE}/{edition}.json
# Response format: {"quran": [{chapter, verse, text}, ...]}
# Available editions from: https://github.com/fawazahmed0/quran-api

# Arabic edition (Uthmani Hafs script with diacritics)
ARABIC_EDITION = "ara-quranuthmanihaf"

# Translation editions by language
TRANSLATION_EDITIONS = {
    # Format: {language: edition_name}
    # English: Muhammad Taqi-ud-Din al-Hilali & Muhammad Muhsin Khan
    # (Closest authentic English translation available in the API)
    "english": "eng-muhammadtaqiudd",
    # Urdu: Muhammad Junagarhi
    "urdu": "urd-muhammadjunagar",
    # Hindi: Muhammad Farooq Khan
    "hindi": "hin-muhammadfarooqk",
    # Telugu: Muhammad Aziz Ur Rehman
    "telugu": "tel-muhammadazizurr",
}

# Transliteration editions (Arabic text with Roman transliteration)
# Uses the same format but with -la suffix for transliteration
TRANSLITERATION_EDITIONS = {
    "english": "ara-quran-la",  # Standard Arabic transliteration
}

# Direct URLs for cached / reliable editions
EDITION_URLS = {}
# Arabic primary
EDITION_URLS["arabic"] = f"{QURAN_API_BASE}/{ARABIC_EDITION}.json"
# Translations
for lang, edition in TRANSLATION_EDITIONS.items():
    EDITION_URLS[lang] = f"{QURAN_API_BASE}/{edition}.json"
# Transliteration
for lang, edition in TRANSLITERATION_EDITIONS.items():
    EDITION_URLS[f"{lang}_transliteration"] = f"{QURAN_API_BASE}/{edition}.json"


# ── Download helpers ────────────────────────────────────────────────


def _fetch_json(url: str) -> list[dict]:
    """Fetch JSON from URL with retry.

    The fawazahmed0 API returns wrapper format: {"key": [{...}, ...]}
    This function unwraps the wrapper and returns the inner list.
    """
    import time

    try:
        import httpx

        client = httpx.Client(timeout=30.0)
        for attempt in range(3):
            try:
                resp = client.get(url)
                resp.raise_for_status()
                raw = resp.json()
                # Unwrap wrapper: {"quran": [...]} or any single-key wrapper
                if isinstance(raw, dict) and len(raw) == 1:
                    key = list(raw.keys())[0]
                    inner = raw[key]
                    if isinstance(inner, list):
                        return inner
                # If it's already a list, return as-is
                if isinstance(raw, list):
                    return raw
                logger.warning(
                    "Unexpected format from %s: %s", url, type(raw)
                )
                return []
            except Exception as e:
                if attempt < 2:
                    logger.warning(
                        "Retry %d for %s: %s", attempt + 1, url, e
                    )
                    time.sleep(2)
                else:
                    raise
    except ImportError:
        logger.warning(
            "httpx not installed. Try: pip install httpx"
        )
        return []
    except Exception as e:
        logger.error("Failed to fetch %s: %s", url, e)
        return []


def _build_verse_map(edition_data: list[dict]) -> dict:
    """Convert [{chapter, verse, text}] → {(chapter, verse): text}."""
    return {
        (item["chapter"], item["verse"]): item["text"]
        for item in edition_data
        if isinstance(item, dict)
    }


def _normalize_arabic(text: str) -> str:
    """Remove diacritics from Arabic text (basic normalisation)."""
    import re
    diacritics = re.compile(
        "[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u08D0-\u08FF]"
    )
    return diacritics.sub("", text)


# ── Main builder ────────────────────────────────────────────────────


def download_and_prepare(
    output_path: Path = OUTPUT_JSON,
) -> Path:
    """Download all editions and merge into a single JSON dataset.

    Falls back to generating synthetic data for the dataset structure
    if API calls fail (to enable offline development).
    """
    logger.info("Downloading Quran dataset from trusted APIs …")

    # Fetch all editions in parallel
    import concurrent.futures

    results: dict[str, list[dict]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {
            pool.submit(_fetch_json, url): name
            for name, url in EDITION_URLS.items()
        }
        for future in concurrent.futures.as_completed(future_map):
            name = future_map[future]
            try:
                results[name] = future.result()
            except Exception as e:
                logger.error("Failed to fetch %s: %s", name, e)
                results[name] = []

    # Build maps
    arabic_map = _build_verse_map(results.get("arabic", []))
    english_map = _build_verse_map(results.get("english", []))
    english_trans_map = _build_verse_map(results.get("english_transliteration", []))
    urdu_map = _build_verse_map(results.get("urdu", []))
    urdu_trans_map = _build_verse_map(results.get("urdu_transliteration", []))
    hindi_map = _build_verse_map(results.get("hindi", []))
    hindi_trans_map = _build_verse_map(results.get("hindi_transliteration", []))
    telugu_map = _build_verse_map(results.get("telugu", []))
    telugu_trans_map = _build_verse_map(results.get("telugu_transliteration", []))

    # Build maps for translations
    # Note: urdu, hindi, telugu, and transliteration editions may not exist
    # The script handles missing editions gracefully with empty strings

    # Merge into unified dataset
    dataset = []
    for (surah, ayah), arabic_text in arabic_map.items():
        key = (surah, ayah)

        # Transliteration: use Arabic transliteration as the roman field
        roman_text = english_trans_map.get(key, "")

        # Clean up transliteration formatting (remove HTML tags)
        if roman_text:
            import re
            roman_text = re.sub(r"<[^>]+>", "", roman_text)

        verse = {
            "surah": surah,
            "ayah": ayah,
            "verse_key": f"{surah}:{ayah}",
            "arabic": arabic_text,
            "normalized": _normalize_arabic(arabic_text),
            "english": english_map.get(key, ""),
            "urdu": urdu_map.get(key, ""),
            "hindi": hindi_map.get(key, ""),
            "telugu": telugu_map.get(key, ""),
            "roman": roman_text or "",
            "juz": None,
            "page": None,
            "sajda": None,
        }
        dataset.append(verse)

    # Sort by surah, ayah
    dataset.sort(key=lambda v: (v["surah"], v["ayah"]))

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    logger.info(
        "Dataset saved to %s — %d verses.",
        output_path,
        len(dataset),
    )
    return output_path


# ── CLI ─────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Prepare the Quran dataset."
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the existing dataset.",
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        help="Export dataset to CSV file path.",
    )
    parser.add_argument(
        "--export-sqlite",
        type=str,
        default=None,
        const=str(DATA_DIR / "quran.db"),
        nargs="?",
        help="Export dataset to SQLite file path.",
    )
    args = parser.parse_args()

    if args.validate:
        ds = QuranDataset()
        ds.load()
        issues = ds.validate()
        if issues:
            logger.error("Validation FAILED with %d issues:", len(issues))
            for issue in issues[:20]:
                logger.error("  • %s", issue)
        else:
            logger.info("Dataset validation PASSED ✓")
        return

    # Download and build
    download_and_prepare()

    ds = QuranDataset()
    ds.load()

    # Validate after build
    issues = ds.validate()
    if issues:
        logger.warning("Dataset has %d issues.", len(issues))
    else:
        logger.info("Dataset validated OK ✓")

    # Stats
    stats = ds.verses_per_surah()
    logger.info(
        "Dataset: %d surahs, %d verses",
        len(stats),
        ds.total_verses,
    )

    # Optional exports
    if args.export_csv:
        ds.export_csv(Path(args.export_csv))

    if args.export_sqlite:
        ds.export_sqlite(Path(args.export_sqlite))
        logger.info("SQLite export complete.")

    logger.info("All done! Ready to use.")


if __name__ == "__main__":
    main()
