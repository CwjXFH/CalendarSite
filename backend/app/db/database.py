import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "calendar.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS holiday_days (
                date TEXT PRIMARY KEY,
                kind TEXT NOT NULL CHECK (kind IN ('holiday', 'workday')),
                name TEXT
            )
            """
        )
        conn.commit()
