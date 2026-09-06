import type { CalendarResponse, HolidaysResponse, MetaResponse } from './types'

export function isAbortError(err: unknown): boolean {
  if (err instanceof DOMException && err.name === 'AbortError') {
    return true
  }
  return err instanceof Error && err.name === 'AbortError'
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal })
  if (response.ok === false) {
    let message = `请求失败 (${response.status})`
    try {
      const err = await response.json()
      if (err?.message) {
        message = err.message
      }
    } catch (parseErr: unknown) {
      if (isAbortError(parseErr)) {
        throw parseErr
      }
    }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export function fetchMeta(): Promise<MetaResponse> {
  return getJson<MetaResponse>('/api/v1/meta')
}

export function fetchCalendar(
  year: number,
  month: number,
  signal?: AbortSignal,
): Promise<CalendarResponse> {
  return getJson<CalendarResponse>(
    `/api/v1/calendar?year=${year}&month=${month}`,
    signal,
  )
}

export function fetchHolidays(
  year: number,
  signal?: AbortSignal,
): Promise<HolidaysResponse> {
  return getJson<HolidaysResponse>(`/api/v1/holidays?year=${year}`, signal)
}
