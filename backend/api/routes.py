"""FastAPI router — all REST endpoints for the Quran translation app."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from database import get_db
from schemas import (
    DetectRequest,
    DetectResponse,
    VerseResponse,
    SearchRequest,
    SearchResponse,
    LanguagesResponse,
    LanguageInfo,
    HealthResponse,
)
from services.quran_service import QuranService
from services.ocr_service import OcrService
from services.matching_engine import MatchingEngine
from ai.normalization.text_normalizer import ArabicTextNormalizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

# Global service instances
ocr_service: OcrService | None = None
normalizer: ArabicTextNormalizer | None = None


def get_services():
    """Dependency that wires up services for each request."""
    return {
        "ocr": ocr_service,
        "normalizer": normalizer,
    }


# ── POST /detect ────────────────────────────────────────────────────


@router.post("/detect", response_model=DetectResponse)
def detect_verse(
    req: DetectRequest,
    db: Session = Depends(get_db),
    services: dict = Depends(get_services),
):
    """OCR → Normalize → Match → Return verse.

    Accepts either a base64 image or pre-extracted OCR text.
    """
    svc = QuranService(db)
    engine = MatchingEngine(svc)
    normalizer = services["normalizer"]
    ocr = services["ocr"]

    try:
        # ── Step 1: Extract text ────────────────────────────────
        raw_text = None
        boxes = None

        if req.ocr_text:
            raw_text = req.ocr_text
        elif req.image_base64 and ocr and ocr.is_loaded():
            raw_text, boxes = ocr.extract_text_with_boxes(
                req.image_base64
            )
        elif req.image_base64 and (not ocr or not ocr.is_loaded()):
            # OCR engine is unavailable — return a clear, actionable error
            # so the client can fall back to text input.
            return DetectResponse(
                success=False,
                error=(
                    "Camera OCR is not available on this server. "
                    "Please type the Arabic text in the text box and "
                    "tap Detect Verse instead."
                ),
            )
        else:
            raise HTTPException(
                400, "Provide either 'ocr_text' or 'image_base64'."
            )

        if not raw_text or not raw_text.strip():
            return DetectResponse(
                success=False,
                error="No Arabic text detected in the image.",
            )

        # ── Step 2: Normalize ───────────────────────────────────
        if normalizer:
            normalized = normalizer.normalize(raw_text)
        else:
            normalized = raw_text

        # ── Step 3: Match ────────────────────────────────────────
        lang = req.language if req.language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        best_match, alternatives = engine.identify(normalized, lang)

        if not best_match:
            return DetectResponse(
                success=False,
                detected_text=raw_text[:300],
                error="Could not match with the Quran dataset. Try re-scanning.",
            )

        # ── Step 4: Build response ──────────────────────────────
        verse_resp = VerseResponse(
            surah=best_match["surah"],
            ayah=best_match["ayah"],
            verse_key=best_match["verse_key"],
            arabic=best_match["arabic"],
            normalized=best_match["normalized"],
            translation=best_match["translation"],
            translation_language=best_match["translation_language"],
            roman=best_match.get("roman"),
            juz=best_match.get("juz"),
            page=best_match.get("page"),
            confidence=best_match.get("confidence", 0.9),
        )

        alt_responses = [
            VerseResponse(
                surah=a["surah"],
                ayah=a["ayah"],
                verse_key=a["verse_key"],
                arabic=a["arabic"],
                normalized=a["normalized"],
                translation=a["translation"],
                translation_language=a["translation_language"],
                roman=a.get("roman"),
                confidence=a.get("confidence", 0.5),
            )
            for a in alternatives
        ]

        return DetectResponse(
            success=True,
            detected_text=raw_text[:300],
            matched_verse=verse_resp,
            alternatives=alt_responses,
            language=lang,
        )

    except Exception as e:
        logger.exception("Detection failed")
        return DetectResponse(
            success=False,
            error=f"Detection error: {str(e)}",
        )


# ── GET /verse/{surah}/{ayah} ───────────────────────────────────────


@router.get("/verse/{surah}/{ayah}", response_model=VerseResponse)
def get_verse(
    surah: int,
    ayah: int,
    language: str = DEFAULT_LANGUAGE,
    db: Session = Depends(get_db),
):
    """Fetch a specific verse by surah + ayah."""
    svc = QuranService(db)
    verse = svc.get_verse(surah, ayah, language)
    if not verse:
        raise HTTPException(404, f"Verse {surah}:{ayah} not found.")
    return VerseResponse(
        surah=verse["surah"],
        ayah=verse["ayah"],
        verse_key=verse["verse_key"],
        arabic=verse["arabic"],
        normalized=verse["normalized"],
        translation=verse["translation"],
        translation_language=verse["translation_language"],
        roman=verse.get("roman"),
        juz=verse.get("juz"),
        page=verse.get("page"),
        confidence=1.0,
    )


# ── GET /search ─────────────────────────────────────────────────────


@router.get("/search", response_model=SearchResponse)
def search_verses(
    q: str,
    language: str = DEFAULT_LANGUAGE,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Search the Quran dataset by translation text."""
    svc = QuranService(db)
    results = svc.search_translation(q, language, limit)
    verses = [
        VerseResponse(
            surah=r["surah"],
            ayah=r["ayah"],
            verse_key=r["verse_key"],
            arabic=r["arabic"],
            normalized=r["normalized"],
            translation=r["translation"],
            translation_language=r["translation_language"],
            roman=r.get("roman"),
            confidence=1.0,
        )
        for r in results
    ]
    return SearchResponse(results=verses, total=len(verses), query=q)


# ── GET /languages ──────────────────────────────────────────────────


@router.get("/languages", response_model=LanguagesResponse)
def list_languages():
    """Return supported translation languages."""
    codes = SUPPORTED_LANGUAGES
    langs = [
        LanguageInfo(code=code, name=name, is_available=True)
        for code, name in codes.items()
    ]
    return LanguagesResponse(languages=langs)


# ── GET /health ─────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
def health_check(
    db: Session = Depends(get_db),
    services: dict = Depends(get_services),
):
    """Health check endpoint."""
    svc = QuranService(db)
    ocr = services["ocr"]

    return HealthResponse(
        status="ok",
        ocr_loaded=ocr.is_loaded() if ocr else False,
        dataset_size=svc.total_verses,
        embeddings_enabled=False,
    )
