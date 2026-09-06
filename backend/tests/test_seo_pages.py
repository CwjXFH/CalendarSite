from pathlib import Path
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
    assert "/y/2026/m/9" in text
    assert "/?y=2026&amp;m=9" not in text
    assert "/?y=2026&m=9" not in text
    assert "月历" in text
    assert "常见问题" in text
    assert "FAQPage" in text
    assert "BreadcrumbList" in text
    assert _attr(text, 'rel="canonical" href="') == "https://wannianli.site/y/2026"
    assert "公历农历对照" in _attr(text, 'name="description" content="')
    assert 'class="page-main"' in text
    assert 'href="/seo.css?v=20260906l"' in text
    assert 'src="/logo.svg"' in text
    assert "放假安排放假" not in text
    assert "二十四节气节气" not in text
    assert "nav-short" not in text
    assert 'class="tabbar"' in text
    assert "cals--year" in text
    assert "topic-capsules" in text
    assert "暂无宜忌" not in text
    assert "yiji" not in text


def test_seo_css_is_served() -> None:
    response = client.get("/seo.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert response.headers["cache-control"] == "public, max-age=600"
    assert ".page-main" in response.text
    assert ".nav-holiday" in response.text
    assert ".tabbar" in response.text
    assert ".cals--year" in response.text
    assert ".nav-short" not in response.text
    assert ".day-cell--holiday {\n  background: var(--holiday-bg);\n  border-radius: 0;" in response.text
    assert ".day-cell--work {\n  background: var(--work-bg);\n  border-radius: 0;" in response.text
    assert ".day-cell--weekend {\n  background: var(--weekend-bg);\n  border-radius: 0;" in response.text
    assert "--today-fill: #d8eee6;" in response.text
    assert "--work-bg: #f3ead8;" in response.text
    assert "--today-fill: #f3ead8;" not in response.text
    assert ".day-cell--today {\n  background: var(--today-fill);" in response.text
    assert ".day-cell__lunar--term {\n  color: var(--term);\n  font-weight: 650;\n}" in response.text


def test_logo_svg_is_image() -> None:
    response = client.get("/logo.svg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]
    body = response.content.decode("utf-8")
    assert "<svg" in body
    assert "历" in body
    assets = client.get("/assets/logo.svg")
    assert assets.status_code == 200
    assert "image/svg+xml" in assets.headers["content-type"]


def test_gift_svg_is_image() -> None:
    response = client.get("/gift.svg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]
    body = response.content.decode("utf-8")
    assert "<svg" in body
    assert 'fill="none"' in body
    assert 'stroke="#C45C5C"' in body
    assert "#D85D59" not in body
    assert "#FBE6A2" not in body
    assert "evenodd" not in body
    assert "PlusOutlined" not in body
    root = Path(__file__).resolve().parents[2]
    frontend = (root / "frontend" / "public" / "gift.svg").read_text(encoding="utf-8")
    backend = (root / "backend" / "app" / "static" / "gift.svg").read_text(encoding="utf-8")
    assert frontend == backend == body


def test_leaf_svg_is_image() -> None:
    response = client.get("/leaf.svg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]
    body = response.content.decode("utf-8")
    assert "<svg" in body
    assert "<path" in body
    assert "#5D8A62" in body
    assert "border-radius" not in body
    root = Path(__file__).resolve().parents[2]
    frontend = (root / "frontend" / "public" / "leaf.svg").read_text(encoding="utf-8")
    backend = (root / "backend" / "app" / "static" / "leaf.svg").read_text(encoding="utf-8")
    assert frontend == backend == body
    nginx = (root / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    assert "location = /leaf.svg" in nginx
    assert "try_files /leaf.svg =404" in nginx


def test_nginx_unknown_paths_are_real_404() -> None:
    root = Path(__file__).resolve().parents[2]
    nginx = (root / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    assert "try_files $uri $uri/ /index.html" not in nginx
    assert "try_files $uri $uri/ =404;" in nginx
    vite = (root / "frontend" / "vite.config.ts").read_text(encoding="utf-8")
    assert "appType: 'mpa'" in vite


def test_homepage_pixel_icons_and_grid() -> None:
    root = Path(__file__).resolve().parents[2]
    page = (root / "frontend" / "src" / "pages" / "CalendarPage.tsx").read_text(encoding="utf-8")
    css = (root / "frontend" / "src" / "App.css").read_text(encoding="utf-8")
    assert "/gift.svg?v=20260906p" in page
    assert page.count("/leaf.svg?v=20260906p") == 2
    assert "ico--leaf" not in page
    assert ".ico--leaf" not in css
    assert "border-right: 1px solid var(--grid-line);\n  border-bottom: 1px solid var(--grid-line)" not in css
    assert ".day-cell--weekend {\n  background: transparent;" in css
    assert ".day-cell__lunar--term {\n  color: var(--term);\n  font-weight: 650;" in css
    assert ".day-cell--selected:not(.day-cell--holiday):not(.day-cell--work):not(.day-cell--today) {\n  background: var(--selected-fill);" in css
    assert ".day-cell--today {\n  background: var(--today-fill);" in css
    assert ".day-cell--holiday {\n  background: var(--holiday-bg);\n  border-radius: 0;" in css
    assert ".day-cell--work {\n  background: var(--work-bg);\n  border-radius: 0;" in css
    assert ".day-cell--selected .day-cell__solar {\n  background: var(--selected-fill);" not in css


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
    assert "暂无宜忌" not in text
    assert "yiji" not in text


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
    assert "暂无宜忌" not in text
    assert "yiji" not in text

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
