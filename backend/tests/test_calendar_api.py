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


def test_invalid_year() -> None:
    response = client.get("/api/v1/calendar", params={"year": 1899, "month": 1})
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_YEAR"
