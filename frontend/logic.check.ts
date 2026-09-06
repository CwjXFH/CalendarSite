import assert from 'node:assert/strict'
import {
  daysBetween,
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

console.log('logic.check ok')
