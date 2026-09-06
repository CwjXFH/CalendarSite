import { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Select, Space, Spin, message } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import { fetchCalendar, fetchHolidays, fetchMeta, isAbortError } from '../api'
import DayCellView from '../components/DayCell'
import {
  JIEQI_SLUG,
  dayStatus,
  daysBetween,
  formatMakeup,
  formatRange,
  lunarDetail,
  nextHolidayBar,
  parseDateQuery,
  parseHomeQuery,
  resolveSearch,
  todayStr,
  weekdayLabel,
} from '../logic'
import type { DayCell, HolidayPeriod } from '../types'

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']
const FETCH_DEBOUNCE_MS = 150

function applyYmd(
  ymd: { y: number; m: number; d: number },
  minYear: number,
  maxYear: number,
  setYear: (y: number) => void,
  setMonth: (m: number) => void,
  setSelected: (d: string) => void,
) {
  if (ymd.y < minYear || ymd.y > maxYear || ymd.m < 1 || ymd.m > 12) {
    return
  }
  const last = new Date(ymd.y, ymd.m, 0).getDate()
  const day = Math.min(Math.max(ymd.d, 1), last)
  setYear(ymd.y)
  setMonth(ymd.m)
  setSelected(`${ymd.y}-${String(ymd.m).padStart(2, '0')}-${String(day).padStart(2, '0')}`)
}

