"""法定假日与调休：只从 JSON 读（HOLIDAYS_PATH / data/holidays.json）。

改假日：编辑 JSON 并更新 updated 后重启后端。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

# kind: holiday = 法定节假日, workday = 调休上班日
DEFAULT_HOLIDAYS_PATH = Path(__file__).resolve().parents[2] / "data" / "holidays.json"


def holidays_path() -> Path:
    """HOLIDAYS_PATH 可为 JSON 文件，或含 holidays.json 的目录。"""
    override = os.environ.get("HOLIDAYS_PATH", "").strip()
    path = Path(override) if override else DEFAULT_HOLIDAYS_PATH
    if path.is_dir():
        return path / "holidays.json"
    return path


@lru_cache(maxsize=8)
def _holiday_payload(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _payload(path: Path | None = None) -> dict:
    return _holiday_payload(str(path or holidays_path()))


def _year_day_lists(raw: dict) -> dict[str, list]:
    return {
        key: value
        for key, value in raw.items()
        if key != "updated" and isinstance(value, list)
    }


def load_holiday_rows(path: Path | None = None) -> list[tuple[str, str, str]]:
    raw = _payload(path)
    rows: list[tuple[str, str, str]] = []
    for days in _year_day_lists(raw).values():
        for item in days:
            kind = item["kind"]
            if kind not in ("holiday", "workday"):
                raise ValueError(f"invalid holiday kind: {kind}")
            rows.append((item["date"], kind, item["name"]))
    return rows


def holiday_updated(year: int, path: Path | None = None) -> date | None:
    """JSON 里该年放假数据的变更日；无记录则 None。updated 可为整文件日期或按年 map。"""
    raw = _payload(path)
    if str(year) not in _year_day_lists(raw):
        return None
    updated = raw.get("updated")
    if isinstance(updated, dict):
        value = updated.get(str(year))
        return date.fromisoformat(value) if value else None
    if isinstance(updated, str) and updated:
        return date.fromisoformat(updated)
    return None


def get_holiday_map(start_date: str, end_date: str) -> dict[str, str]:
    """返回 date -> kind（holiday / workday）。"""
    return {
        day: kind
        for day, kind, _name in load_holiday_rows()
        if start_date <= day <= end_date
    }


def list_holiday_days(year: int) -> list[dict[str, str]]:
    start, end = f"{year}-01-01", f"{year}-12-31"
    rows = [
        {"date": day, "kind": kind, "name": name or ""}
        for day, kind, name in load_holiday_rows()
        if start <= day <= end
    ]
    rows.sort(key=lambda row: row["date"])
    return rows


def holiday_years() -> list[int]:
    return sorted({int(day[:4]) for day, _kind, _name in load_holiday_rows()})


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
