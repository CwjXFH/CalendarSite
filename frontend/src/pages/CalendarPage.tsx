import { useEffect, useState } from 'react'
import { Button, Select, Space, Spin, Typography, message } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import { fetchCalendar, fetchMeta, isAbortError } from '../api'
import DayCellView from '../components/DayCell'
import type { DayCell } from '../types'

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']
const FETCH_DEBOUNCE_MS = 150

function todayStr(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export default function CalendarPage() {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [minYear, setMinYear] = useState(1900)
  const [maxYear, setMaxYear] = useState(now.getFullYear() + 3)
  const [days, setDays] = useState<DayCell[]>([])
  const [lunarYearMonth, setLunarYearMonth] = useState('')
  const [selected, setSelected] = useState(todayStr())
  const [loading, setLoading] = useState(false)
  const today = todayStr()

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
    }, FETCH_DEBOUNCE_MS)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [year, month])

  const yearOptions = Array.from({ length: maxYear - minYear + 1 }, (_, i) => {
    const value = minYear + i
    return { value, label: `${value} 年` }
  })

  const monthOptions = Array.from({ length: 12 }, (_, i) => ({
    value: i + 1,
    label: `${i + 1} 月`,
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

  const selectedCell = days.find((d) => d.date === selected)
  const headerLunar = selectedCell?.lunarYearMonth || lunarYearMonth

  return (
    <div className="page">
      <header className="page__header">
        <div className="page__brand">
          <Typography.Title level={1} className="page__title">
            万年历
          </Typography.Title>
          {headerLunar ? (
            <span className="page__lunar">{headerLunar}</span>
          ) : null}
        </div>
        <Space wrap className="page__controls">
          <Select
            value={year}
            options={yearOptions}
            onChange={setYear}
            style={{ width: 120 }}
          />
          <Select
            value={month}
            options={monthOptions}
            onChange={setMonth}
            style={{ width: 100 }}
          />
          <Button icon={<LeftOutlined />} onClick={() => shiftMonth(-1)} />
          <Button icon={<RightOutlined />} onClick={() => shiftMonth(1)} />
          <Button
            onClick={() => {
              const n = new Date()
              setYear(n.getFullYear())
              setMonth(n.getMonth() + 1)
              setSelected(todayStr())
            }}
          >
            今天
          </Button>
        </Space>
      </header>

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

      <footer className="page__footer">
        <a
          href="https://beian.miit.gov.cn/"
          target="_blank"
          rel="noreferrer"
        >
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
