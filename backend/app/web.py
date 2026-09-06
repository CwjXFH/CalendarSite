from __future__ import annotations

import json
from calendar import monthrange
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.templating import Jinja2Templates

from app.api.v1 import limiter
from app.config import MIN_YEAR, SITE_NAME, SITE_URL, max_year
from app.services.calendar import get_calendar_cached
from app.services.holiday import group_holiday_periods, holiday_years
from app.services.jieqi import (
    JIEQI_24,
    JIEQI_BLURB,
    JIEQI_SLUG,
    JieqiItem,
    get_jieqi_by_slug,
    get_jieqi_year,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

WEEKDAYS = ("一", "二", "三", "四", "五", "六", "日")


def _valid_year(year: int) -> bool:
    return MIN_YEAR <= year <= max_year()


def _require_year(year: int) -> None:
    if _valid_year(year) is False:
        raise HTTPException(status_code=404, detail="year out of range")


def _month_view(year: int, month: int) -> dict:
    cal = get_calendar_cached(year, month)
    days = list(cal.days)
    return {
        "year": year,
        "month": month,
        "lunarYearMonth": cal.lunarYearMonth,
        "weeks": [days[i : i + 7] for i in range(0, 42, 7)],
        "href": f"/y/{year}/m/{month}",
    }


def _fmt_range(start: date, end: date) -> str:
    if start == end:
        return f"{start.month}月{start.day}日"
    if start.month == end.month:
        return f"{start.month}月{start.day}日–{end.day}日"
    return f"{start.month}月{start.day}日–{end.month}月{end.day}日"


def _fmt_dates(dates: list[date]) -> str:
    return "、".join(f"{d.month}月{d.day}日" for d in dates)


def _breadcrumb_json(items: list[tuple[str, str]]) -> str:
    entities = [
        {
            "@type": "ListItem",
            "position": index,
            "name": name,
            "item": f"{SITE_URL}{path}",
        }
        for index, (name, path) in enumerate(items, start=1)
    ]
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": entities,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _faq_json(faqs: list[tuple[str, str]]) -> str:
    entities = [
        {
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {"@type": "Answer", "text": answer},
        }
        for question, answer in faqs
    ]
    return json.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _html(
    request: Request,
    template: str,
    context: dict,
    max_age: int = 3600,
) -> HTMLResponse:
    response = templates.TemplateResponse(request, template, context)
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    return response


def _page(
    request: Request,
    *,
    template: str,
    title: str,
    description: str,
    path: str,
    heading: str,
    year: int,
    faqs: list[tuple[str, str]],
    breadcrumbs: list[tuple[str, str]] | None = None,
    extra: dict | None = None,
    max_age: int = 3600,
) -> HTMLResponse:
    context = {
        "site_name": SITE_NAME,
        "site_url": SITE_URL,
        "title": title,
        "description": description,
        "canonical": f"{SITE_URL}{path}",
        "heading": heading,
        "year": year,
        "min_year": MIN_YEAR,
        "max_year": max_year(),
        "weekdays": WEEKDAYS,
        "faqs": faqs,
        "faq_json": _faq_json(faqs) if faqs else "",
        "breadcrumb_json": _breadcrumb_json(breadcrumbs) if breadcrumbs else "",
        "nav_fangjia": f"/fangjia/{year}",
        "nav_jieqi": f"/jieqi/{year}",
        "nav_year": f"/y/{year}",
    }
    if extra:
        context.update(extra)
    return _html(request, template, context, max_age=max_age)


def _fangjia_faqs(year: int, periods: list) -> list[tuple[str, str]]:
    if periods == []:
        return [
            (
                f"{year}年放假安排公布了吗？",
                f"本站暂无{year}年国务院办公厅公布的放假调休数据。请以官方通知为准，公布后会更新。",
            ),
            (
                "法定节假日一般有哪些？",
                "元旦、春节、清明、劳动节、端午、中秋、国庆。具体天数和调休每年由国务院办公厅通知确定。",
            ),
            (
                "调休是什么意思？",
                "把相邻周末调整到长假两端，对应工作日需补班。月历上标「班」。",
            ),
            (
                "周末一定放假吗？",
                "自然周末通常休息；若被安排为调休上班日，则当天需要上班。",
            ),
            (
                "放假安排以什么为准？",
                "以国务院办公厅当年通知为准，本站按已公布安排标注，不推测未公布年份。",
            ),
            (
                "哪里看公历农历？",
                f"可打开{year}年年历或各月页面，格子内同时显示公历与农历。",
            ),
        ]

    spring = next((p for p in periods if "春节" in p.name), None)
    national = next((p for p in periods if "国庆" in p.name), None)
    new_year = next((p for p in periods if p.name.startswith("元旦")), None)
    mid = next((p for p in periods if "中秋" in p.name and "国庆" not in p.name), None)
    makeup_all = [d for p in periods for d in p.makeup]

    faqs: list[tuple[str, str]] = []
    if spring is not None:
        extra = f"调休上班：{_fmt_dates(spring.makeup)}。" if spring.makeup else ""
        faqs.append(
            (
                f"{year}年春节放假安排是什么？",
                f"{year}年春节放假{_fmt_range(spring.start, spring.end)}，共{spring.days}天。{extra}",
            )
        )
    if national is not None:
        extra = f"调休上班：{_fmt_dates(national.makeup)}。" if national.makeup else ""
        faqs.append(
            (
                f"{year}年国庆怎么放假、哪些日子调休？",
                f"{year}年国庆放假{_fmt_range(national.start, national.end)}，共{national.days}天。{extra}",
            )
        )
    if new_year is not None:
        extra = f"调休上班：{_fmt_dates(new_year.makeup)}。" if new_year.makeup else ""
        faqs.append(
            (
                f"{year}年元旦放几天？",
                f"{year}年元旦放假{_fmt_range(new_year.start, new_year.end)}，共{new_year.days}天。{extra}",
            )
        )
    if mid is not None:
        faqs.append(
            (
                f"{year}年中秋放几天？",
                f"{year}年中秋放假{_fmt_range(mid.start, mid.end)}，共{mid.days}天。",
            )
        )
    faqs.extend(
        [
            (
                "调休上班日要上班吗？",
                "要。调休是把周末挪到连休日，对应日期需补班。本页月历用「班」标出。"
                + (f" {year}年调休上班日：{_fmt_dates(sorted(makeup_all))}。" if makeup_all else ""),
            ),
            (
                "放假安排以什么为准？",
                "以国务院办公厅当年通知为准。本站按已公布安排标注法定假日与调休，不编造未公布年份。",
            ),
            (
                f"如何把{year}年放假安排导入日历？",
                f"下载 {SITE_URL}/fangjia/{year}.ics 导入系统日历，含法定假日与调休补班。",
            ),
            (
                "法定节假日和周末有何不同？",
                "法定节假日是国务院安排的休息日（月历深红）；周末是自然周六日（浅红）。调休补班日即使在周末也要上班。",
            ),
        ]
    )
    return faqs[:8]


def _jieqi_year_faqs(year: int, terms: tuple[JieqiItem, ...]) -> list[tuple[str, str]]:
    lichun = next((t for t in terms if t.name == "立春"), None)
    dongzhi = next((t for t in terms if t.name == "冬至"), None)
    qingming = next((t for t in terms if t.name == "清明"), None)
    faqs = [
        (
            "二十四节气分别是哪些？",
            "小寒、大寒、立春、雨水、惊蛰、春分、清明、谷雨、立夏、小满、芒种、夏至、"
            "小暑、大暑、立秋、处暑、白露、秋分、寒露、霜降、立冬、小雪、大雪、冬至。",
        ),
        (
            "交节时间是什么意思？",
            "交节时间是太阳黄经到达该节气点的时刻（北京时间），不一定在当天 0 点。",
        ),
        (
            "节气按公历还是农历？",
            "节气按太阳运行划分，对应公历日期每年略有前后；农历日期会跟着变。本表给出公历交节时刻。",
        ),
    ]
    if lichun is not None:
        faqs.insert(
            0,
            (
                f"{year}年立春是哪天？",
                f"{year}年立春交节时间是{lichun.datetime_text}（北京时间）。",
            ),
        )
    if dongzhi is not None:
        faqs.append(
            (
                f"{year}年冬至是哪天？",
                f"{year}年冬至交节时间是{dongzhi.datetime_text}（北京时间）。",
            )
        )
    if qingming is not None:
        faqs.append(
            (
                "清明是节气还是法定假日？",
                f"清明既是二十四节气，也常对应法定假日。{year}年清明交节时间是{qingming.datetime_text}（北京时间）；放假以国务院安排为准。",
            )
        )
    faqs.append(
        (
            "怎么看某一个节气的交节时刻？",
            f"打开本页表格中的节气名称，进入该节气页面，首屏给出{year}年交节日期与钟点。",
        )
    )
    return faqs[:8]


def _jieqi_term_faqs(year: int, item: JieqiItem, prev: JieqiItem | None, nxt: JieqiItem | None) -> list[tuple[str, str]]:
    faqs = [
        (
            f"{year}年{item.name}是几月几号？",
            f"{year}年{item.name}是{item.when.month}月{item.when.day}日{item.weekday}。",
        ),
        (
            f"{item.name}交节具体时间是几点？",
            f"{year}年{item.name}交节时间是{item.datetime_text}（北京时间）。",
        ),
        (
            f"{item.name}是什么节气？",
            JIEQI_BLURB[item.name],
        ),
        (
            "交节当天从 0 点就算这个节气吗？",
            f"一般以交节时刻为界。{year}年{item.name}在{item.time_text}交节，此前仍属上一节气。",
        ),
    ]
    if nxt is not None:
        faqs.append(
            (
                f"{item.name}之后下一个节气是什么？",
                f"下一个节气是{nxt.name}，交节时间是{nxt.datetime_text}（北京时间）。",
            )
        )
    if prev is not None:
        faqs.append(
            (
                f"{item.name}之前一个节气是什么？",
                f"上一节气是{prev.name}，交节时间是{prev.datetime_text}（北京时间）。",
            )
        )
    faqs.append(
        (
            f"如何查看{year}年全部节气？",
            f"见{year}年二十四节气时间表，列出全部 {len(JIEQI_24)} 个节气的交节时间。",
        )
    )
    return faqs[:8]


@router.get("/y/{year}", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def year_page(request: Request, year: int) -> HTMLResponse:
    _require_year(year)
    months = [_month_view(year, month) for month in range(1, 13)]
    periods = group_holiday_periods(year)
    terms = get_jieqi_year(year)
    faqs = [
        (
            f"{year}年有哪几个月？",
            f"{year}年公历 1 月至 12 月均可对照农历；点击月份进入该月日历。",
        ),
        (
            f"{year}年放假吗？",
            f"{year}年已公布放假安排，详见放假安排页。"
            if periods
            else f"{year}年尚未录入国务院放假安排，可先看月历中的周末与节气。",
        ),
        (
            f"{year}年有哪些节气？",
            f"{year}年二十四节气共 {len(terms)} 个，详见节气时间表。",
        ),
        (
            "格子里的农历是什么？",
            "每个日期同时给出公历日和农历日；初一显示农历月份，传统节日、节气优先显示名称。",
        ),
        (
            "红色格子是什么意思？",
            "深红为法定节假日，浅红为周末；标「班」为调休上班。",
        ),
        (
            "年份能查到多早？",
            f"公历农历与节气可查 {MIN_YEAR} 年至 {max_year()} 年。",
        ),
    ]
    return _page(
        request,
        template="year.html",
        title=f"{year}年公历农历日历 - 万年历",
        description=f"{year}年全年公历农历对照，含法定节假日、调休、传统节日与二十四节气。",
        path=f"/y/{year}",
        heading=f"{year}年公历农历日历",
        year=year,
        faqs=faqs,
        breadcrumbs=[("万年历", "/"), (f"{year}年公历农历日历", f"/y/{year}")],
        extra={"months": months, "periods": periods, "terms": terms},
    )


@router.get("/y/{year}/m/{month}", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def month_page(request: Request, year: int, month: int) -> HTMLResponse:
    _require_year(year)
    if month < 1 or month > 12:
        raise HTTPException(status_code=404, detail="invalid month")
    cal = _month_view(year, month)
    prev_date = date(year, month, 1) - timedelta(days=1)
    last_day = monthrange(year, month)[1]
    next_date = date(year, month, last_day) + timedelta(days=1)
    prev_href = (
        f"/y/{prev_date.year}/m/{prev_date.month}" if _valid_year(prev_date.year) else None
    )
    next_href = (
        f"/y/{next_date.year}/m/{next_date.month}" if _valid_year(next_date.year) else None
    )
    month_terms = [t for t in get_jieqi_year(year) if t.when.month == month]
    month_festivals = sorted(
        {
            cell.festival
            for week in cal["weeks"]
            for cell in week
            if cell.isCurrentMonth and cell.festival
        }
    )
    faqs = [
        (
            f"{year}年{month}月公历农历怎么对照？",
            f"下表为{year}年{month}月日历，每格同时给出公历日与农历{cal['lunarYearMonth']}对应日期。",
        ),
        (
            f"{year}年{month}月有哪些节气？",
            "、".join(f"{t.name}（{t.when.day}日 {t.time_text}）" for t in month_terms)
            if month_terms
            else f"{year}年{month}月没有交节的二十四节气。",
        ),
        (
            f"{year}年{month}月有哪些传统节日？",
            "、".join(month_festivals) if month_festivals else f"{year}年{month}月日历未标传统节日。",
        ),
        (
            "如何换月份？",
            "使用上月、下月链接进入相邻月份；交互换月请回首页万年历。",
        ),
        (
            f"{year}年放假安排在哪？",
            f"见{year}年放假安排页，含调休补班日期。",
        ),
        (
            "周末和法定假日如何区分？",
            "周末浅红色，法定节假日深红色，调休上班标「班」。",
        ),
    ]
    return _page(
        request,
        template="month.html",
        title=f"{year}年{month}月公历农历日历 - 万年历",
        description=f"{year}年{month}月公历农历对照，{cal['lunarYearMonth']}，含节假日、调休与节气。",
        path=f"/y/{year}/m/{month}",
        heading=f"{year}年{month}月公历农历",
        year=year,
        faqs=faqs,
        breadcrumbs=[
            ("万年历", "/"),
            (f"{year}年", f"/y/{year}"),
            (f"{month}月", f"/y/{year}/m/{month}"),
        ],
        extra={
            "cal": cal,
            "prev_href": prev_href,
            "next_href": next_href,
            "month_terms": month_terms,
        },
    )


@router.get("/jieqi/{year}", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def jieqi_year_page(request: Request, year: int) -> HTMLResponse:
    _require_year(year)
    terms = get_jieqi_year(year)
    faqs = _jieqi_year_faqs(year, terms)
    description = (
        f"{year}年二十四节气时间表，列出小寒至冬至共 {len(terms)} 个节气的"
        "公历交节日期与北京时间。"
    )
    lead = f"{year}年二十四节气共 {len(terms)} 个，下表为各节气交节时间（北京时间）。"
    return _page(
        request,
        template="jieqi_year.html",
        title=f"{year}年二十四节气时间表 - 万年历",
        description=description,
        path=f"/jieqi/{year}",
        heading=f"{year}年二十四节气时间表",
        year=year,
        faqs=faqs,
        breadcrumbs=[("万年历", "/"), (f"{year}年二十四节气时间表", f"/jieqi/{year}")],
        extra={"terms": terms, "lead": lead, "slugs": JIEQI_SLUG},
    )


@router.get("/jieqi/{year}/{slug}", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def jieqi_term_page(request: Request, year: int, slug: str) -> HTMLResponse:
    _require_year(year)
    item = get_jieqi_by_slug(year, slug)
    if item is None:
        raise HTTPException(status_code=404, detail="unknown jieqi")
    terms = get_jieqi_year(year)
    index = next(i for i, term in enumerate(terms) if term.slug == slug)
    prev_item = terms[index - 1] if index > 0 else None
    next_item = terms[index + 1] if index + 1 < len(terms) else None
    lead = f"{year}年{item.name}交节时间是{item.datetime_text}（北京时间）。"
    faqs = _jieqi_term_faqs(year, item, prev_item, next_item)
    return _page(
        request,
        template="jieqi_term.html",
        title=f"{year}年{item.name}交节时间：{item.when.month}月{item.when.day}日 - 万年历",
        description=lead,
        path=f"/jieqi/{year}/{slug}",
        heading=f"{year}年{item.name}交节时间",
        year=year,
        faqs=faqs,
        breadcrumbs=[
            ("万年历", "/"),
            (f"{year}年二十四节气", f"/jieqi/{year}"),
            (item.name, f"/jieqi/{year}/{slug}"),
        ],
        extra={
            "item": item,
            "lead": lead,
            "blurb": JIEQI_BLURB[item.name],
            "prev_item": prev_item,
            "next_item": next_item,
            "cal": _month_view(item.when.year, item.when.month),
        },
    )


@router.get("/fangjia/{year}.ics")
@limiter.limit("30/minute")
async def fangjia_ics(request: Request, year: int) -> Response:
    _require_year(year)
    periods = group_holiday_periods(year)
    if periods == []:
        raise HTTPException(status_code=404, detail="no holiday data")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//wannianli.site//fangjia//ZH",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{year}年放假安排",
    ]
    for period in periods:
        end_excl = period.end + timedelta(days=1)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:holiday-{period.start.isoformat()}@wannianli.site",
                f"DTSTART;VALUE=DATE:{period.start.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{end_excl.strftime('%Y%m%d')}",
                f"SUMMARY:{period.name}放假",
                f"DESCRIPTION:{year}年{period.name}放假{_fmt_range(period.start, period.end)}",
                "END:VEVENT",
            ]
        )
        for makeup in period.makeup:
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:makeup-{makeup.isoformat()}@wannianli.site",
                    f"DTSTART;VALUE=DATE:{makeup.strftime('%Y%m%d')}",
                    f"DTEND;VALUE=DATE:{(makeup + timedelta(days=1)).strftime('%Y%m%d')}",
                    f"SUMMARY:{period.name}调休上班",
                    "END:VEVENT",
                ]
            )
    lines.append("END:VCALENDAR")
    body = "\r\n".join(lines) + "\r\n"
    return Response(
        content=body,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{year}-fangjia.ics"',
            "Cache-Control": "public, max-age=86400",
        },
    )


