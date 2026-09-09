import hmac
import os

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.api.v1 import limiter
from app.services.holiday import (
    delete_holiday_day,
    list_holiday_days,
    upsert_holiday_day,
)

router = APIRouter(prefix="/api/v1")


class HolidayDayIn(BaseModel):
    date: str = Field(description="公历日期 YYYY-MM-DD")
    kind: str = Field(description="holiday 或 workday")
    name: str = Field(default="")


class HolidayDayOut(BaseModel):
    date: str
    kind: str
    name: str


class OpsHolidaysResponse(BaseModel):
    year: int
    days: list[HolidayDayOut]


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