export default function CalendarPage() {
  const [now] = useState(() => new Date())
  const boot = parseHomeQuery(window.location.search)
  const bootDate = boot.date ? parseDateQuery(boot.date, now) : null
  const initialYear = bootDate?.y ?? boot.y ?? now.getFullYear()
  const initialMonth = bootDate?.m ?? boot.m ?? now.getMonth() + 1

  const [year, setYear] = useState(initialYear)
  const [month, setMonth] = useState(initialMonth)
  const [minYear, setMinYear] = useState(1900)
  const [maxYear, setMaxYear] = useState(now.getFullYear() + 3)
  const [days, setDays] = useState<DayCell[]>([])
  const [lunarYearMonth, setLunarYearMonth] = useState('')
  const [selected, setSelected] = useState(() => {
    if (bootDate) {
      return `${bootDate.y}-${String(bootDate.m).padStart(2, '0')}-${String(bootDate.d).padStart(2, '0')}`
    }
    if (boot.y && boot.m && boot.d) {
      return `${boot.y}-${String(boot.m).padStart(2, '0')}-${String(boot.d).padStart(2, '0')}`
    }
    if (boot.y && boot.m && (boot.y !== now.getFullYear() || boot.m !== now.getMonth() + 1)) {
      return `${boot.y}-${String(boot.m).padStart(2, '0')}-01`
    }
    return todayStr(now)
  })
  const [loading, setLoading] = useState(false)
  const [query, setQuery] = useState(boot.q)
  const [searchNote, setSearchNote] = useState<{ ok: boolean; text: string } | null>(null)
  const [periods, setPeriods] = useState<HolidayPeriod[]>([])
  const [holidaysReady, setHolidaysReady] = useState(false)
  const isFirstFetch = useRef(true)
  const bootApplied = useRef(boot.q === '')
  const today = todayStr(now)
  const todayYear = now.getFullYear()

  useEffect(() => {
    fetchMeta()
      .then((meta) => {
        setMinYear(meta.minYear)
        setMaxYear(meta.maxYear)
      })
      .catch((err: Error) => {
        message.error(err.message)
      })
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const delay = isFirstFetch.current ? 0 : FETCH_DEBOUNCE_MS
    isFirstFetch.current = false
    const timer = window.setTimeout(() => {
      setLoading(true)
      fetchCalendar(year, month, controller.signal)
        .then((data) => {
          if (controller.signal.aborted === false) {
            setDays(data.days)
            setLunarYearMonth(data.lunarYearMonth)
          }
        })
        .catch((err: unknown) => {
          if (isAbortError(err)) {
            return
          }
          const messageText = err instanceof Error ? err.message : '请求失败'
          message.error(messageText)
        })
        .finally(() => {
          if (controller.signal.aborted === false) {
            setLoading(false)
          }
        })
    }, delay)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [year, month])

  useEffect(() => {
    const controller = new AbortController()
    const years = Array.from(new Set([todayYear, year, year + 1]))
    Promise.all(years.map((y) => fetchHolidays(y, controller.signal)))
      .then((rows) => {
        if (controller.signal.aborted) {
          return
        }
        setPeriods(rows.flatMap((row) => row.periods))
        setHolidaysReady(true)
      })
      .catch((err: unknown) => {
        if (isAbortError(err)) {
          return
        }
        setHolidaysReady(true)
      })
    return () => controller.abort()
  }, [year, todayYear])

  useEffect(() => {
    setSelected((current) => {
      const [sy, sm] = current.split('-').map(Number)
      if (sy === year && sm === month) {
        return current
      }
      if (year === now.getFullYear() && month === now.getMonth() + 1) {
        return todayStr(now)
      }
      return `${year}-${String(month).padStart(2, '0')}-01`
    })
  }, [year, month, now])

  useEffect(() => {
    if (bootApplied.current) {
      return
    }
    const dateHit = parseDateQuery(boot.q, now)
    if (dateHit) {
      applyYmd(dateHit, minYear, maxYear, setYear, setMonth, setSelected)
      bootApplied.current = true
      return
    }
    if (JIEQI_SLUG[boot.q]) {
      window.location.replace(`/jieqi/${year}/${JIEQI_SLUG[boot.q]}`)
      bootApplied.current = true
      return
    }
    if (days.length === 0 || holidaysReady === false) {
      return
    }
    const hit = resolveSearch(boot.q, now, year, days, periods)
    if (hit?.href) {
      window.location.replace(hit.href)
    } else if (hit?.ymd) {
      applyYmd(hit.ymd, minYear, maxYear, setYear, setMonth, setSelected)
      setSearchNote({ ok: true, text: `已定位到 ${hit.ymd.m}月${hit.ymd.d}日` })
    } else {
      setSearchNote({ ok: false, text: `未找到「${boot.q}」，试试日期、节日或节气名` })
    }
    bootApplied.current = true
  }, [boot.q, days, periods, holidaysReady, minYear, maxYear, year, now])

  const yearOptions = Array.from({ length: maxYear - minYear + 1 }, (_, i) => {
    const value = minYear + i
    return { value, label: `${value}年` }
  })

  const monthOptions = Array.from({ length: 12 }, (_, i) => ({
    value: i + 1,
    label: `${i + 1}月`,
  }))

  function shiftMonth(delta: number) {
    const date = new Date(year, month - 1 + delta, 1)
    const nextYear = date.getFullYear()
    const nextMonth = date.getMonth() + 1
    if (nextYear < minYear || nextYear > maxYear) {
      return
    }
    setYear(nextYear)
    setMonth(nextMonth)
  }

  function onSearch(raw: string) {
    const q = raw.trim()
    if (q === '') {
      setSearchNote(null)
      return
    }
    const hit = resolveSearch(q, now, year, days, periods)
    if (hit?.href) {
      setSearchNote({ ok: true, text: `正在打开「${q}」` })
      window.location.href = hit.href
      return
    }
    if (hit?.ymd) {
      applyYmd(hit.ymd, minYear, maxYear, setYear, setMonth, setSelected)
      setSearchNote({ ok: true, text: `已定位到 ${hit.ymd.m}月${hit.ymd.d}日` })
      return
    }
    setSearchNote({ ok: false, text: `未找到「${q}」，试试日期、节日或节气名` })
  }

  const selectedCell = days.find((d) => d.date === selected)
  const headerLunar = selectedCell?.lunarYearMonth || lunarYearMonth
  const holidayBar = useMemo(() => nextHolidayBar(periods, today), [periods, today])

  const nearby = days
    .filter((d) => d.date > selected && (d.festival || d.solarTerm || d.isLegalHoliday))
    .slice(0, 3)
  const monthPoints = days.filter(
    (d) => d.isCurrentMonth && (d.solarTerm || d.isLegalHoliday || d.festival),
  )
  const titleExtra = selectedCell?.festival || selectedCell?.solarTerm

  return (
    <div className="page">
      <header className="site-header">
        <a className="site-brand" href="/">
          <span className="site-logo" aria-hidden="true" />
          <span className="site-brand__text">
            <span className="site-name">万年历</span>
            {headerLunar ? <span className="site-lunar">{headerLunar}</span> : null}
          </span>
        </a>
        <div className="site-search-wrap">
          <form
            className="site-search"
            role="search"
            onSubmit={(ev) => {
              ev.preventDefault()
              onSearch(query)
            }}
          >
            <span className="site-search__icon" aria-hidden="true" />
            <input
              type="search"
              value={query}
              onChange={(ev) => {
                setQuery(ev.target.value)
                setSearchNote(null)
              }}
              placeholder="搜索日期 / 节日 / 节气"
              aria-label="搜索日期、节日或节气"
            />
          </form>
          {searchNote ? (
            <p className={`site-search__note${searchNote.ok ? ' is-ok' : ' is-empty'}`} role="status">
              {searchNote.text}
            </p>
          ) : null}
        </div>
        <nav className="site-nav" aria-label="站点">
          <a href="/" className="is-active">
            月历
          </a>
          <a href={`/y/${year}`}>年历</a>
          <a href={`/fangjia/${year}`}>
            <span className="nav-full">放假安排</span>
            <span className="nav-short">放假</span>
          </a>
          <a href={`/jieqi/${year}`}>
            <span className="nav-full">二十四节气</span>
            <span className="nav-short">节气</span>
          </a>
        </nav>
      </header>

      <section className="holiday-bar" aria-label="下一个假期">
        {holidayBar ? (
          <>
            <span className="holiday-bar__tag">
              {holidayBar.long ? '下一个长假' : '下一个假期'}
            </span>
            <div className="holiday-bar__main">
              <strong>
                {holidayBar.period.name} · 还有 {daysBetween(today, holidayBar.period.start)} 天
              </strong>
              <span>
                {formatRange(holidayBar.period.start, holidayBar.period.end)} · 共{' '}
                {holidayBar.period.days} 天
                {holidayBar.period.makeup.length > 0
                  ? ` · ${formatMakeup(holidayBar.period.makeup)} 调休上班`
                  : ''}
              </span>
            </div>
            <a className="holiday-bar__cta" href={`/fangjia/${holidayBar.period.start.slice(0, 4)}`}>
              查看放假安排
            </a>
          </>
        ) : (
          <>
            <span className="holiday-bar__tag">放假安排</span>
            <div className="holiday-bar__main">
              <strong>暂未公布后续长假</strong>
              <span>以国务院办公厅通知为准</span>
            </div>
            <a className="holiday-bar__cta" href={`/fangjia/${year}`}>
              查看放假安排
            </a>
          </>
        )}
      </section>

      <section className="cal-stage">
        <div className="cal-stage__toolbar">
          <Space wrap>
            <Select value={year} options={yearOptions} onChange={setYear} style={{ width: 112 }} />
            <Select value={month} options={monthOptions} onChange={setMonth} style={{ width: 88 }} />
            <Button icon={<LeftOutlined />} onClick={() => shiftMonth(-1)} />
            <Button icon={<RightOutlined />} onClick={() => shiftMonth(1)} />
            <Button
              onClick={() => {
                const n = new Date()
                setYear(n.getFullYear())
                setMonth(n.getMonth() + 1)
                setSelected(todayStr(n))
              }}
            >
              今天
            </Button>
          </Space>
          <ul className="legend">
            <li>
              <i className="legend__dot legend__dot--weekend" />
              周末
            </li>
            <li>
              <i className="legend__dot legend__dot--holiday" />
              法定假
            </li>
            <li>
              <i className="legend__dot legend__dot--work" />
              调休班
            </li>
            <li>
              <i className="legend__dot legend__dot--term" />
              节气
            </li>
          </ul>
        </div>
        <Spin spinning={loading}>
          <div className="calendar">
            <div className="calendar__weekdays">
              {WEEKDAYS.map((w) => (
                <div key={w} className="calendar__weekday">
                  {w}
                </div>
              ))}
            </div>
            <div className="calendar__grid">
              {days.map((cell) => (
                <DayCellView
                  key={cell.date}
                  cell={cell}
                  isToday={cell.date === today}
                  isSelected={cell.date === selected}
                  onSelect={setSelected}
                />
              ))}
            </div>
          </div>
        </Spin>
      </section>

      <section className="day-card" aria-live="polite">
        <div className="day-card__when">
          <h2>
            {selectedCell
              ? `${Number(selected.slice(5, 7))}月${selectedCell.day}日 · ${weekdayLabel(selected)}`
              : selected}
            {titleExtra ? ` · ${titleExtra}` : ''}
          </h2>
          <p>
            {selectedCell ? lunarDetail(selectedCell) : headerLunar}
            {selected === today ? ' · 今天' : ''}
          </p>
        </div>
        <div className="day-card__cols">
          <div>
            <h3>临近</h3>
            {nearby.length > 0 ? (
              <ul>
                {nearby.map((cell) => {
                  const name = cell.festival || cell.solarTerm || '节日'
                  const delta = daysBetween(selected, cell.date)
                  const label = delta === 1 ? `明天${name}` : `距${name} ${delta} 天`
                  return <li key={`${cell.date}-${name}`}>{label}</li>
                })}
              </ul>
            ) : (
              <p>本月余下暂无节日或节气</p>
            )}
          </div>
          <div>
            <h3>本月</h3>
            {monthPoints.length > 0 ? (
              <ul>
                {monthPoints.map((cell) => (
                  <li key={`${cell.date}-m`}>
                    {cell.day}日 {cell.festival || cell.solarTerm || '法定假日'}
                  </li>
                ))}
              </ul>
            ) : (
              <p>本月暂无节气或法定假日</p>
            )}
          </div>
          <div>
            <h3>状态</h3>
            <p>{selectedCell ? dayStatus(selectedCell) : '—'}</p>
          </div>
        </div>
        <div className="day-card__actions">
          <a
            className="day-card__btn"
            href={
              selectedCell?.solarTerm && JIEQI_SLUG[selectedCell.solarTerm]
                ? `/jieqi/${year}/${JIEQI_SLUG[selectedCell.solarTerm]}`
                : `/jieqi/${year}`
            }
          >
            查看节气
          </a>
          <a className="day-card__btn day-card__btn--solid" href={`/fangjia/${year}`}>
            放假安排
          </a>
        </div>
      </section>

      <footer className="page__footer">
        <a href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer">
          沪ICP备2026041562号-1
        </a>
        <a
          className="page__footer-mps"
          href="https://beian.mps.gov.cn/#/query/webSearch?code=31011302009659"
          target="_blank"
          rel="noreferrer"
        >
          <img src="/备案图标.png" alt="" />
          沪公网安备31011302009659号
        </a>
      </footer>
    </div>
  )
}
