"""Service for querying the Quran dataset from the database."""

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.quran import Verse


class QuranService:
    """High-level data access for verses, translations, and search."""

    def __init__(self, db: Session):
        self.db = db

    # ── Lookup ──────────────────────────────────────────────────────

    def get_verse(
        self, surah: int, ayah: int, language: str = "english"
    ) -> Optional[dict]:
        """Fetch a single verse by surah + ayah."""
        verse = (
            self.db.query(Verse)
            .filter(Verse.surah == surah, Verse.ayah == ayah)
            .first()
        )
        return verse.to_dict(language) if verse else None

    def get_verses_by_surah(
        self, surah: int, language: str = "english"
    ) -> list[dict]:
        """Fetch all ayahs in a given surah."""
        verses = (
            self.db.query(Verse)
            .filter(Verse.surah == surah)
            .order_by(Verse.ayah)
            .all()
        )
        return [v.to_dict(language) for v in verses]

    # ── Stats ───────────────────────────────────────────────────────

    @property
    def total_verses(self) -> int:
        return self.db.query(func.count(Verse.id)).scalar() or 0

    # ── Fuzzy-match helpers ─────────────────────────────────────────

    def get_all_normalized_texts(self) -> list[tuple[int, int, str]]:
        """Return (surah, ayah, normalized_text) for every verse."""
        rows = self.db.query(Verse.surah, Verse.ayah, Verse.normalized).all()
        return [(r.surah, r.ayah, r.normalized) for r in rows]

    def get_verse_by_normalized(
        self, normalized: str, language: str = "english"
    ) -> Optional[dict]:
        """Look up verse by exact normalized text."""
        verse = (
            self.db.query(Verse)
            .filter(Verse.normalized == normalized)
            .first()
        )
        return verse.to_dict(language) if verse else None

    # ── Search ──────────────────────────────────────────────────────

    def search_translation(
        self, query: str, language: str = "english", limit: int = 10
    ) -> list[dict]:
        """Search in translation text (case-insensitive LIKE)."""
        translation_col = getattr(Verse, language, Verse.english)
        verses = (
            self.db.query(Verse)
            .filter(translation_col.ilike(f"%{query}%"))
            .limit(limit)
            .all()
        )
        return [v.to_dict(language) for v in verses]

    # ── Batch (for preloading / offline sync) ───────────────────────

    def get_all_verses(self, language: str = "english") -> list[dict]:
        """Return the full dataset (slow for large DB — use with care)."""
        verses = self.db.query(Verse).order_by(Verse.surah, Verse.ayah).all()
        return [v.to_dict(language) for v in verses]
