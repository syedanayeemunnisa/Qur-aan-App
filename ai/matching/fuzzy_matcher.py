"""Fuzzy string matching engine for Quran verse identification.

This is the core matching component that bridges OCR output
with the canonical Quran dataset using multiple string
similarity algorithms.
"""

from __future__ import annotations

import logging
from typing import Optional

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """Fuzzy match normalized Arabic text against the Quran dataset.

    Supports:
      - Exact matching
      - Partial / substring matching
      - Token-set ratio (best for OCR errors)
      - Partial-ratio (best for partial verse capture)
      - Weighted combination of scorers
    """

    def __init__(
        self,
        dataset: list[tuple[int, int, str]],
        min_score: int = 60,
    ):
        """
        Args:
            dataset: List of (surah, ayah, normalized_text) tuples.
            min_score: Minimum similarity score (0–100) to consider a match.
        """
        self._index = dataset
        self._texts = [entry[2] for entry in dataset]
        self.min_score = min_score

    # ── Primary matching ────────────────────────────────────────────

    def find_best(
        self, query: str, strategy: str = "auto"
    ) -> Optional[dict]:
        """Return the best-matching verse.

        Args:
            query: Normalized Arabic text to match.
            strategy: 'auto' | 'exact' | 'partial' | 'token_set' | 'weighted'

        Returns:
            {surah, ayah, score, text, method} or None.
        """
        if not query.strip():
            return None

        if strategy == "auto":
            return self._auto_match(query)
        elif strategy == "exact":
            return self._exact_match(query)
        elif strategy == "partial":
            return self._partial_match(query)
        elif strategy == "token_set":
            return self._token_set_match(query)
        elif strategy == "weighted":
            return self._weighted_match(query)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def find_top_k(
        self, query: str, k: int = 5
    ) -> list[dict]:
        """Return the top-k matching verses."""
        if not query.strip():
            return []

        results = process.extract(
            query,
            self._texts,
            scorer=fuzz.token_set_ratio,
            limit=k,
        )

        matches = []
        for text, score, idx in results:
            if score >= self.min_score:
                surah, ayah, _ = self._index[idx]
                matches.append(
                    {
                        "surah": surah,
                        "ayah": ayah,
                        "score": round(score / 100.0, 4),
                        "method": "token_set",
                    }
                )
        return matches

    # ── Matching strategies ─────────────────────────────────────────

    def _auto_match(self, query: str) -> Optional[dict]:
        """Try strategies from most to least restrictive."""
        # 1. Exact
        result = self._exact_match(query)
        if result:
            return result

        # 2. Partial (query is substring)
        result = self._partial_match(query)
        if result and result["score"] >= 0.85:
            return result

        # 3. Token-set (best for OCR errors)
        result = self._token_set_match(query)
        if result and result["score"] >= self.min_score / 100.0:
            return result

        # 4. Weighted combination
        result = self._weighted_match(query)
        if result and result["score"] >= 0.5:
            return result

        return None

    def _exact_match(self, query: str) -> Optional[dict]:
        for surah, ayah, text in self._index:
            if text == query:
                return {
                    "surah": surah,
                    "ayah": ayah,
                    "score": 1.0,
                    "method": "exact",
                }
        return None

    def _partial_match(self, query: str) -> Optional[dict]:
        best_score = 0.0
        best_result = None

        for surah, ayah, text in self._index:
            # Check if one is substring of the other
            if query in text:
                score = len(query) / max(len(text), 1)
            elif text in query:
                score = len(text) / max(len(query), 1)
            else:
                continue

            if score > best_score:
                best_score = score
                best_result = {
                    "surah": surah,
                    "ayah": ayah,
                    "score": round(min(score, 1.0), 4),
                    "method": "partial",
                }

        return best_result

    def _token_set_match(self, query: str) -> Optional[dict]:
        best = process.extractOne(
            query, self._texts, scorer=fuzz.token_set_ratio
        )
        if not best:
            return None

        text, score, idx = best
        if score < self.min_score:
            return None

        surah, ayah, _ = self._index[idx]
        return {
            "surah": surah,
            "ayah": ayah,
            "score": round(score / 100.0, 4),
            "method": "token_set",
        }

    def _weighted_match(self, query: str) -> Optional[dict]:
        """Combine token-set, partial, and token-sort ratios."""
        best_score = 0.0
        best_result = None

        for surah, ayah, text in self._index:
            ts = fuzz.token_set_ratio(query, text) / 100.0
            pr = fuzz.partial_ratio(query, text) / 100.0
            to = fuzz.token_sort_ratio(query, text) / 100.0

            # Weighted: token_set gets highest weight
            combined = ts * 0.5 + pr * 0.3 + to * 0.2

            if combined > best_score:
                best_score = combined
                best_result = {
                    "surah": surah,
                    "ayah": ayah,
                    "score": round(combined, 4),
                    "method": "weighted",
                }

        return best_result

    # ── Utility ─────────────────────────────────────────────────────

    def match_line_confidence(
        self, query: str, surah: int, ayah: int
    ) -> float:
        """Check how well query matches a specific verse."""
        target = None
        for s, a, text in self._index:
            if s == surah and a == ayah:
                target = text
                break

        if not target:
            return 0.0

        ts = fuzz.token_set_ratio(query, target) / 100.0
        pr = fuzz.partial_ratio(query, target) / 100.0
        return round(ts * 0.6 + pr * 0.4, 4)

    @property
    def size(self) -> int:
        return len(self._index)
