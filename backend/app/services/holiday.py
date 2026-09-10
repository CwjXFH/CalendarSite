"""法定假日与调休：只从挂载的 calendar.db 读。

空表时写入 holidays.bootstrap.json（2024–2026）。之后改假日走 ops API。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.db.database import db_path, get_connection

BOOTSTRAP_PATH = Path(__file__).resolve().parents[1] / "data" / "holidays.bootstrap.json"


def holiday_mtime(year: int) -> datetime | None:
    """该年有假日数据时返回 calendar.db 的 mtime；否则 None。"""
    with get_connection() as conn:
        has_year = conn.execute(
            "SELECT 1 FROM holiday_days WHERE date >= ? AND date <= ? LIMIT 1",
            (f"{year}-01-01", f"{year}-12-31"),
        ).fetchone()
    if has_year is None:
        return None
    return datetime.fromtimestamp(db_path().stat().st_mtime, tz=timezone.utc)


def holiday_updated(year: int) -> date | None:
    when = holiday_mtime(year)
    if when is None:
        return None
    return when.date()


def get_holiday_map(start_date: str, end_date: str) -> dict[str, str]:
    """返回 date -> kind（holiday / workday）。"""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT date, kind
            FROM holiday_days
            WHERE date >= ? AND date <= ?
            """,
            (start_date, end_date),
        ).fetchall()
    return {row["date"]: row["kind"] for row in rows}


def list_holiday_days(year: int) -> list[dict[str, str]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT date, kind, name
            FROM holiday_days
            WHERE date >= ? AND date <= ?
            ORDER BY date
            """,
            (f"{year}-01-01", f"{year}-12-31"),
        ).fetchall()
    return [
        {"date": row["date"], "kind": row["kind"], "name": row["name"] or ""}
        for row in rows
    ]


def holiday_years() -> list[int]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(date, 1, 4) AS y FROM holiday_days ORDER BY y"
        ).fetchall()
    return [int(row["y"]) for row in rows]


@dataclass
class HolidayPeriod:
    name: str
    start: date
    end: date
    makeup: list[date] = field(default_factory=list)

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def group_holiday_periods(year: int) -> list[HolidayPeriod]:
    rows = list_holiday_days(year)
    holidays = [r for r in rows if r["kind"] == "holiday"]
    workdays = [r for r in rows if r["kind"] == "workday"]

    periods: list[HolidayPeriod] = []
    for row in holidays:
        day = date.fromisoformat(row["date"])
        name = row["name"] or "法定假日"
        if periods and day == periods[-1].end + timedelta(days=1):
            periods[-1].end = day
            if name != periods[-1].name and name not in periods[-1].name:
                periods[-1].name = f"{periods[-1].name}、{name}"
        else:
            periods.append(HolidayPeriod(name=name, start=day, end=day))

    for row in workdays:
        family = (row["name"] or "").replace("调休", "")
        work_day = date.fromisoformat(row["date"])
        matched = next((p for p in periods if family and family in p.name), None)
        if matched is None:
            continue
        matched.makeup.append(work_day)
    return periods


def upsert_holiday_day(day: str, kind: str, name: str) -> None:
    date.fromisoformat(day)
    if kind not in ("holiday", "workday"):
        raise ValueError(f"invalid holiday kind: {kind}")
    with get_connection(write=True) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO holiday_days (date, kind, name) VALUES (?, ?, ?)",
            (day, kind, name),
        )
        conn.commit()


def delete_holiday_day(day: str) -> None:
    date.fromisoformat(day)
    with get_connection(write=True) as conn:
        conn.execute("DELETE FROM holiday_days WHERE date = ?", (day,))
        conn.commit()


def _bootstrap_rows() -> list[tuple[str, str, str]]:
    raw = json.loads(BOOTSTRAP_PATH.read_text(encoding="utf-8"))
    rows: list[tuple[str, str, str]] = []
    for item in raw:
        kind = item["kind"]
        if kind not in ("holiday", "workday"):
            raise ValueError(f"invalid holiday kind: {kind}")
        rows.append((item["date"], kind, item["name"]))
    return rows


# bootstrap json 只在 holiday_days 为空时灌入；有行后永不读取，改 json 不影响线上。真相源是 calendar.db。
def bootstrap_holidays_if_empty() -> None:
    """仅当 holiday_days 为空时写入 2024–2026 bootstrap，已有行则不动。"""
    rows = _bootstrap_rows()
    with get_connection(write=True) as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM holiday_days").fetchone()["c"]
        if count > 0:
            return
        conn.executemany(
            "INSERT INTO holiday_days (date, kind, name) VALUES (?, ?, ?)",
            rows,
        )
        conn.commit()
