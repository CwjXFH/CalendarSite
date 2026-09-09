"""从 JSON 载入法定假日与调休补班，写入 holiday_days（中国大陆）。

改假日：编辑 data/holidays.json（或 HOLIDAYS_PATH）并更新 updated 后重启后端。
"""

import json
import os
from datetime import date
from pathlib import Path

from app.db.database import get_connection, init_db

# kind: holiday = 法定节假日, workday = 调休上班日
DEFAULT_HOLIDAYS_PATH = Path(__file__).resolve().parents[2] / "data" / "holidays.json"


def holidays_path() -> Path:
    """HOLIDAYS_PATH 可为 JSON 文件，或含 holidays.json 的目录。"""
    override = os.environ.get("HOLIDAYS_PATH", "").strip()
    path = Path(override) if override else DEFAULT_HOLIDAYS_PATH
    if path.is_dir():
        return path / "holidays.json"
    return path


def _holiday_payload(path: Path | None = None) -> dict:
    source = path or holidays_path()
    return json.loads(source.read_text(encoding="utf-8"))


def _year_day_lists(raw: dict) -> dict[str, list]:
    return {
        key: value
        for key, value in raw.items()
        if key != "updated" and isinstance(value, list)
    }


def load_holiday_rows(path: Path | None = None) -> list[tuple[str, str, str]]:
    raw = _holiday_payload(path)
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
    raw = _holiday_payload(path)
    if str(year) not in _year_day_lists(raw):
        return None
    updated = raw.get("updated")
    if isinstance(updated, dict):
        value = updated.get(str(year))
        return date.fromisoformat(value) if value else None
    if isinstance(updated, str) and updated:
        return date.fromisoformat(updated)
    return None


def seed_holidays(force: bool = True) -> None:
    """用 JSON 覆盖 holiday_days。默认覆盖已有数据，避免过期调休日残留。"""
    init_db()
    rows = load_holiday_rows()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM holiday_days").fetchone()["c"]
        if count > 0 and force is False:
            return
        conn.execute("DELETE FROM holiday_days")
        conn.executemany(
            "INSERT OR REPLACE INTO holiday_days (date, kind, name) VALUES (?, ?, ?)",
            rows,
        )
        conn.commit()
