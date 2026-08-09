import type { CalendarResponse, MetaResponse } from './types'

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (response.ok === false) {
    let message = `请求失败 (${response.status})`
    try {
      const err = await response.json()
      if (err?.message) {
        message = err.message
      }
    } catch {
      // ignore parse error
    }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export function fetchMeta(): Promise<MetaResponse> {
  return getJson<MetaResponse>('/api/v1/meta')
}

export function fetchCalendar(year: number, month: number): Promise<CalendarResponse> {
  return getJson<CalendarResponse>(`/api/v1/calendar?year=${year}&month=${month}`)
}
