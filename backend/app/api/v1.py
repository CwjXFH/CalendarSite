import hmac
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import MIN_YEAR, max_year
from app.schemas import (
    CalendarResponse,
    DayDetailResponse,
    HealthResponse,
    HolidayDayIn,
    HolidayDayOut,
    HolidayPeriodOut,
    HolidaysResponse,
    MetaResponse,
    OpsHolidaysResponse,
)
from app.services.calendar import get_calendar_cached, get_day_detail
from app.services.holiday import (
    delete_holiday_day,
    group_holiday_periods,
    list_holiday_days,
    upsert_holiday_day,
)

router = APIRouter(prefix="/api/v1")
limiter = Limiter(key_func=get_remote_address)


@router.get("/health", response_model=HealthResponse)
@limiter.limit("120/minute")
async def health(request: Request, response: Response) -> HealthResponse:
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse(status="ok")


@router.get("/meta", response_model=MetaResponse)
@limiter.limit("120/minute")
async def meta(request: Request, response: Response) -> MetaResponse:
    response.headers["Cache-Control"] = "public, max-age=86400"
    return MetaResponse(minYear=MIN_YEAR, maxYear=max_year())


@router.get("/calendar", response_model=CalendarResponse)
@limiter.limit("60/minute")
async def calendar(
    request: Request,
    response: Response,
    year: int = Query(..., description="公历年"),
    month: int = Query(..., ge=1, le=12, description="公历月"),
) -> CalendarResponse:
    upper = max_year()
    if year < MIN_YEAR or year > upper:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_YEAR",
                "message": f"year must be between {MIN_YEAR} and {upper}",
            },
        )
    response.headers["Cache-Control"] = "public, max-age=86400"
    return get_calendar_cached(year, month)


@router.get("/day", response_model=DayDetailResponse)
@limiter.limit("60/minute")
async def day(
    request: Request,
    response: Response,
    date: str = Query(..., description="公历日期 YYYY-MM-DD"),
) -> DayDetailResponse:
    try:
        current = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_DATE", "message": "date must be YYYY-MM-DD"},
        )
    upper = max_year()
    if current.year < MIN_YEAR or current.year > upper:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_YEAR",
                "message": f"year must be between {MIN_YEAR} and {upper}",
            },
        )
    response.headers["Cache-Control"] = "public, max-age=86400"
    return get_day_detail(current)


@router.get("/holidays", response_model=HolidaysResponse)
@limiter.limit("60/minute")
async def holidays(
    request: Request,
    response: Response,
    year: int = Query(..., description="公历年"),
) -> HolidaysResponse:
    upper = max_year()
    if year < MIN_YEAR or year > upper:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_YEAR",
                "message": f"year must be between {MIN_YEAR} and {upper}",
            },
        )
    response.headers["Cache-Control"] = "public, max-age=86400"
    periods = [
        HolidayPeriodOut(
            name=period.name,
            start=period.start.isoformat(),
            end=period.end.isoformat(),
            days=period.days,
            makeup=[day.isoformat() for day in period.makeup],
        )
        for period in group_holiday_periods(year)
    ]
    return HolidaysResponse(year=year, periods=periods)


def _require_ops(request: Request) -> None:
    expected = os.environ.get("OPS_TOKEN", "")
    got = request.headers.get("X-Ops-Token", "")
    if expected == "" or hmac.compare_digest(got, expected) is False:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "unauthorized"},
        )


@router.get("/ops/holidays", response_model=OpsHolidaysResponse)
@limiter.limit("60/minute")
async def ops_list_holidays(
    request: Request,
    year: int = Query(..., description="公历年"),
) -> OpsHolidaysResponse:
    _require_ops(request)
    days = [HolidayDayOut(**row) for row in list_holiday_days(year)]
    return OpsHolidaysResponse(year=year, days=days)


@router.put("/ops/holidays")
@limiter.limit("60/minute")
async def ops_upsert_holiday(request: Request, body: HolidayDayIn) -> dict[str, bool]:
    _require_ops(request)
    try:
        upsert_holiday_day(body.date, body.kind, body.name)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_HOLIDAY", "message": "invalid date or kind"},
        )
    return {"ok": True}


@router.delete("/ops/holidays")
@limiter.limit("60/minute")
async def ops_delete_holiday(
    request: Request,
    date: str = Query(..., description="公历日期 YYYY-MM-DD"),
) -> dict[str, bool]:
    _require_ops(request)
    try:
        delete_holiday_day(date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_DATE", "message": "date must be YYYY-MM-DD"},
        )
    return {"ok": True}
