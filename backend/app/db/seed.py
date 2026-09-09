"""从 JSON 载入法定假日与调休补班，写入 holiday_days（中国大陆）。

改假日：编辑 data/holidays.json（或 HOLIDAYS_PATH）后重启后端即可。
"""

import json
import os
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


def load_holiday_rows(path: Path | None = None) -> list[tuple[str, str, str]]:
    source = path or holidays_path()
    raw = json.loads(source.read_text(encoding="utf-8"))
    rows: list[tuple[str, str, str]] = []
    for _year, days in raw.items():
        for item in days:
            kind = item["kind"]
            if kind not in ("holiday", "workday"):
                raise ValueError(f"invalid holiday kind: {kind}")
            rows.append((item["date"], kind, item["name"]))
    return rows


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
