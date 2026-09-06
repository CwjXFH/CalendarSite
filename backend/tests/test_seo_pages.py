from xml.etree import ElementTree

from fastapi.testclient import TestClient

from app.main import app
from app.services.holiday import group_holiday_periods
from app.services.jieqi import get_jieqi_year

client = TestClient(app)
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _attr(text: str, prefix: str) -> str:
    start = text.index(prefix) + len(prefix)
    return text[start : text.index('"', start)]


def _title(text: str) -> str:
    start = text.index("<title>") + len("<title>")
    return text[start : text.index("</title>", start)]


def test_fastapi_root_is_not_a_jinja_home() -> None:
    response = client.get("/")
    assert response.status_code == 404


def test_year_page() -> None:
    response = client.get("/y/2026")
    assert response.status_code == 200
    text = response.text
    assert "2026年公历农历日历" in text
    assert "/?y=2026&amp;m=9" in text
    assert "月历" in text
    assert "常见问题" in text
    assert "FAQPage" in text
    assert "BreadcrumbList" in text
    assert _attr(text, 'rel="canonical" href="') == "https://wannianli.site/y/2026"
    assert "公历农历对照" in _attr(text, 'name="description" content="')


def test_month_page_september_2026() -> None:
    response = client.get("/y/2026/m/9")
    assert response.status_code == 200
    text = response.text
    assert "2026年9月" in text
    assert "中秋" in text
    assert "白露" in text or "秋分" in text
    assert "查看" not in text
    assert "/y/jump" not in text


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
    assert "月历" in text
    assert "常见问题" in text
    assert 'href="/fangjia/2026.ics"' not in text
    assert "下载 ICS" not in text
    assert "添加到手机日历" not in text
    assert ".ics" not in text


def test_jieqi_2026_table_and_term() -> None:
    year_page = client.get("/jieqi/2026")
    assert year_page.status_code == 200
    text = year_page.text
    assert "立春" in text
    assert "冬至" in text
    assert "FAQPage" in text
    assert "<details" in text
    assert "月历" in text
    assert "/jieqi/2026/lichun" in text
    desc = _attr(text, 'name="description" content="')
    og = _attr(text, 'property="og:description" content="')
    assert desc.startswith("2026年二十四节气时间表")
    assert "立春交节" not in desc
    assert og == desc
    assert _attr(text, 'rel="canonical" href="') == "https://wannianli.site/jieqi/2026"

    term = client.get("/jieqi/2026/lichun")
    assert term.status_code == 200
    assert "交节" in term.text
    assert "2月4日" in term.text
    assert "星期三" in term.text
    assert "04:02" in term.text
    assert "FAQPage" in term.text
    term_desc = _attr(term.text, 'name="description" content="')
    assert term_desc.startswith("2026年立春交节时间是")
    assert _attr(term.text, 'rel="canonical" href="') == (
        "https://wannianli.site/jieqi/2026/lichun"
    )


def test_topic_pages_are_not_cross_wired() -> None:
    year = client.get("/y/2026").text
    month = client.get("/y/2026/m/9").text
    fangjia = client.get("/fangjia/2026").text
    jieqi = client.get("/jieqi/2026").text
    term = client.get("/jieqi/2026/lichun").text
    assert _title(year) == "2026年公历农历日历 - 万年历"
    assert _title(month) == "2026年9月公历农历日历 - 万年历"
    assert _title(fangjia) == "2026年放假安排与调休日历 - 万年历"
    assert _title(jieqi) == "2026年二十四节气时间表 - 万年历"
    assert _title(term).startswith("2026年立春交节时间")
    assert "放假" not in _attr(jieqi, 'name="description" content="')
    assert "公历农历对照" not in _attr(jieqi, 'name="description" content="')
    assert "二十四节气时间表" not in _attr(year, 'name="description" content="')
    assert "二十四节气时间表" not in _attr(term, 'name="description" content="')
    assert {
        _attr(page, 'rel="canonical" href="')
        for page in (year, month, fangjia, jieqi, term)
    } == {
        "https://wannianli.site/y/2026",
        "https://wannianli.site/y/2026/m/9",
        "https://wannianli.site/fangjia/2026",
        "https://wannianli.site/jieqi/2026",
        "https://wannianli.site/jieqi/2026/lichun",
    }


def test_sitemap_index_and_parts() -> None:
    index = client.get("/sitemap.xml")
    assert index.status_code == 200
    assert "application/xml" in index.headers["content-type"]
    root = ElementTree.fromstring(index.text)
    assert root.tag.endswith("sitemapindex")
    locs = [node.text for node in root.findall("sm:sitemap/sm:loc", NS)]
    assert locs == [
        "https://wannianli.site/sitemap-core.xml",
        "https://wannianli.site/sitemap-months.xml",
        "https://wannianli.site/sitemap-jieqi.xml",
    ]
    assert client.head("/sitemap.xml").status_code == 200

    core = client.get("/sitemap-core.xml")
    months = client.get("/sitemap-months.xml")
    jieqi = client.get("/sitemap-jieqi.xml")
    for response in (core, months, jieqi):
        assert response.status_code == 200
        parsed = ElementTree.fromstring(response.text)
        assert parsed.tag.endswith("urlset")
    assert "https://wannianli.site/</loc>" in core.text
    assert "https://wannianli.site/y/2026</loc>" in core.text
    assert "https://wannianli.site/jieqi/2026</loc>" in core.text
    assert "https://wannianli.site/fangjia/2026</loc>" in core.text
    assert "https://wannianli.site/y/2026/m/9</loc>" in months.text
    assert "https://wannianli.site/jieqi/2026/lichun</loc>" in jieqi.text


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
