from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["cache-control"] == "no-store"


def test_meta() -> None:
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    data = response.json()
    assert data["minYear"] == 1900
    assert data["maxYear"] >= 2026
    assert response.headers["cache-control"] == "public, max-age=86400"


def test_calendar_month() -> None:
    response = client.get("/api/v1/calendar", params={"year": 2026, "month": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2026
    assert data["month"] == 2
    assert data["lunarYearMonth"]
    assert "年" in data["lunarYearMonth"] and data["lunarYearMonth"].endswith("月")
    assert len(data["days"]) == 42
    mid = next(d for d in data["days"] if d["date"] == "2026-02-15")
    assert data["lunarYearMonth"] == mid["lunarYearMonth"]
    spring = next(d for d in data["days"] if d["date"] == "2026-02-17")
    assert spring["festival"] == "春节"
    assert spring["isLegalHoliday"] is True
    assert response.headers["cache-control"] == "public, max-age=86400"


def _day(year: int, month: int, date: str) -> dict:
    response = client.get("/api/v1/calendar", params={"year": year, "month": month})
    assert response.status_code == 200
    return next(d for d in response.json()["days"] if d["date"] == date)


def test_2026_official_holidays() -> None:
    """国办发明电〔2025〕7号：2026 年放假调休。"""
    new_year = _day(2026, 1, "2026-01-03")
    assert new_year["isLegalHoliday"] is True
    new_year_work = _day(2026, 1, "2026-01-04")
    assert new_year_work["isMakeupWorkday"] is True
    assert new_year_work["isLegalHoliday"] is False

    spring_start = _day(2026, 2, "2026-02-15")
    spring_end = _day(2026, 2, "2026-02-23")
    assert spring_start["isLegalHoliday"] is True
    assert spring_end["isLegalHoliday"] is True
    assert _day(2026, 2, "2026-02-14")["isMakeupWorkday"] is True
    assert _day(2026, 2, "2026-02-28")["isMakeupWorkday"] is True

    labor_work = _day(2026, 5, "2026-05-09")
    assert labor_work["isMakeupWorkday"] is True
    leftover = _day(2026, 4, "2026-04-26")
    assert leftover["isMakeupWorkday"] is False
    assert leftover["isLegalHoliday"] is False


def test_holidays_2026() -> None:
    response = client.get("/api/v1/holidays", params={"year": 2026})
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2026
    names = [p["name"] for p in data["periods"]]
    assert "春节" in names
    assert "国庆" in names
    national = next(p for p in data["periods"] if p["name"] == "国庆")
    assert national["days"] == 7
    assert national["start"] == "2026-10-01"
    assert "2026-09-20" in national["makeup"]
    assert response.headers["cache-control"] == "public, max-age=86400"


def test_invalid_year() -> None:
    response = client.get("/api/v1/calendar", params={"year": 1899, "month": 1})
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_YEAR"


def test_lunar_festivals() -> None:
    from app.services.lunar import get_day_info

    assert get_day_info(2026, 2, 17)["festival"] == "春节"
    assert get_day_info(2026, 2, 16)["festival"] == "除夕"
    assert get_day_info(2026, 2, 10)["festival"] == "小年"
    assert get_day_info(2026, 2, 11)["festival"] == "小年"
    assert get_day_info(2026, 1, 26)["festival"] == "腊八"
    assert get_day_info(2026, 3, 3)["festival"] == "元宵"


def test_calendar_day_has_yiji() -> None:
    mid = _day(2026, 9, "2026-09-24")
    assert "年" in mid["ganZhi"] and "月" in mid["ganZhi"] and mid["ganZhi"].endswith("日")
    assert mid["lunarMonthDay"] == "八月十四"
    assert mid["yi"] != []
    assert mid["ji"] != []
    assert mid["nearestTerm"] is not None
    assert mid["nearestTerm"]["name"] == "秋分"
    assert mid["nearestTerm"]["passed"] is True
    assert mid["nearestTerm"]["date"] == "2026-09-23"


def test_day_detail_endpoint() -> None:
    response = client.get("/api/v1/day", params={"date": "2026-09-24"})
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-09-24"
    assert data["weekday"] == "星期四"
    assert data["lunarMonthDay"] == "八月十四"
    assert "丁酉月" in data["ganZhi"]
    assert data["yi"] != []
    assert data["ji"] != []
    assert data["nearestTerm"]["name"] == "秋分"
    assert data["nearestTerm"]["time"]
    assert response.headers["cache-control"] == "public, max-age=86400"

    bad = client.get("/api/v1/day", params={"date": "2026-13-40"})
    assert bad.status_code == 400
    assert bad.json()["code"] == "INVALID_DATE"


def test_nearest_jieqi_on_term_day() -> None:
    from datetime import date

    from app.services.jieqi import nearest_jieqi

    found = nearest_jieqi(date(2026, 9, 23))
    assert found is not None
    item, passed = found
    assert item.name == "秋分"
    assert passed is False
