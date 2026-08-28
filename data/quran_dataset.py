"""Quran dataset handler — load, validate, and query the dataset.

This module provides tools to:
  - Load the Quran JSON dataset
  - Validate dataset integrity
  - Export to various formats (JSON, SQLite, CSV)
  - Generate statistics
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


class QuranDataset:
    """Handler for the Quran dataset with validation and export."""

    # Known surah names (English)
    SURAH_NAMES = [
        "Al-Fatiha", "Al-Baqarah", "Aal-E-Imran", "An-Nisa'", "Al-Ma'idah",
        "Al-An'am", "Al-A'raf", "Al-Anfal", "At-Tawbah", "Yunus",
        "Hud", "Yusuf", "Ar-Ra'd", "Ibrahim", "Al-Hijr",
        "An-Nahl", "Al-Isra'", "Al-Kahf", "Maryam", "Ta-Ha",
        "Al-Anbiya'", "Al-Hajj", "Al-Mu'minun", "An-Nur", "Al-Furqan",
        "Ash-Shu'ara'", "An-Naml", "Al-Qasas", "Al-'Ankabut", "Ar-Rum",
        "Luqman", "As-Sajdah", "Al-Ahzab", "Saba'", "Fatir",
        "Ya-Sin", "As-Saffat", "Sad", "Az-Zumar", "Ghafir",
        "Fussilat", "Ash-Shura", "Az-Zukhruf", "Ad-Dukhan", "Al-Jathiya",
        "Al-Ahqaf", "Muhammad", "Al-Fath", "Al-Hujurat", "Qaf",
        "Adh-Dhariyat", "At-Tur", "An-Najm", "Al-Qamar", "Ar-Rahman",
        "Al-Waqi'ah", "Al-Hadid", "Al-Mujadilah", "Al-Hashr", "Al-Mumtahanah",
        "As-Saff", "Al-Jumu'ah", "Al-Munafiqun", "At-Taghabun", "At-Talaq",
        "At-Tahrim", "Al-Mulk", "Al-Qalam", "Al-Haqqah", "Al-Ma'arij",
        "Nuh", "Al-Jinn", "Al-Muzzammil", "Al-Muddaththir", "Al-Qiyamah",
        "Al-Insan", "Al-Mursalat", "An-Naba'", "An-Nazi'at", "'Abasa",
        "At-Takwir", "Al-Infitar", "Al-Mutaffifin", "Al-Inshiqaq", "Al-Buruj",
        "At-Tariq", "Al-A'la", "Al-Ghashiyah", "Al-Fajr", "Al-Balad",
        "Ash-Shams", "Al-Layl", "Ad-Duhaa", "Ash-Sharh", "At-Tin",
        "Al-'Alaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah", "Al-'Adiyat",
        "Al-Qari'ah", "At-Takathur", "Al-'Asr", "Al-Humazah", "Al-Fil",
        "Quraysh", "Al-Ma'un", "Al-Kawthar", "Al-Kafirun", "An-Nasr",
        "Al-Masad", "Al-Ikhlas", "Al-Falaq", "An-Nas",
    ]

    def __init__(self, json_path: Optional[Path] = None):
        self.json_path = json_path or (
            Path(__file__).resolve().parent / "quran_dataset.json"
        )
        self._data: list[dict] = []
        self._loaded = False

    # ── Loading ─────────────────────────────────────────────────────

    def load(self) -> list[dict]:
        """Load the JSON dataset into memory."""
        if not self.json_path.exists():
            logger.warning(
                "Dataset not found at %s. Run prepare_dataset.py first.",
                self.json_path,
            )
            return []

        with open(self.json_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        self._loaded = True
        logger.info("Loaded %d verses from %s", len(self._data), self.json_path)
        return self._data

    @property
    def data(self) -> list[dict]:
        if not self._loaded:
            self.load()
        return self._data

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── Iteration ───────────────────────────────────────────────────

    def iter_verses(self) -> Iterator[dict]:
        """Yield each verse record."""
        yield from self.data

    def get_verse(self, surah: int, ayah: int) -> Optional[dict]:
        """Get a specific verse by surah + ayah."""
        for v in self.data:
            if v["surah"] == surah and v["ayah"] == ayah:
                return v
        return None

    # ── Validation ──────────────────────────────────────────────────

    def validate(self) -> list[str]:
        """Run integrity checks and return a list of issues (empty = OK)."""
        issues = []

        if not self.data:
            issues.append("Dataset is empty.")

        required_fields = {
            "surah", "ayah", "arabic", "normalized",
            "english", "roman",
        }

        for i, v in enumerate(self.data):
            # Check required fields
            missing = required_fields - set(v.keys())
            if missing:
                issues.append(
                    f"Verse {i}: missing fields: {missing}"
                )

            # Validate types
            if not isinstance(v.get("surah"), int) or v["surah"] < 1:
                issues.append(
                    f"Verse {i}: invalid surah: {v.get('surah')}"
                )
            if not isinstance(v.get("ayah"), int) or v["ayah"] < 1:
                issues.append(
                    f"Verse {i}: invalid ayah: {v.get('ayah')}"
                )

            # Validate Arabic text has Arabic characters
            arabic = v.get("arabic", "")
            if not any("\u0600" <= c <= "\u06FF" for c in arabic):
                issues.append(
                    f"Verse {i}: Arabic text missing Arabic chars: {arabic[:50]}"
                )

            # Check normalized isn't empty
            if not v.get("normalized", "").strip():
                issues.append(f"Verse {i}: normalized text is empty.")

        if not issues:
            logger.info(
                "Validation passed — %d verses OK.", len(self.data)
            )
        else:
            logger.warning(
                "Validation found %d issues.", len(issues)
            )

        return issues

    # ── Statistics ──────────────────────────────────────────────────

    @property
    def total_verses(self) -> int:
        return len(self.data)

    @property
    def total_surahs(self) -> int:
        surahs = set(v["surah"] for v in self.data)
        return len(surahs)

    def verses_per_surah(self) -> dict[int, int]:
        """Return {surah_number: verse_count}."""
        counts: dict[int, int] = {}
        for v in self.data:
            counts[v["surah"]] = counts.get(v["surah"], 0) + 1
        return dict(sorted(counts.items()))

    def surah_name(self, surah: int) -> str:
        """Get English name of a surah (1-indexed)."""
        if 1 <= surah <= 114:
            return self.SURAH_NAMES[surah - 1]
        return f"Surah {surah}"

    # ── Export ──────────────────────────────────────────────────────

    def export_sqlite(self, db_path: Path):
        """Export dataset to SQLite."""
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                surah INTEGER NOT NULL,
                ayah INTEGER NOT NULL,
                verse_key TEXT UNIQUE NOT NULL,
                arabic TEXT NOT NULL,
                normalized TEXT NOT NULL,
                english TEXT,
                urdu TEXT,
                hindi TEXT,
                telugu TEXT,
                roman TEXT,
                juz INTEGER,
                page INTEGER,
                sajda INTEGER
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_surah_ayah ON verses(surah, ayah)")

        for v in self.data:
            cursor.execute(
                """INSERT OR REPLACE INTO verses
                (surah, ayah, verse_key, arabic, normalized,
                 english, urdu, hindi, telugu, roman,
                 juz, page, sajda)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    v["surah"], v["ayah"],
                    f"{v['surah']}:{v['ayah']}",
                    v["arabic"], v["normalized"],
                    v.get("english"), v.get("urdu"),
                    v.get("hindi"), v.get("telugu"),
                    v.get("roman"),
                    v.get("juz"), v.get("page"),
                    v.get("sajda"),
                ),
            )

        conn.commit()
        conn.close()
        logger.info(
            "Exported %d verses to SQLite: %s", len(self.data), db_path
        )

    def export_csv(self, csv_path: Path, fields: Optional[list[str]] = None):
        """Export dataset to CSV."""
        import csv

        if fields is None:
            fields = [
                "surah", "ayah", "arabic", "english",
                "urdu", "hindi", "telugu", "roman",
            ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for v in self.data:
                writer.writerow({k: v.get(k, "") for k in fields})

        logger.info(
            "Exported %d verses to CSV: %s", len(self.data), csv_path
        )
