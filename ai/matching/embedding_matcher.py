"""Semantic embedding matching — for partial verse detection.

Uses sentence-transformers to embed both the OCR query and the
Quran dataset, then finds the closest match via cosine similarity.

This is an *optional* enhancement over fuzzy string matching.
Enable by setting EMBEDDINGS_ENABLED=true in config.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingMatcher:
    """Semantic embedding matching for robust verse identification.

    Benefits over fuzzy matching:
      - Handles severely partial text (e.g., 2–3 words from a long verse)
      - Understands semantic similarity (synonyms / paraphrases won't affect)
      - Resistant to OCR reordering errors

    Requirements:
      pip install sentence-transformers torch
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._dataset_embeddings: Optional[np.ndarray] = None
        self._dataset_index: list[tuple[int, int]] = []  # (surah, ayah)

    # ── Lazy load ──────────────────────────────────────────────────

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s …", self.model_name)
            self._model = SentenceTransformer(
                self.model_name, device=self.device
            )
        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
            raise

    # ── Dataset indexing ────────────────────────────────────────────

    def index_dataset(
        self, verses: list[tuple[int, int, str]]
    ):
        """Compute and store embeddings for the full Quran dataset.

        Args:
            verses: List of (surah, ayah, normalized_text).
        """
        self._load_model()
        texts = [v[2] for v in verses]
        self._dataset_index = [(v[0], v[1]) for v in verses]

        logger.info("Computing embeddings for %d verses …", len(texts))
        self._dataset_embeddings = self._model.encode(
            texts,
            show_progress_bar=True,
            normalize_embeddings=True,  # cosine-ready
        )
        logger.info("Embedding matrix shape: %s", self._dataset_embeddings.shape)

    # ── Matching ────────────────────────────────────────────────────

    def find_best(
        self, query: str, top_k: int = 3, threshold: float = 0.6
    ) -> list[dict]:
        """Find the closest verses by cosine similarity.

        Args:
            query: Normalized Arabic text.
            top_k: Number of candidates to return.
            threshold: Minimum similarity (0–1) to consider a match.

        Returns:
            [{surah, ayah, similarity, text}]
        """
        if self._dataset_embeddings is None:
            logger.warning(
                "Dataset not indexed. Call index_dataset() first."
            )
            return []

        self._load_model()
        query_emb = self._model.encode(
            [query],
            normalize_embeddings=True,
        )

        # Cosine similarity (already normalized)
        sims = query_emb @ self._dataset_embeddings.T
        sims = sims.flatten()

        # Top-k
        top_indices = np.argsort(sims)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score >= threshold:
                surah, ayah = self._dataset_index[idx]
                results.append(
                    {
                        "surah": surah,
                        "ayah": ayah,
                        "similarity": round(score, 4),
                        "method": "embedding",
                    }
                )

        return results

    def find_best_single(
        self, query: str, threshold: float = 0.6
    ) -> Optional[dict]:
        """Return the single best-matching verse, or None."""
        results = self.find_best(query, top_k=1, threshold=threshold)
        return results[0] if results else None

    # ── Persistence ─────────────────────────────────────────────────

    def save_embeddings(self, path: str):
        """Save precomputed embeddings to disk."""
        if self._dataset_embeddings is None:
            logger.warning("No embeddings to save.")
            return

        import pickle

        with open(path, "wb") as f:
            pickle.dump(
                {
                    "embeddings": self._dataset_embeddings,
                    "index": self._dataset_index,
                    "model_name": self.model_name,
                },
                f,
            )
        logger.info("Embeddings saved to %s", path)

    def load_embeddings(self, path: str) -> bool:
        """Load precomputed embeddings from disk."""
        import pickle
        from pathlib import Path

        p = Path(path)
        if not p.exists():
            logger.warning("Embeddings file not found: %s", path)
            return False

        with open(path, "rb") as f:
            data = pickle.load(f)

        self._dataset_embeddings = data["embeddings"]
        self._dataset_index = data["index"]
        logger.info(
            "Loaded %d embeddings from %s",
            len(self._dataset_index),
            path,
        )
        return True
