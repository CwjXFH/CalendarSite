import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "calendar.db"


def db_path() -> Path:
    """DB_PATH 覆盖默认 backend/data/calendar.db（容器内为 /data/calendar.db）。"""
    override = os.environ.get("DB_PATH", "").strip()
    return Path(override) if override else DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    path = db_path()
    if path.is_file() is False:
        raise FileNotFoundError(f"holiday database not found: {path}")
    conn = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def require_db() -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'holiday_days'"
        ).fetchone()
        if row is None:
            raise RuntimeError(f"holiday_days table missing in {db_path()}")
