import type { DayCell as DayCellData } from '../types'

interface Props {
  cell: DayCellData
  isToday: boolean
  isSelected: boolean
  onSelect: (date: string) => void
}

function badgeText(cell: DayCellData): string | null {
  return cell.festival ?? cell.solarTerm
}

export default function DayCellView({ cell, isToday, isSelected, onSelect }: Props) {
  const classes = ['day-cell']
  if (cell.isCurrentMonth === false) {
    classes.push('day-cell--muted')
  }
  if (cell.isLegalHoliday) {
    classes.push('day-cell--holiday')
  } else if (cell.isMakeupWorkday) {
    classes.push('day-cell--work')
  } else if (cell.isWeekend) {
    classes.push('day-cell--weekend')
  }
  if (cell.solarTerm) {
    classes.push('day-cell--term')
  }
  if (isToday) {
    classes.push('day-cell--today')
  }
  if (isSelected) {
    classes.push('day-cell--selected')
  }

  const badge = badgeText(cell)
  const lunarClass = ['day-cell__lunar']
  if (cell.festival) {
    lunarClass.push('day-cell__lunar--fest')
  } else if (cell.solarTerm) {
    lunarClass.push('day-cell__lunar--term')
  }

  return (
    <button
      type="button"
      className={classes.join(' ')}
      onClick={() => onSelect(cell.date)}
      aria-label={cell.date}
      aria-pressed={isSelected}
    >
      <span className="day-cell__solar">{cell.day}</span>
      <span className={lunarClass.join(' ')}>{badge ?? cell.lunarText}</span>
      {cell.isMakeupWorkday ? <span className="day-cell__ban">班</span> : null}
    </button>
  )
}
