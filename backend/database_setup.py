"""Script to create and populate the Quran database.

Usage:
    python database_setup.py            # Build SQLite from bundled JSON
    python database_setup.py --download  # Download dataset first
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import engine, SessionLocal, Base
from models.quran import Verse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_JSON = DATA_DIR / "quran_dataset.json"


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")


def populate_from_json(json_path: Path = DEFAULT_JSON):
    """Load Quran verses from a JSON file into the database."""
    if not json_path.exists():
        logger.error(
            "Dataset file not found at %s.\n"
            "Run `python data/prepare_dataset.py` first.",
            json_path,
        )
        return

    logger.info("Loading dataset from %s …", json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        verses_data = json.load(f)

    db: Session = SessionLocal()
    try:
        existing = db.query(Verse).count()
        if existing > 0:
            logger.info(
                "Database already has %d verses. Skipping insert.", existing
            )
            return

        batch_size = 500
        for i, v in enumerate(verses_data, 1):
            verse = Verse(
                surah=v["surah"],
                ayah=v["ayah"],
                juz=v.get("juz"),
                page=v.get("page"),
                arabic=v["arabic"],
                normalized=v["normalized"],
                english=v.get("english"),
                urdu=v.get("urdu"),
                hindi=v.get("hindi"),
                telugu=v.get("telugu"),
                roman=v.get("roman"),
                sajda=v.get("sajda"),
                verse_key=f"{v['surah']}:{v['ayah']}",
            )
            db.add(verse)

            if i % batch_size == 0:
                db.commit()
                logger.info("Inserted %d / %d verses …", i, len(verses_data))

        db.commit()
        logger.info(
            "Successfully inserted %d verses.", len(verses_data)
        )
    except Exception:
        db.rollback()
        logger.exception("Failed to populate database.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Set up the Quran database."
    )
    parser.add_argument(
        "--json",
        type=str,
        default=str(DEFAULT_JSON),
        help="Path to the Quran dataset JSON file.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the dataset before populating.",
    )
    args = parser.parse_args()

    if args.download:
        from data.prepare_dataset import download_and_prepare

        download_and_prepare()

    create_tables()
    populate_from_json(Path(args.json))
    logger.info("Done. Database is ready at backend/quran.db")


if __name__ == "__main__":
    main()
