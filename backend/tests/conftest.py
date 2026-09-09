import atexit
import json
import os
import sqlite3
import tempfile
from pathlib import Path

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "holiday_days.json"


def pytest_configure() -> None:
    fd, name = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(name)
    conn.execute(
        """
        CREATE TABLE holiday_days (
            date TEXT PRIMARY KEY,
            kind TEXT NOT NULL CHECK (kind IN ('holiday', 'workday')),
            name TEXT
        )
        """
    )
    rows = [
        (item["date"], item["kind"], item["name"])
        for item in json.loads(_FIXTURE.read_text(encoding="utf-8"))
    ]
    conn.executemany(
        "INSERT INTO holiday_days (date, kind, name) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    os.environ["DB_PATH"] = name
    os.environ.setdefault("OPS_TOKEN", "test-ops-token")
    atexit.register(lambda: Path(name).unlink(missing_ok=True))
