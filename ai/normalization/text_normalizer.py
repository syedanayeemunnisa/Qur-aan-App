"""Arabic text normalizer — strips diacritics, unifies characters, cleans OCR noise.

This is *critical* for the matching pipeline: OCR output will contain
extra/missing diacritics, spacing errors, and character confusion.
Normalization bridges the gap between raw OCR text and the clean
Quran dataset.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


class ArabicTextNormalizer:
    """Normalize Arabic text for fuzzy matching against the Quran dataset.

    Key transformations:
    - Remove tashkeel (diacritics): fatha, damma, kasra, sukun, shadda, etc.
    - Unify variant forms of the same letter (e.g., ا vs أ vs إ vs آ → ا)
    - Remove tatweel (kashida) elongation characters
    - Remove non-Arabic / control characters
    - Normalise spacing
    """

    # Unicode ranges
    ARABIC_CHARS = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
    ARABIC_DIACRITICS = re.compile(
        "[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u08D0-\u08FF]"
    )
    TATWEEL = re.compile(r"[\u0640]")  # Kashida
    NON_ARABIC = re.compile(r"[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s]")

    # Letter unification maps
    ALEF_MAP = str.maketrans(
        "آأإٱٲٳ",
        "اااااا",  # All alef variants → bare alef
    )

    TA_MARBUTA_MAP = str.maketrans(
        "ةۀ",
        "هه",  # Ta marbuta → ha
    )

    YEH_MAP = str.maketrans(
        "ىٰٸ",
        "ييي",  # Alif maqsura / superscript alef → yeh
    )

    WAV_MAP = str.maketrans(
        "ؤۥۄ",
        "ووو",  # Waw with hamza → bare waw
    )

    def __init__(self, keep_bismillah: bool = True):
        self.keep_bismillah = keep_bismillah

    # ── Public API ──────────────────────────────────────────────────

    def normalize(self, text: str) -> str:
        """Normalize Arabic text for matching.

        Returns a cleaned, diacritic-free string that can be compared
        against the 'normalized' field in the Quran dataset.
        NOTE: Does NOT strip Bismillah — it's a valid verse (1:1, 27:30).
        """
        if not text or not text.strip():
            return ""

        text = self._remove_diacritics(text)
        text = self._remove_tatweel(text)
        text = self._unify_letters(text)
        text = self._remove_non_arabic(text)
        text = self._quran_normalize(text)
        text = self._normalize_whitespace(text)

        return text.strip()

    def normalize_light(self, text: str) -> str:
        """Light normalization — keep diacritics but clean noise.

        Useful for display purposes.
        """
        text = self._remove_tatweel(text)
        text = self._remove_non_arabic(text)
        text = self._normalize_whitespace(text)
        return text.strip()

    # ── Internal steps ──────────────────────────────────────────────

    @staticmethod
    def _remove_diacritics(text: str) -> str:
        """Strip all Arabic diacritical marks (tashkeel)."""
        return ArabicTextNormalizer.ARABIC_DIACRITICS.sub("", text)

    @staticmethod
    def _remove_tatweel(text: str) -> str:
        """Remove tatweel / kashida elongation characters."""
        return ArabicTextNormalizer.TATWEEL.sub("", text)

    @staticmethod
    def _unify_letters(text: str) -> str:
        """Unify variant letter forms for robust matching."""
        text = text.translate(ArabicTextNormalizer.ALEF_MAP)
        text = text.translate(ArabicTextNormalizer.TA_MARBUTA_MAP)
        text = text.translate(ArabicTextNormalizer.YEH_MAP)
        text = text.translate(ArabicTextNormalizer.WAV_MAP)
        return text

    @staticmethod
    def _remove_non_arabic(text: str) -> str:
        """Strip any non-Arabic / non-space characters."""
        return ArabicTextNormalizer.NON_ARABIC.sub("", text)

    @staticmethod
    def _quran_normalize(text: str) -> str:
        """Quran-specific normalization that the generic pass misses.

        In the Quran dataset, the definite article uses ALEF WASLA (ٱ)
        instead of regular ALEF (ا).  Replace "ال" at word-start with "ٱل"
        so user input matches the stored form.
        """
        # "ال" at the start of a word → "ٱل" (alef wasla)
        text = re.sub(r'(?<=\s)ال', 'ٱل', text)
        # Also handle text that starts with "ال"
        if text.startswith('ال'):
            text = 'ٱل' + text[2:]
        return text

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Collapse multiple spaces and strip."""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _strip_bismillah(text: str) -> str:
        """Remove Basmalah if it appears at the start (common OCR artefact)."""
        bismillah = "بسم الله الرحمن الرحيم"
        normalized_bismillah = "بسم الله الرحمن الرحيم"

        if text.startswith(normalized_bismillah):
            text = text[len(normalized_bismillah):].strip()
        elif text.startswith(bismillah):
            text = text[len(bismillah):].strip()
        return text

    # ── OCR-specific cleaning ───────────────────────────────────────

    @staticmethod
    def clean_ocr_artefacts(text: str) -> str:
        """Remove common OCR insertion errors."""
        # Remove stray brackets, numbers, Latin chars
        text = re.sub(r"[A-Za-z0-9\[\](){}<>\"\'\\|/]", "", text)
        # Remove repeated isolated characters (noise)
        text = re.sub(r"(.)\1{3,}", r"\1", text)
        # Remove leading/trailing punctuation
        text = re.sub(r"^[\s,.;:!؟،]+|[\s,.;:!؟،]+$", "", text)
        return text
