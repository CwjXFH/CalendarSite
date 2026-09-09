from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from functools import lru_cache

from app.db.database import db_path
from app.schemas import CalendarResponse, DayCell, DayDetailResponse, NearestTerm
from app.services.holiday import get_holiday_map
from app.services.jieqi import JieqiItem, jieqi_around, nearest_jieqi
from app.services.lunar import get_day_info


def _month_grid_start(year: int, month: int) -> date:
    first = date(year, month, 1)
    # 周一起始：周一=0 ... 周日=6
    weekday = first.weekday()
    return first - timedelta(days=weekday)


def _nearest_out(current: date, terms: tuple[JieqiItem, ...]) -> NearestTerm | None:
    found = nearest_jieqi(current, terms)
    if found is None:
        return None
    item, passed = found
    return NearestTerm(
        name=item.name,
        slug=item.slug,
        date=item.when.isoformat(),
        time=item.time_text,
        passed=passed,
    )


def _cell_from_info(
    current: date,
    info: dict,
    kind: str | None,
    terms: tuple[JieqiItem, ...],
    month: int | None = None,
    year: int | None = None,
) -> DayCell:
    return DayCell(
        date=current.isoformat(),
        day=current.day,
        lunarText=str(info["lunarText"]),
        lunarYearMonth=str(info["lunarYearMonth"]),
        lunarMonthDay=str(info["lunarMonthDay"]),
        ganZhi=str(info["ganZhi"]),
        festival=info["festival"],
        solarTerm=info["solarTerm"],
        yi=list(info["yi"]),
        ji=list(info["ji"]),
        nearestTerm=_nearest_out(current, terms),
        isWeekend=current.weekday() >= 5,
        isLegalHoliday=kind == "holiday",
        isMakeupWorkday=kind == "workday",
        isCurrentMonth=(
            month is not None
            and year is not None
            and current.month == month
            and current.year == year
        ),
    )


def _build_days(year: int, month: int) -> list[DayCell]:
    start = _month_grid_start(year, month)
    days: list[DayCell] = []

    end = start + timedelta(days=41)
    holiday_map = get_holiday_map(start.isoformat(), end.isoformat())
    terms = jieqi_around(year)

    for offset in range(42):
        current = start + timedelta(days=offset)
        info = get_day_info(current.year, current.month, current.day)
        days.append(
            _cell_from_info(
                current,
                info,
                holiday_map.get(current.isoformat()),
                terms,
                month=month,
                year=year,
            )
        )

    return days


def get_day_detail(current: date) -> DayDetailResponse:
    info = get_day_info(current.year, current.month, current.day)
    kind = get_holiday_map(current.isoformat(), current.isoformat()).get(current.isoformat())
    cell = _cell_from_info(current, info, kind, jieqi_around(current.year))
    return DayDetailResponse(
        date=cell.date,
        year=current.year,
        month=current.month,
        day=current.day,
        weekday=str(info["weekday"]),
        lunarText=cell.lunarText,
        lunarYearMonth=cell.lunarYearMonth,
        lunarMonthDay=cell.lunarMonthDay,
        ganZhi=cell.ganZhi,
        festival=cell.festival,
        solarTerm=cell.solarTerm,
        yi=cell.yi,
        ji=cell.ji,
        nearestTerm=cell.nearestTerm,
        isWeekend=cell.isWeekend,
        isLegalHoliday=cell.isLegalHoliday,
        isMakeupWorkday=cell.isMakeupWorkday,
    )


@lru_cache(maxsize=256)
def _calendar_cached(year: int, month: int, db_mtime: float) -> CalendarResponse:
    days = _build_days(year, month)
    target_day = min(15, monthrange(year, month)[1])
    header = next(d for d in days if d.isCurrentMonth and d.day == target_day)
    return CalendarResponse(
        year=year,
        month=month,
        lunarYearMonth=header.lunarYearMonth,
        days=days,
    )


def get_calendar_cached(year: int, month: int) -> CalendarResponse:
    return _calendar_cached(year, month, db_path().stat().st_mtime)


def clear_calendar_cache() -> None:
    _calendar_cached.cache_clear()