@router.get("/fangjia/{year}", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def fangjia_page(request: Request, year: int) -> HTMLResponse:
    _require_year(year)
    periods = group_holiday_periods(year)
    months = [_month_view(year, month) for month in range(1, 13)]
    faqs = _fangjia_faqs(year, periods)
    if periods:
        lead = (
            f"{year}年放假安排含{len(periods)}个假期，月历标出法定节假日与调休补班。"
            "以下按国务院已公布安排整理。"
        )
        description = f"{year}年放假安排与调休日历，含假期表、月历标注和调休上班日。"
    else:
        lead = f"{year}年国务院办公厅放假安排尚未录入本站，请以官方通知为准。"
        description = f"{year}年放假安排（待公布）与调休日历。"
    return _page(
        request,
        template="fangjia.html",
        title=f"{year}年放假安排与调休日历 - 万年历",
        description=description,
        path=f"/fangjia/{year}",
        heading=f"{year}年放假安排与调休",
        year=year,
        faqs=faqs,
        breadcrumbs=[("万年历", "/"), (f"{year}年放假安排", f"/fangjia/{year}")],
        extra={
            "lead": lead,
            "periods": periods,
            "months": months,
            "ics_href": f"/fangjia/{year}.ics" if periods else None,
        },
    )


def _urlset(entries: list[tuple[str, str, str]]) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, freq, prio in entries:
        loc = escape(f"{SITE_URL}{path}")
        parts.append(
            f"<url><loc>{loc}</loc><changefreq>{freq}</changefreq><priority>{prio}</priority></url>"
        )
    parts.append("</urlset>")
    return "\n".join(parts)


_SITEMAP_INDEX = "\n".join(
    [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f"<sitemap><loc>{escape(SITE_URL)}/sitemap-core.xml</loc></sitemap>",
        f"<sitemap><loc>{escape(SITE_URL)}/sitemap-months.xml</loc></sitemap>",
        f"<sitemap><loc>{escape(SITE_URL)}/sitemap-jieqi.xml</loc></sitemap>",
        "</sitemapindex>",
    ]
)


@lru_cache(maxsize=8)
def _sitemap_urlset(kind: str, current: int, upper: int, holiday_key: str) -> str:
    holidays = [int(item) for item in holiday_key.split(",") if item]
    entries: list[tuple[str, str, str]] = []
    if kind == "core":
        entries.append(("/", "daily", "1.0"))
        for year in holidays:
            entries.append(
                (f"/fangjia/{year}", "weekly" if year == current else "yearly", "0.9")
            )
        for year in range(MIN_YEAR, upper + 1):
            freq = "weekly" if year == current else "yearly"
            prio = "0.8" if year == current else "0.5"
            entries.append((f"/y/{year}", freq, prio))
            entries.append((f"/jieqi/{year}", freq, prio))
    elif kind == "months":
        for year in range(MIN_YEAR, upper + 1):
            freq = "weekly" if year == current else "yearly"
            prio = "0.6" if year == current else "0.4"
            for month in range(1, 13):
                entries.append((f"/y/{year}/m/{month}", freq, prio))
    elif kind == "jieqi":
        slugs = tuple(JIEQI_SLUG.values())
        for year in range(MIN_YEAR, upper + 1):
            freq = "weekly" if year == current else "yearly"
            prio = "0.6" if year == current else "0.4"
            for slug in slugs:
                entries.append((f"/jieqi/{year}/{slug}", freq, prio))
    else:
        raise KeyError(kind)
    return _urlset(entries)


def _sitemap_xml(kind: str) -> str:
    if kind == "index":
        return _SITEMAP_INDEX
    return _sitemap_urlset(
        kind,
        date.today().year,
        max_year(),
        ",".join(str(year) for year in holiday_years()),
    )


def _sitemap_response(kind: str) -> PlainTextResponse:
    return PlainTextResponse(
        _sitemap_xml(kind),
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.api_route("/sitemap.xml", methods=["GET", "HEAD"])
@limiter.limit("120/minute")
async def sitemap_index(request: Request) -> PlainTextResponse:
    return _sitemap_response("index")


@router.api_route("/sitemap-core.xml", methods=["GET", "HEAD"])
@limiter.limit("120/minute")
async def sitemap_core(request: Request) -> PlainTextResponse:
    return _sitemap_response("core")


@router.api_route("/sitemap-months.xml", methods=["GET", "HEAD"])
@limiter.limit("120/minute")
async def sitemap_months(request: Request) -> PlainTextResponse:
    return _sitemap_response("months")


@router.api_route("/sitemap-jieqi.xml", methods=["GET", "HEAD"])
@limiter.limit("120/minute")
async def sitemap_jieqi(request: Request) -> PlainTextResponse:
    return _sitemap_response("jieqi")
