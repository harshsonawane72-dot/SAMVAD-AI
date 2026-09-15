import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Anchor SQLite database path to backend/samvad.db
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "samvad.db"
DEFAULT_SQLITE_URL = f"sqlite:///{DB_FILE.as_posix()}"
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_SQLITE_URL)

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_columns():
    """Safely migrate SQLite table to include optional assessment columns if missing."""
    import sqlite3
    try:
        conn = sqlite3.connect(str(DB_FILE))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(cases)")
        columns = [row[1] for row in cursor.fetchall()]
        if columns:
            if "risk_level" not in columns:
                cursor.execute("ALTER TABLE cases ADD COLUMN risk_level VARCHAR(32)")
            if "svi_score" not in columns:
                cursor.execute("ALTER TABLE cases ADD COLUMN svi_score INTEGER")
            if "human_review" not in columns:
                cursor.execute("ALTER TABLE cases ADD COLUMN human_review BOOLEAN")
            if "indicators" not in columns:
                cursor.execute("ALTER TABLE cases ADD COLUMN indicators TEXT")
            conn.commit()
        conn.close()
    except Exception:
        pass

