from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from functools import lru_cache

from app.schemas import CalendarResponse, DayCell
from app.services.holiday import get_holiday_map
from app.services.lunar import get_day_info


def _month_grid_start(year: int, month: int) -> date:
    first = date(year, month, 1)
    # 周一起始：周一=0 ... 周日=6
    weekday = first.weekday()
    return first - timedelta(days=weekday)


def _build_days(year: int, month: int) -> list[DayCell]:
    start = _month_grid_start(year, month)
    days: list[DayCell] = []

    end = start + timedelta(days=41)
    holiday_map = get_holiday_map(start.isoformat(), end.isoformat())

    for offset in range(42):
        current = start + timedelta(days=offset)
        info = get_day_info(current.year, current.month, current.day)
        date_str = current.isoformat()
        kind = holiday_map.get(date_str)
        is_weekend = current.weekday() >= 5

        days.append(
            DayCell(
                date=date_str,
                day=current.day,
                lunarText=str(info["lunarText"]),
                lunarYearMonth=str(info["lunarYearMonth"]),
                festival=info["festival"],
                solarTerm=info["solarTerm"],
                isWeekend=is_weekend,
                isLegalHoliday=kind == "holiday",
                isMakeupWorkday=kind == "workday",
                isCurrentMonth=current.month == month and current.year == year,
            )
        )

    return days


@lru_cache(maxsize=256)
def get_calendar_cached(year: int, month: int) -> CalendarResponse:
    days = _build_days(year, month)
    target_day = min(15, monthrange(year, month)[1])
    header = next(d for d in days if d.isCurrentMonth and d.day == target_day)
    return CalendarResponse(
        year=year,
        month=month,
        lunarYearMonth=header.lunarYearMonth,
        days=days,
    )


def clear_calendar_cache() -> None:
    get_calendar_cached.cache_clear()
