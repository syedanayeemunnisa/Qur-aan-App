"""SQLAlchemy model for the Quran dataset."""

from sqlalchemy import Column, Integer, String, Text, Float, Index

from database import Base


class Verse(Base):
    """Represents a single Quranic verse (ayah) with all translations."""

    __tablename__ = "verses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    surah = Column(Integer, nullable=False, index=True)
    ayah = Column(Integer, nullable=False)
    juz = Column(Integer, nullable=True)
    page = Column(Integer, nullable=True)

    # Arabic
    arabic = Column(Text, nullable=False)  # With diacritics (tashkeel)
    normalized = Column(Text, nullable=False, index=True)  # Without diacritics

    # Translations
    english = Column(Text, nullable=True)
    urdu = Column(Text, nullable=True)
    hindi = Column(Text, nullable=True)
    telugu = Column(Text, nullable=True)

    # Transliteration
    roman = Column(Text, nullable=True)

    # Metadata
    sajda = Column(Integer, nullable=True)  # Prostration type, if any
    verse_key = Column(
        String(10), unique=True, nullable=False
    )  # e.g. "1:1"

    # Embedding (optional — for semantic search)
    embedding = Column(Float, nullable=True)

    __table_args__ = (
        Index("idx_surah_ayah", "surah", "ayah", unique=True),
        Index("idx_normalized", "normalized"),
    )

    def to_dict(self, language: str = "english") -> dict:
        """Serialize verse with the requested translation language."""
        translation_map = {
            "english": self.english,
            "urdu": self.urdu,
            "hindi": self.hindi,
            "telugu": self.telugu,
        }
        if language == "roman":
            translation = self.roman or ""
        else:
            translation = translation_map.get(language, self.english)

        return {
            "surah": self.surah,
            "ayah": self.ayah,
            "verse_key": self.verse_key,
            "arabic": self.arabic,
            "normalized": self.normalized,
            "translation": translation,
            "translation_language": language,
            "roman": self.roman,
            "juz": self.juz,
            "page": self.page,
            "sajda": self.sajda,
        }

    def __repr__(self):
        return f"<Verse {self.verse_key}: {self.arabic[:50]}…>"
