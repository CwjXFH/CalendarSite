import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "calendar.db"

_HOLIDAY_DAYS_DDL = """
CREATE TABLE IF NOT EXISTS holiday_days (
    date TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('holiday', 'workday')),
    name TEXT
)
"""


def db_path() -> Path:
    """DB_PATH 覆盖默认 backend/data/calendar.db（容器内为 /data/calendar.db）。"""
    override = os.environ.get("DB_PATH", "").strip()
    return Path(override) if override else DEFAULT_DB_PATH


def get_connection(*, write: bool = False) -> sqlite3.Connection:
    path = db_path()
    if path.is_file() is False:
        if write is False:
            raise FileNotFoundError(f"holiday database not found: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    if write:
        conn.execute(_HOLIDAY_DAYS_DDL)
    return conn


def require_db() -> None:
    """文件不存在则建空表，不写入假日行。"""
    with get_connection(write=True) as conn:
        conn.execute(_HOLIDAY_DAYS_DDL)
        conn.commit()
