import json
from pathlib import Path

from app.db.seed import DEFAULT_HOLIDAYS_PATH, holidays_path, load_holiday_rows


def test_default_holidays_json_covers_2024_2026() -> None:
    rows = load_holiday_rows(DEFAULT_HOLIDAYS_PATH)
    years = {date[:4] for date, _kind, _name in rows}
    assert years == {"2024", "2025", "2026"}
    by_date = {date: (kind, name) for date, kind, name in rows}
    assert by_date["2024-02-10"] == ("holiday", "春节")
    assert by_date["2024-02-04"] == ("workday", "春节调休")
    assert by_date["2026-10-01"] == ("holiday", "国庆")
    assert by_date["2026-09-20"] == ("workday", "国庆调休")
    assert len(rows) == 108


def test_holidays_path_env_file_or_directory(tmp_path: Path, monkeypatch) -> None:
    file_path = tmp_path / "holidays.json"
    file_path.write_text(
        json.dumps({"2027": [{"date": "2027-01-01", "kind": "holiday", "name": "元旦"}]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("HOLIDAYS_PATH", str(file_path))
    assert holidays_path() == file_path
    assert load_holiday_rows() == [("2027-01-01", "holiday", "元旦")]

    monkeypatch.setenv("HOLIDAYS_PATH", str(tmp_path))
    assert holidays_path() == file_path
    assert load_holiday_rows() == [("2027-01-01", "holiday", "元旦")]

    monkeypatch.delenv("HOLIDAYS_PATH")
    assert holidays_path() == DEFAULT_HOLIDAYS_PATH
