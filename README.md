# 📿 Quranic App — Real-Time Quran Translation & Recognition

> **Production-ready MVP** for real-time Arabic Quranic text recognition, translation, and transliteration using mobile camera input.

## 🎯 Architecture Overview

```
┌─────────────────────────┐     ┌──────────────────────────────┐
│    Flutter Mobile App   │◄───►│     FastAPI Backend          │
│  (Camera + Overlay UI)  │     │  (API Gateway + Services)    │
└─────────────────────────┘     └──────────┬───────────────────┘
                                           │
                                    ┌──────┴──────┐
                                    │  AI/ML Layer │
                                    │ (OCR + Match)│
                                    └──────┬──────┘
                                           │
                                    ┌──────┴──────┐
                                    │  SQLite DB   │
                                    │ (Quran Data) │
                                    └─────────────┘
```

## 🚀 Core Pipeline (CRITICAL)

```
Camera Input → OCR (Arabic) → Normalize Text → Fuzzy Match → Identify Verse → Display Translation
```

**NEVER translate OCR output directly.** Always follow the pipeline above for 100% religious accuracy.

## 🧩 Tech Stack

| Component     | Technology                              |
|---------------|-----------------------------------------|
| **Frontend**  | Flutter (Dart) — Camera + Overlay UI    |
| **Backend**   | FastAPI (Python) — API Gateway          |
| **AI/ML**     | Python — EasyOCR + Custom Matching      |
| **Database**  | SQLite — Preloaded Quran Dataset        |
| **OCR**       | EasyOCR (Arabic) / Tesseract fallback   |

## 📁 Project Structure

```
quranic-app/
├── backend/               # FastAPI backend
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration
│   ├── database.py       # DB connection
│   ├── schemas.py        # Pydantic schemas
│   ├── models/           # SQLAlchemy models
│   ├── api/              # API routes
│   └── services/         # Business logic
├── ai/                   # AI/ML layer
│   ├── ocr/             # Arabic OCR pipeline
│   ├── normalization/   # Text cleaning
│   └── matching/        # Verse matching engine
├── data/                 # Quran dataset
│   ├── quran_dataset.py # Dataset handler
│   └── prepare_dataset.py # Data preparation
└── flutter_app/          # Mobile app
    └── lib/             # Dart source
```

## 📦 Dataset Schema

Each verse record contains:
- `surah`: Surah number (1–114)
- `ayah`: Ayah number
- `arabic`: Quranic Arabic with diacritics
- `normalized`: Arabic without diacritics (for matching)
- `english`: Sahih International translation
- `urdu`: Urdu translation
- `hindi`: Hindi translation
- `telugu`: Telugu translation
- `roman`: Roman English transliteration

## 🔧 Setup & Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Dataset Preparation

```bash
cd data
python prepare_dataset.py    # Downloads & builds Quran dataset
python quran_dataset.py      # Verify dataset integrity
```

### Flutter App

```bash
cd flutter_app
flutter pub get
flutter run
```

## 🔌 API Endpoints

| Method | Endpoint                     | Description                    |
|--------|------------------------------|--------------------------------|
| POST   | `/api/v1/detect`            | OCR + verse identification     |
| GET    | `/api/v1/verse/{surah}/{ayah}` | Get verse by reference      |
| GET    | `/api/v1/search?q=...`      | Search verses                  |
| GET    | `/api/v1/languages`         | Available languages            |
| POST   | `/api/v1/health`            | Health check                   |

## ⚠️ Religious Integrity

This app prioritizes **100% Quranic accuracy**:
- No direct translation of OCR output
- Every displayed verse is verified against the authentic Quran dataset
- Fuzzy matching ensures correct Surah + Ayah identification
- Multiple translation sources for cross-verification

## 📜 License

MIT — Free for educational and non-commercial use.
Quranic data is public domain.
