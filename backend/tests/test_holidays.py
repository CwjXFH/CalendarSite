import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.database import db_path, get_connection, require_db
from app.main import app
from app.services.holiday import (
    get_holiday_map,
    holiday_updated,
    holiday_years,
    list_holiday_days,
)

client = TestClient(app)
OPS = {"X-Ops-Token": "test-ops-token"}


def test_shipped_fixture_covers_2024_2026() -> None:
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
    mtime_day = datetime.fromtimestamp(db_path().stat().st_mtime, tz=timezone.utc).date()
    assert holiday_updated(2026) == mtime_day
    assert holiday_updated(2024) == mtime_day
    assert holiday_updated(2023) is None


def test_db_path_env_and_missing_file(tmp_path: Path, monkeypatch) -> None:
    missing = tmp_path / "missing.db"
    monkeypatch.setenv("DB_PATH", str(missing))
    with pytest.raises(FileNotFoundError):
        get_connection()
    require_db()
    assert missing.is_file()
    assert list_holiday_days(2026) == []

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
        "INSERT INTO holiday_days VALUES ('2027-01-01', 'holiday', '元旦')"
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("DB_PATH", str(path))
    assert db_path() == path
    assert list_holiday_days(2027) == [
        {"date": "2027-01-01", "kind": "holiday", "name": "元旦"}
    ]
    mtime_day = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date()
    assert holiday_updated(2027) == mtime_day


def test_ops_holidays_require_token() -> None:
    listed = client.get("/api/v1/ops/holidays", params={"year": 2026})
    assert listed.status_code == 401
    wrong = client.get(
        "/api/v1/ops/holidays",
        params={"year": 2026},
        headers={"X-Ops-Token": "nope"},
    )
    assert wrong.status_code == 401


def test_ops_holidays_upsert_list_delete() -> None:
    put = client.put(
        "/api/v1/ops/holidays",
        headers=OPS,
        json={"date": "2027-01-01", "kind": "holiday", "name": "元旦"},
    )
    assert put.status_code == 200
    listed = client.get("/api/v1/ops/holidays", params={"year": 2027}, headers=OPS)
    assert listed.status_code == 200
    assert listed.json()["days"] == [
        {"date": "2027-01-01", "kind": "holiday", "name": "元旦"}
    ]
    deleted = client.delete(
        "/api/v1/ops/holidays",
        params={"date": "2027-01-01"},
        headers=OPS,
    )
    assert deleted.status_code == 200
    empty = client.get("/api/v1/ops/holidays", params={"year": 2027}, headers=OPS)
    assert empty.json()["days"] == []
