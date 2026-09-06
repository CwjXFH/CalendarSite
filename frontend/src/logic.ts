import type { DayCell, HolidayPeriod, HomeQuery, Ymd } from './types'

export const JIEQI_SLUG: Record<string, string> = {
  小寒: 'xiaohan',
  大寒: 'dahan',
  立春: 'lichun',
  雨水: 'yushui',
  惊蛰: 'jingzhe',
  春分: 'chunfen',
  清明: 'qingming',
  谷雨: 'guyu',
  立夏: 'lixia',
  小满: 'xiaoman',
  芒种: 'mangzhong',
  夏至: 'xiazhi',
  小暑: 'xiaoshu',
  大暑: 'dashu',
  立秋: 'liqiu',
  处暑: 'chushu',
  白露: 'bailu',
  秋分: 'qiufen',
  寒露: 'hanlu',
  霜降: 'shuangjiang',
  立冬: 'lidong',
  小雪: 'xiaoxue',
  大雪: 'daxue',
  冬至: 'dongzhi',
}

const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六']

export function todayStr(now = new Date()): string {
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function weekdayLabel(date: string): string {
  const dt = new Date(`${date}T12:00:00`)
  return `星期${WEEKDAYS[dt.getDay()]}`
}

export function daysBetween(from: string, to: string): number {
  const a = new Date(`${from}T12:00:00`)
  const b = new Date(`${to}T12:00:00`)
  return Math.round((b.getTime() - a.getTime()) / 86400000)
}

export function parseHomeQuery(search: string): HomeQuery {
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search)
  const num = (key: string) => {
    const raw = params.get(key)
    if (raw == null || raw === '') {
      return null
    }
    const value = Number(raw)
    return Number.isInteger(value) ? value : null
  }
  return {
    y: num('y'),
    m: num('m'),
    d: num('d'),
    date: params.get('date'),
    q: (params.get('q') ?? '').trim(),
  }
}

export function parseDateQuery(q: string, today: Date): Ymd | null {
  const text = q.trim()
  if (text === '') {
    return null
  }
  const iso = text.match(/^(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})日?$/)
  if (iso) {
    return { y: Number(iso[1]), m: Number(iso[2]), d: Number(iso[3]) }
  }
  const md = text.match(/^(\d{1,2})[-/.月](\d{1,2})日?$/)
  if (md) {
    return { y: today.getFullYear(), m: Number(md[1]), d: Number(md[2]) }
  }
  return null
}

export function nextHolidayBar(
  periods: HolidayPeriod[],
  today: string,
  minLongDays = 5,
): { period: HolidayPeriod; long: boolean } | null {
  const upcoming = periods
    .filter((p) => p.start > today)
    .slice()
    .sort((a, b) => a.start.localeCompare(b.start))
  const longOnes = upcoming.filter((p) => p.days >= minLongDays)
  if (longOnes.length > 0) {
    return { period: longOnes[0], long: true }
  }
  if (upcoming.length > 0) {
    return { period: upcoming[0], long: false }
  }
  return null
}

export function formatRange(start: string, end: string): string {
  const a = start.split('-')
  const b = end.split('-')
  return `${Number(a[1])}/${Number(a[2])}-${Number(b[1])}/${Number(b[2])}`
}

export function formatMakeup(dates: string[]): string {
  return dates
    .map((iso) => {
      const [, m, d] = iso.split('-')
      return `${Number(m)}/${Number(d)}`
    })
    .join('、')
}

export function lunarDetail(cell: DayCell): string {
  const ganZhi = cell.lunarYearMonth.slice(0, cell.lunarYearMonth.indexOf('年'))
  const lunarMonth = cell.lunarYearMonth.slice(cell.lunarYearMonth.indexOf('年') + 1)
  const lunarDay = cell.lunarText.endsWith('月') ? '初一' : cell.lunarText
  return `农历${lunarMonth}${lunarDay} · ${ganZhi}年`
}

export function dayStatus(cell: DayCell): string {
  if (cell.isLegalHoliday && cell.isWeekend) {
    return '法定假日 · 周末'
  }
  if (cell.isLegalHoliday) {
    return '法定假日'
  }
  if (cell.isMakeupWorkday) {
    return '调休上班'
  }
  if (cell.isWeekend) {
    return '周末 · 非调休上班'
  }
  return '工作日'
}

export function resolveSearch(
  q: string,
  today: Date,
  year: number,
  days: DayCell[],
  periods: HolidayPeriod[],
): { href?: string; ymd?: Ymd } | null {
  const date = parseDateQuery(q, today)
  if (date) {
    return { ymd: date }
  }
  if (JIEQI_SLUG[q]) {
    return { href: `/jieqi/${year}/${JIEQI_SLUG[q]}` }
  }
  const dayHit = days.find(
    (cell) => cell.festival === q || cell.solarTerm === q,
  )
  if (dayHit) {
    const [y, m, d] = dayHit.date.split('-').map(Number)
    return { ymd: { y, m, d } }
  }
  const holiday = periods.find((p) => p.name.includes(q) || q.includes(p.name))
  if (holiday) {
    const [y, m, d] = holiday.start.split('-').map(Number)
    return { ymd: { y, m, d } }
  }
  return null
}
