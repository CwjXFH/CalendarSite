import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import {
  clippedList,
  daysBetween,
  formatTermLine,
  isoDate,
  lunarParts,
  monthLandingDate,
  nextHolidayBar,
  parseDateQuery,
  parseHomeQuery,
  resolveSearch,
} from './src/logic.ts'

const today = new Date(2026, 8, 6)

assert.deepEqual(parseDateQuery('2026-10-01', today), { y: 2026, m: 10, d: 1 })
assert.deepEqual(parseDateQuery('9月25日', today), { y: 2026, m: 9, d: 25 })
assert.equal(parseDateQuery('白露', today), null)
assert.equal(daysBetween('2026-09-06', '2026-10-01'), 25)

const periods = [
  { name: '中秋', start: '2026-09-25', end: '2026-09-27', days: 3, makeup: [] },
  { name: '国庆', start: '2026-10-01', end: '2026-10-07', days: 7, makeup: ['2026-09-20'] },
]
const bar = nextHolidayBar(periods, '2026-09-06')
assert.equal(bar?.period.name, '国庆')
assert.equal(bar?.long, true)
assert.equal(nextHolidayBar(periods, '2026-10-08'), null)

const q = parseHomeQuery('?y=2026&m=9&q=白露')
assert.deepEqual(q, { y: 2026, m: 9, d: null, date: null, q: '白露' })
assert.equal(resolveSearch('白露', today, 2026, [], [])?.href, '/jieqi/2026/bailu')
assert.deepEqual(
  resolveSearch('国庆', today, 2026, [], periods)?.ymd,
  { y: 2026, m: 10, d: 1 },
)
assert.deepEqual(
  resolveSearch('中秋', today, 2026, [], periods)?.ymd,
  { y: 2026, m: 9, d: 25 },
)
assert.deepEqual(
  resolveSearch('中秋节', today, 2026, [], periods)?.ymd,
  { y: 2026, m: 9, d: 25 },
)
assert.equal(resolveSearch('不存在的节', today, 2026, [], periods), null)

assert.deepEqual(
  lunarParts({
    date: '2026-09-24',
    day: 24,
    lunarText: '十四',
    lunarYearMonth: '丙午年八月',
    festival: null,
    solarTerm: null,
    isWeekend: false,
    isLegalHoliday: false,
    isMakeupWorkday: false,
    isCurrentMonth: true,
  }),
  { ganZhi: '丙午年', monthDay: '八月十四' },
)

assert.deepEqual(clippedList(['a', 'b', 'c'], false, 2), { shown: ['a', 'b'], rest: 1 })
assert.deepEqual(clippedList(['a', 'b', 'c'], true, 2), { shown: ['a', 'b', 'c'], rest: 0 })
assert.deepEqual(clippedList([], false), { shown: [], rest: 0 })
assert.equal(
  formatTermLine({ name: '秋分', date: '2026-09-23', time: '21:04', passed: true }, '2026-09-24'),
  '秋分（已过） 9月23日 21:04',
)
assert.equal(
  formatTermLine({ name: '白露', date: '2026-09-07', time: '22:41', passed: false }, '2026-09-06'),
  '白露（未至） 9月7日 22:41',
)
assert.equal(
  formatTermLine({ name: '秋分', date: '2026-09-23', time: '08:05', passed: false }, '2026-09-23'),
  '秋分（当日） 9月23日 08:05',
)

assert.equal(isoDate(2026, 2, 31), '2026-02-28')
assert.equal(monthLandingDate(2026, 9, today), '2026-09-06')
assert.equal(monthLandingDate(2026, 4, today), '2026-04-06')
assert.notEqual(monthLandingDate(2026, 4, today), '2026-04-01')
assert.equal(monthLandingDate(2026, 10, today, '2026-09-24'), '2026-10-24')
assert.equal(monthLandingDate(2026, 2, today, '2026-01-31'), '2026-02-28')

const appTsx = readFileSync(new URL('./src/App.tsx', import.meta.url), 'utf8')
assert.match(appTsx, /import ['"]dayjs\/locale\/zh-cn['"]/)
assert.match(appTsx, /dayjs\.locale\(['"]zh-cn['"]\)/)
assert.match(appTsx, /locale=\{zhCN\}/)

dayjs.locale('zh-cn')
assert.equal(dayjs('2026-09-01').format('MMM'), '9月')
assert.equal(dayjs('2026-09-07').format('dd'), '一')
assert.equal(dayjs('2026-09-06').format('dddd'), '星期日')

const css = readFileSync(new URL('./src/App.css', import.meta.url), 'utf8')
function cssToken(name: string): string {
  const match = css.match(new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6})`))
  assert.ok(match, name)
  return match[1]
}
assert.notEqual(cssToken('--today-fill'), cssToken('--work-bg'))
assert.match(css, /\.day-cell \{[\s\S]*?border-radius: 0/)
assert.match(css, /\.day-cell \{[\s\S]*?min-height: 62px/)
assert.match(css, /\.day-cell \{[\s\S]*?align-items: center/)
assert.match(css, /\.day-cell--today \{[\s\S]*?background: var\(--today-fill\)/)
assert.match(css, /\.holiday-bar__cta \{[\s\S]*?background: var\(--pink-deep\)[\s\S]*?color: #fff/)
assert.match(css, /\.day-cell--weekend \.day-cell__lunar/)
assert.doesNotMatch(css, /box-shadow: inset 0 0 0 1\.5px var\(--pink\)/)
assert.doesNotMatch(css, /\.day-cell--holiday \{[^}]*border-radius:\s*[^0;\s]/)
assert.doesNotMatch(css, /\.day-cell--work \{[^}]*border-radius:\s*[^0;\s]/)
assert.doesNotMatch(
  css,
  /\.day-cell--today:not\(\.day-cell--selected\) \.day-cell__solar \{[^}]*background: var\(--today-fill\)/,
)

console.log('logic.check ok')
