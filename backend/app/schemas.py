from pydantic import BaseModel, Field


class NearestTerm(BaseModel):
    name: str
    slug: str
    date: str
    time: str
    passed: bool


class DayCell(BaseModel):
    date: str = Field(description="公历日期 YYYY-MM-DD")
    day: int = Field(description="公历日")
    lunarText: str = Field(description="农历文案")
    lunarYearMonth: str = Field(description="农历年月，如丙午年六月")
    lunarMonthDay: str = Field(default="", description="农历月日，如八月十四")
    ganZhi: str = Field(default="", description="年月日干支")
    festival: str | None = Field(default=None, description="传统节日")
    solarTerm: str | None = Field(default=None, description="二十四节气")
    yi: list[str] = Field(default_factory=list, description="黄历宜")
    ji: list[str] = Field(default_factory=list, description="黄历忌")
    nearestTerm: NearestTerm | None = Field(default=None, description="最近交节")
    isWeekend: bool = Field(description="是否自然周末")
    isLegalHoliday: bool = Field(description="是否法定节假日")
    isMakeupWorkday: bool = Field(description="是否调休补班")
    isCurrentMonth: bool = Field(description="是否属于查询月")


class DayDetailResponse(BaseModel):
    date: str
    year: int
    month: int
    day: int
    weekday: str
    lunarText: str
    lunarYearMonth: str
    lunarMonthDay: str
    ganZhi: str
    festival: str | None = None
    solarTerm: str | None = None
    yi: list[str] = Field(default_factory=list)
    ji: list[str] = Field(default_factory=list)
    nearestTerm: NearestTerm | None = None
    isWeekend: bool
    isLegalHoliday: bool
    isMakeupWorkday: bool


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


class ErrorResponse(BaseModel):
    code: str
    message: str


class HealthResponse(BaseModel):
    status: str
