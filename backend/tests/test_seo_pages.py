from fastapi.testclient import TestClient

from app.main import app
from app.services.holiday import group_holiday_periods
from app.services.jieqi import get_jieqi_year

client = TestClient(app)


def test_home_html_without_js() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    text = response.text
    assert "<html" in text
    assert "万年历" in text
    assert "FAQPage" in text
    assert "放假" in text
    assert "节气" in text
    assert ">一</th>" in text
    assert "application/ld+json" in text
    assert 'rel="canonical"' in text


def test_year_page() -> None:
    response = client.get("/y/2026")
    assert response.status_code == 200
    text = response.text
    assert "2026年公历农历日历" in text
    assert "/y/2026/m/9" in text
    assert "FAQPage" in text


def test_month_page_september_2026() -> None:
    response = client.get("/y/2026/m/9")
    assert response.status_code == 200
    text = response.text
    assert "2026年9月" in text
    assert "中秋" in text
    assert "白露" in text or "秋分" in text


def test_fangjia_2026() -> None:
    response = client.get("/fangjia/2026")
    assert response.status_code == 200
    text = response.text
    assert "放假" in text
    assert "调休" in text
    assert "<title>" in text and "放假" in text[text.find("<title>") : text.find("</title>")]
    assert "春节" in text
    assert "2月15日" in text
    assert "班" in text
    assert 'href="/"' in text
    assert "FAQPage" in text
    assert 'href="/fangjia/2026.ics"' in text


def test_jieqi_2026_table_and_term() -> None:
    year_page = client.get("/jieqi/2026")
    assert year_page.status_code == 200
    assert "立春" in year_page.text
    assert "冬至" in year_page.text
    assert "FAQPage" in year_page.text
    assert "/jieqi/2026/lichun" in year_page.text

    term = client.get("/jieqi/2026/lichun")
    assert term.status_code == 200
    assert "交节" in term.text
    assert "2月4日" in term.text
    assert "04:02" in term.text
    assert "FAQPage" in term.text


def test_sitemap_contains_matrix() -> None:
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    text = response.text
    assert "https://wannianli.site/</loc>" in text
    assert "https://wannianli.site/y/2026</loc>" in text
    assert "https://wannianli.site/y/2026/m/9</loc>" in text
    assert "https://wannianli.site/jieqi/2026</loc>" in text
    assert "https://wannianli.site/jieqi/2026/lichun</loc>" in text
    assert "https://wannianli.site/fangjia/2026</loc>" in text


def test_fangjia_ics() -> None:
    response = client.get("/fangjia/2026.ics")
    assert response.status_code == 200
    assert "text/calendar" in response.headers["content-type"]
    assert "BEGIN:VCALENDAR" in response.text
    assert "春节放假" in response.text
    assert "调休上班" in response.text


def test_out_of_range_is_html_404() -> None:
    response = client.get("/y/1899")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "返回首页" in response.text


def test_unknown_jieqi_404() -> None:
    response = client.get("/jieqi/2026/not-a-term")
    assert response.status_code == 404


def test_2026_holiday_periods() -> None:
    periods = {p.name: p for p in group_holiday_periods(2026)}
    spring = periods["春节"]
    assert spring.days == 9
    assert [d.isoformat() for d in spring.makeup] == ["2026-02-14", "2026-02-28"]


def test_2026_has_24_jieqi() -> None:
    terms = get_jieqi_year(2026)
    assert len(terms) == 24
    assert terms[0].name == "小寒"
    assert terms[-1].name == "冬至"
    assert terms[-1].when.year == 2026
