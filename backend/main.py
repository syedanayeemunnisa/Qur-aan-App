"""FastAPI application entry point for the Quran Translation API."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path so ai/ and data/ modules are importable
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from config import CORS_ORIGINS, HOST, PORT, DEBUG
from database import engine, Base

# Import all models so they are registered with SQLAlchemy
import models.quran  # noqa: F401

import api.routes
from api.routes import router
from services.ocr_service import OcrService
from ai.normalization.text_normalizer import ArabicTextNormalizer

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO if DEBUG else logging.WARNING,
    format="%(asctime)s | %(name)-25s | %(levelname)-5s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Lifespan (replaces deprecated on_event) ────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the app."""
    # ── Startup ──
    logger.info("Creating database tables …")
    Base.metadata.create_all(bind=engine)

    logger.info("Initialising OCR service …")
    try:
        api.routes.ocr_service = OcrService()
    except Exception as e:
        logger.warning("OCR service init failed (will lazy-load): %s", e)
        api.routes.ocr_service = None

    logger.info("Initialising Arabic text normalizer …")
    try:
        api.routes.normalizer = ArabicTextNormalizer()
    except Exception as e:
        logger.warning("Normalizer init failed: %s", e)
        api.routes.normalizer = None

    logger.info("Startup complete. Ready to serve.")

    yield  # ── App is running ──

    # ── Shutdown ──
    logger.info("Shutting down …")


# ── App factory ─────────────────────────────────────────────────────

app = FastAPI(
    title="Quran Translation API",
    description="Real-time Quran verse detection and translation service.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(",") if CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register routes ────────────────────────────────────────────────
app.include_router(router)


# ── Web demo (served at /app) ───────────────────────────────────────
@app.get("/")
def serve_demo():
    """Serve the web-based Quran app demo."""
    return FileResponse(
        Path(__file__).resolve().parent / "templates" / "index.html"
    )


# ── Entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info",
    )
