"""Database engine, session factory, and base model."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

# ── Engine ──────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite needs this
    echo=False,
)


# Enable WAL mode + foreign keys for SQLite at connection time
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ── Session factory ─────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative base ────────────────────────────────────────────────
Base = declarative_base()


# ── Dependency for FastAPI ──────────────────────────────────────────
def get_db():
    """Yield a DB session — use as FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
