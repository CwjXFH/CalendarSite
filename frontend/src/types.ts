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

export interface ApiError {
  code: string
  message: string
}
