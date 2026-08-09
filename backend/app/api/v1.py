from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import MIN_YEAR, max_year
from app.schemas import CalendarResponse, HealthResponse, MetaResponse
from app.services.calendar import get_calendar_cached

router = APIRouter(prefix="/api/v1")
limiter = Limiter(key_func=get_remote_address)


@router.get("/health", response_model=HealthResponse)
@limiter.limit("120/minute")
async def health(request: Request) -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/meta", response_model=MetaResponse)
@limiter.limit("120/minute")
async def meta(request: Request) -> MetaResponse:
    return MetaResponse(minYear=MIN_YEAR, maxYear=max_year())


@router.get("/calendar", response_model=CalendarResponse)
@limiter.limit("60/minute")
async def calendar(
    request: Request,
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
    return get_calendar_cached(year, month)
