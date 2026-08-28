"""Roman English transliteration generator for Quranic Arabic.

Provides both:
  1. Rule-based transliteration (character mapping)
  2. Dataset-based lookup (from preloaded Quran transliteration data)

The rule-based approach is a fallback when the dataset does not
include transliteration for a given verse.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class TransliterationGenerator:
    """Generate Roman English transliteration for Arabic Quranic text.

    Uses a hybrid approach:
      - Primary: lookup from preloaded dataset
      - Fallback: rule-based character mapping

    The rule-based system follows the standard SATTS (Standard Arabic
    Technical Transliteration System) with Quran-specific adjustments.
    """

    # Arabic → Roman character mapping (SATTS-based)
    CHAR_MAP: dict[str, str] = {
        # Consonants
        "ا": "a",
        "ب": "b",
        "ت": "t",
        "ث": "th",
        "ج": "j",
        "ح": "ḥ",
        "خ": "kh",
        "د": "d",
        "ذ": "dh",
        "ر": "r",
        "ز": "z",
        "س": "s",
        "ش": "sh",
        "ص": "ṣ",
        "ض": "ḍ",
        "ط": "ṭ",
        "ظ": "ẓ",
        "ع": "ʿ",
        "غ": "gh",
        "ف": "f",
        "ق": "q",
        "ك": "k",
        "ل": "l",
        "م": "m",
        "ن": "n",
        "ه": "h",
        "و": "w",
        "ي": "y",
        "ء": "'",
        "أ": "a",
        "ؤ": "w",
        "إ": "i",
        "ئ": "y",
        "آ": "a",
        # Special characters
        "ة": "h",  # Ta marbuta → h (pausal form)
        "ى": "a",  # Alif maqsura → a
        "۞": "",  # Rub el Hizb
        "۝": "",  # Ayah marker
        # Diacritics (for transliteration display)
        "َ": "a",  # Fatha
        "ُ": "u",  # Damma
        "ِ": "i",  # Kasra
        "ّ": "",   # Shadda (doubling handled separately)
        "ْ": "",   # Sukun
        "ً": "an",  # Tanwin fatha
        "ٌ": "un",  # Tanwin damma
        "ٍ": "in",  # Tanwin kasra
    }

    # Common Quranic words with special transliteration
    SPECIAL_WORDS: dict[str, str] = {
        "الله": "Allah",
        "الرحمن": "ar-Rahman",
        "الرحيم": "ar-Raheem",
        "بسم": "Bismi",
        "قل": "Qul",
        "هو": "Huwa",
        "محمد": "Muhammad",
        "إبراهيم": "Ibrahim",
        "إسرائيل": "Israel",
        "موسى": "Musa",
        "عيسى": "Isa",
        "جبريل": "Jibreel",
        "ميكائيل": "Mika'eel",
        "إبليس": "Iblees",
        "فرعون": "Fir'awn",
        "قرآن": "Qur'an",
        "الكتاب": "al-Kitab",
        "يوم": "Yawm",
        "رب": "Rabb",
        "نور": "Nur",
        "هدى": "Huda",
        "حق": "Haqq",
        "صبر": "Sabr",
        "شكر": "Shukr",
        "رحمة": "Rahmah",
        "نعمة": "Ni'mah",
    }

    def __init__(self, dataset: Optional[dict] = None):
        """
        Args:
            dataset: Optional dict mapping verse keys to transliterations.
                      e.g., {"1:1": "Bismillah ir-Rahman ir-Raheem", ...}
        """
        self._dataset = dataset or {}

    # ── Public API ──────────────────────────────────────────────────

    def transliterate(
        self, arabic_text: str, verse_key: Optional[str] = None
    ) -> str:
        """Transliterate Arabic text to Roman English.

        Args:
            arabic_text: Arabic text (with or without diacritics).
            verse_key: Optional "surah:ayah" key for dataset lookup.

        Returns:
            Roman English transliteration string.
        """
        if not arabic_text.strip():
            return ""

        # 1. Try dataset lookup first
        if verse_key and verse_key in self._dataset:
            return self._dataset[verse_key]

        # 2. Fall back to rule-based transliteration
        return self._rule_based(arabic_text)

    def set_dataset(self, dataset: dict[str, str]):
        """Set the lookup dataset.

        Args:
            dataset: Dict mapping "surah:ayah" → transliteration string.
        """
        self._dataset = dataset
        logger.info(
            "Transliteration dataset loaded: %d entries.", len(dataset)
        )

    def add_to_dataset(self, verse_key: str, transliteration: str):
        """Add a single verse transliteration to the dataset."""
        self._dataset[verse_key] = transliteration

    # ── Rule-based transliteration ──────────────────────────────────

    def _rule_based(self, text: str) -> str:
        """Convert Arabic text to Roman using character mapping."""
        # Check special words first
        words = text.split()
        result_words = []

        for word in words:
            # Check if entire word has a special mapping
            stripped = word.strip()
            if stripped in self.SPECIAL_WORDS:
                result_words.append(self.SPECIAL_WORDS[stripped])
                continue

            # Character-by-character transliteration
            transliterated = self._transliterate_word(stripped)
            result_words.append(transliterated)

        return " ".join(result_words)

    def _transliterate_word(self, word: str) -> str:
        """Transliterate a single Arabic word."""
        result = []
        shadda = False
        prev_char = ""

        for i, char in enumerate(word):
            if char == "ّ":
                # Shadda — double the previous consonant
                shadda = True
                continue

            mapped = self.CHAR_MAP.get(char, char)

            if mapped and mapped not in {"", "a", "i", "u", "an", "un", "in"}:
                # This is a consonant
                if shadda and result:
                    # Double the last consonant
                    result.append(mapped)
                result.append(mapped)
                shadda = False
                prev_char = mapped
            elif mapped in {"a", "i", "u"} and prev_char:
                # Short vowel after consonant
                if mapped == "a":
                    result.append("a")
                elif mapped == "i":
                    result.append("i")
                elif mapped == "u":
                    result.append("u")
                shadda = False
            elif mapped in {"an", "un", "in"}:
                # Tanwin
                result.append(mapped)
                shadda = False

        # Apply common word-final rules
        word_str = "".join(result)

        # Ta marbuta (ة) → "ah" in pausal form
        if word_str.endswith("h") and len(word_str) > 1:
            # Keep as is (already handled by map)
            pass

        # Apply capitalization rules
        word_str = self._apply_capitalization(word_str)

        return word_str

    @staticmethod
    def _apply_capitalization(word: str) -> str:
        """Apply English capitalization rules."""
        # Capitalize first letter
        if word:
            word = word[0].upper() + word[1:]
        return word

    # ── Utility ─────────────────────────────────────────────────────

    @staticmethod
    def format_verse(
        text: str, verse_key: str, add_bismillah: bool = False
    ) -> str:
        """Format a complete verse transliteration.

        Args:
            text: Transliteration text.
            verse_key: "surah:ayah" for reference.
            add_bismillah: Prepend Basmalah for non-Tawbah surahs.

        Returns:
            Formatted transliteration string.
        """
        surah_str = f"Surah {verse_key.split(':')[0]}"
        ayah_str = f"Ayah {verse_key.split(':')[1]}"
        return f"{text} — {surah_str}:{ayah_str}"
