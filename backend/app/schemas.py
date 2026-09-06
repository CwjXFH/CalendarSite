from pydantic import BaseModel, Field


class DayCell(BaseModel):
    date: str = Field(description="公历日期 YYYY-MM-DD")
    day: int = Field(description="公历日")
    lunarText: str = Field(description="农历文案")
    lunarYearMonth: str = Field(description="农历年月，如丙午年六月")
    festival: str | None = Field(default=None, description="传统节日")
    solarTerm: str | None = Field(default=None, description="二十四节气")
    isWeekend: bool = Field(description="是否自然周末")
    isLegalHoliday: bool = Field(description="是否法定节假日")
    isMakeupWorkday: bool = Field(description="是否调休补班")
    isCurrentMonth: bool = Field(description="是否属于查询月")


class CalendarResponse(BaseModel):
    year: int
    month: int
    lunarYearMonth: str = Field(description="农历年月，如丙午年六月")
    days: list[DayCell]


class MetaResponse(BaseModel):
    minYear: int
    maxYear: int


class HolidayPeriodOut(BaseModel):
    name: str
    start: str
    end: str
    days: int
    makeup: list[str]


class HolidaysResponse(BaseModel):
    year: int
    periods: list[HolidayPeriodOut]


class ErrorResponse(BaseModel):
    code: str
    message: str


class HealthResponse(BaseModel):
    status: str
