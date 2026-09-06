from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from app.db.database import get_connection


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
