"""Matching engine — matches OCR-extracted text to Quran verses."""

from __future__ import annotations

import logging
from typing import Optional

from rapidfuzz import fuzz, process

from config import FUZZY_MATCH_MIN_SCORE, MATCH_CONFIDENCE_THRESHOLD
from services.quran_service import QuranService

logger = logging.getLogger(__name__)


class MatchingEngine:
    """Fuzzy-match OCR output against the Quran dataset.

    Strategy (tried in order):
    1. **exact** — normalized text matches exactly.
    2. **partial** — OCR text is a substring of a known verse.
    3. **fuzzy** — Levenshtein / partial-ratio above threshold.
    4. **multi-line** — split OCR text into individual lines and
       match each independently.
    """

    def __init__(self, quran_service: QuranService):
        self.quran_service = quran_service
        self._index: list[tuple[int, int, str]] | None = None

    # ── Public API ──────────────────────────────────────────────────

    def identify(
        self, ocr_text: str, language: str = "english"
    ) -> tuple[Optional[dict], list[dict]]:
        """Return (best_match, alternatives)."""
        self._ensure_index()

        text = ocr_text.strip()
        if not text:
            return None, []

        best, alternatives = self._try_identify(text)

        if best:
            best_dict = self.quran_service.get_verse(
                best[0], best[1], language
            )
            alt_dicts = [
                self.quran_service.get_verse(s, a, language)
                for s, a, _ in alternatives[:5]
                if (s, a) != (best[0], best[1])
            ]
            if best_dict:
                best_dict["confidence"] = best[2]
            return best_dict, [d for d in alt_dicts if d]
        return None, []

    # ── Internal matching ───────────────────────────────────────────

    def _try_identify(self, text: str) -> tuple[Optional[tuple], list]:
        """Try exact → fuzzy → partial → multi-line strategies.

        Ordering matters: fuzzy is tried before partial so that short
        substring hits (e.g. "الم" found inside a longer verse) do not
        short-circuit the more accurate fuzzy scorer.
        """
        # 1. Exact match on normalized text
        best = self._exact_match(text)
        if best:
            logger.info("Exact match: %s", best)
            return best, []

        # 2. Fuzzy match — best for full/partial verses containing diacritic
        #    differences that normalisation did not eliminate.
        best, alternatives = self._fuzzy_match(text)
        if best and best[2] >= FUZZY_MATCH_MIN_SCORE / 100.0:
            logger.info("Fuzzy match: %s (%d alts)", best, len(alternatives))
            return best, alternatives

        # 3. Partial match — OCR captured part of a verse (substring)
        best = self._partial_match(text)
        if best and best[2] >= MATCH_CONFIDENCE_THRESHOLD:
            logger.info("Partial match: %s", best)
            return best, []

        # 4. Multi-line — try matching individual lines
        best = self._multi_line_match(text)
        if best:
            logger.info("Multi-line match: %s", best)
            return best, []

        return None, []

    def _exact_match(self, text: str) -> Optional[tuple[int, int, float]]:
        for surah, ayah, normalized in self._index:
            if normalized == text:
                return (surah, ayah, 1.0)
        return None

    def _partial_match(self, text: str) -> Optional[tuple[int, int, float]]:
        """Return the best partial match by longest-overlap ratio.

        Uses the Dice coefficient of overlapping n-grams to avoid
        short tokens (e.g. "الم") causing false-positive matches on
        longer input text.
        """
        best: Optional[tuple[int, int, float]] = None
        best_score = 0.0
        for surah, ayah, normalized in self._index:
            if not normalized:
                continue
            # Compute Dice coefficient of shared bigrams
            norm_bigrams = {normalized[i:i+2] for i in range(len(normalized)-1)}
            text_bigrams = {text[i:i+2] for i in range(len(text)-1)}
            if not norm_bigrams or not text_bigrams:
                continue
            intersection = norm_bigrams & text_bigrams
            dice = 2.0 * len(intersection) / (len(norm_bigrams) + len(text_bigrams))
            if dice >= 0.5 and dice > best_score:
                best_score = dice
                best = (surah, ayah, dice)
        return best

    def _fuzzy_match(
        self, text: str
    ) -> tuple[Optional[tuple], list[tuple]]:
        """Use token-set ratio for robust matching."""
        candidates = [
            (s, a, normalized) for s, a, normalized in self._index
        ]
        texts = [c[2] for c in candidates]

        # Token-set ratio is best for OCR errors
        best_match = process.extractOne(
            text, texts, scorer=fuzz.token_set_ratio
        )

        if not best_match:
            return None, []

        best_text, score, idx = best_match
        surah, ayah, _ = candidates[idx]

        # Also return top-5 alternatives
        all_matches = process.extract(
            text, texts, scorer=fuzz.token_set_ratio, limit=6
        )
        alternatives = []
        for alt_text, alt_score, alt_idx in all_matches:
            if alt_idx != idx and alt_score >= FUZZY_MATCH_MIN_SCORE:
                s, a, _ = candidates[alt_idx]
                alternatives.append((s, a, alt_score / 100.0))

        return (surah, ayah, score / 100.0), alternatives

    def _multi_line_match(
        self, text: str
    ) -> Optional[tuple[int, int, float]]:
        """Split OCR text by newlines and match each line independently.

        Uses only single-line strategies (exact → fuzzy → partial) to
        avoid infinite recursion with _try_identify.
        """
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if len(lines) < 2:
            return None  # single-line case is already handled upstream

        for line in lines:
            # 1. Exact
            best = self._exact_match(line)
            if best:
                return best
            # 2. Fuzzy
            best_fuzzy, _ = self._fuzzy_match(line)
            if best_fuzzy and best_fuzzy[2] >= FUZZY_MATCH_MIN_SCORE / 100.0:
                return best_fuzzy
            # 3. Partial
            best_partial = self._partial_match(line)
            if best_partial and best_partial[2] >= MATCH_CONFIDENCE_THRESHOLD:
                return best_partial

        return None

    def _ensure_index(self):
        if self._index is None:
            self._index = self.quran_service.get_all_normalized_texts()
            logger.info(
                "Loaded %d verses into matching index.", len(self._index)
            )
