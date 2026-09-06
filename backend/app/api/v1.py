from fastapi import APIRouter, HTTPException, Query, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import MIN_YEAR, max_year
from app.schemas import (
    CalendarResponse,
    HealthResponse,
    HolidayPeriodOut,
    HolidaysResponse,
    MetaResponse,
)
from app.services.calendar import get_calendar_cached
from app.services.holiday import group_holiday_periods

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
