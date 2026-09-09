import sqlite3
from datetime import date
from pathlib import Path

import pytest

from app.db.database import db_path, get_connection, require_db
from app.services.holiday import (
    get_holiday_map,
    holiday_updated,
    holiday_years,
    list_holiday_days,
)


def test_shipped_db_covers_2024_2026() -> None:
    years = holiday_years()
    assert years == [2024, 2025, 2026]
    by_date = {row["date"]: row for row in list_holiday_days(2024)}
    assert by_date["2024-02-10"]["kind"] == "holiday"
    assert by_date["2024-02-10"]["name"] == "春节"
    assert by_date["2024-02-04"]["kind"] == "workday"
    assert get_holiday_map("2026-10-01", "2026-10-12")["2026-10-01"] == "holiday"
    assert get_holiday_map("2026-09-20", "2026-09-20")["2026-09-20"] == "workday"
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM holiday_days").fetchone()["c"]
    assert count == 108
    assert holiday_updated(2026) == date(2026, 9, 9)
    assert holiday_updated(2024) == date(2026, 9, 9)
    assert holiday_updated(2023) is None


def test_db_path_env_and_missing_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DB_PATH", str(tmp_path / "missing.db"))
    with pytest.raises(FileNotFoundError):
        require_db()

    path = tmp_path / "calendar.db"
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE holiday_days (
            date TEXT PRIMARY KEY,
            kind TEXT NOT NULL CHECK (kind IN ('holiday', 'workday')),
            name TEXT
        )
        """
    )
    conn.execute(
        "CREATE TABLE holiday_meta (year INTEGER PRIMARY KEY, updated TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT INTO holiday_days VALUES ('2027-01-01', 'holiday', '元旦')"
    )
    conn.execute("INSERT INTO holiday_meta VALUES (2027, '2027-01-02')")
    conn.commit()
    conn.close()
    monkeypatch.setenv("DB_PATH", str(path))
    assert db_path() == path
    assert list_holiday_days(2027) == [
        {"date": "2027-01-01", "kind": "holiday", "name": "元旦"}
    ]
    assert holiday_updated(2027) == date(2027, 1, 2)
    monkeypatch.delenv("DB_PATH")
    assert db_path().name == "calendar.db"
