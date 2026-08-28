"""Pydantic schemas for request / response validation."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ── Request schemas ─────────────────────────────────────────────────


class DetectRequest(BaseModel):
    """Payload sent from the Flutter app with OCR result or image data."""

    image_base64: Optional[str] = Field(
        None, description="Base64-encoded camera frame"
    )
    ocr_text: Optional[str] = Field(
        None, description="Pre-extracted Arabic text (skip OCR)"
    )
    language: str = Field(
        "english", description="Target translation language"
    )


class SearchRequest(BaseModel):
    """Search the Quran dataset."""

    query: str = Field(..., min_length=1, description="Search text")
    language: str = Field("english", description="Search in translation")
    limit: int = Field(10, ge=1, le=100)


# ── Response schemas ────────────────────────────────────────────────


class VerseResponse(BaseModel):
    """A single matched verse with translations."""

    surah: int
    ayah: int
    verse_key: str
    arabic: str
    normalized: str
    translation: str
    translation_language: str
    roman: Optional[str] = None
    juz: Optional[int] = None
    page: Optional[int] = None
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Matching confidence score"
    )


class DetectResponse(BaseModel):
    """Result of OCR + verse identification."""

    success: bool
    detected_text: Optional[str] = None
    matched_verse: Optional[VerseResponse] = None
    alternatives: list[VerseResponse] = Field(default_factory=list)
    language: str = "english"
    error: Optional[str] = None


class SearchResponse(BaseModel):
    """Search results."""

    results: list[VerseResponse]
    total: int
    query: str


class LanguageInfo(BaseModel):
    """Supported language metadata."""

    code: str
    name: str
    is_available: bool


class LanguagesResponse(BaseModel):
    """List of available languages."""

    languages: list[LanguageInfo]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str = "1.0.0"
    ocr_loaded: bool
    dataset_size: int
    embeddings_enabled: bool
