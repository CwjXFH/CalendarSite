"""法定假日与调休：只从挂载的 calendar.db 读。

改假日：ops API 写 holiday_days。放假页 lastmod 用该 db 文件 mtime。查询每次打开数据库。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from app.db.database import db_path, get_connection


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
