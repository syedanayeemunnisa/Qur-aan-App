"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "quran.db"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# CORS — allow Flutter app connections
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "*",  # Relax for dev; lock down in production
)

# OCR
OCR_ENGINE = os.getenv("OCR_ENGINE", "easyocr")  # "easyocr" | "tesseract"
OCR_LANG = os.getenv("OCR_LANG", "ar")
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
EASYOCR_GPU = os.getenv("EASYOCR_GPU", "false").lower() == "true"

# Matching
MATCH_CONFIDENCE_THRESHOLD = float(os.getenv("MATCH_CONFIDENCE", "0.75"))
FUZZY_MATCH_MIN_SCORE = int(os.getenv("FUZZY_MATCH_MIN", "60"))

# Embeddings (optional — requires sentence-transformers)
EMBEDDINGS_ENABLED = os.getenv("EMBEDDINGS_ENABLED", "false").lower() == "true"
EMBEDDINGS_MODEL = os.getenv(
    "EMBEDDINGS_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Cache
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour

# Supported languages
SUPPORTED_LANGUAGES = {
    "english": "English (Muhsin Khan & Hilali)",
    "urdu": "Urdu (Muhammad Junagarhi)",
    "hindi": "Hindi (Muhammad Farooq Khan)",
    "telugu": "Telugu (Muhammad Aziz Ur Rehman)",
    "roman": "Roman English (Transliteration)",
}

DEFAULT_LANGUAGE = "english"
