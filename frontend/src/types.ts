export interface DayCell {
  date: string
  day: number
  lunarText: string
  lunarYearMonth: string
  festival: string | null
  solarTerm: string | null
  isWeekend: boolean
  isLegalHoliday: boolean
  isMakeupWorkday: boolean
  isCurrentMonth: boolean
}

export interface CalendarResponse {
  year: number
  month: number
  lunarYearMonth: string
  days: DayCell[]
}

export interface MetaResponse {
  minYear: number
  maxYear: number
}

export interface HolidayPeriod {
  name: string
  start: string
  end: string
  days: number
  makeup: string[]
}

export interface HolidaysResponse {
  year: number
  periods: HolidayPeriod[]
}

export interface ApiError {
  code: string
  message: string
}

export interface HomeQuery {
  y: number | null
  m: number | null
  d: number | null
  date: string | null
  q: string
}

export interface Ymd {
  y: number
  m: number
  d: number
}
