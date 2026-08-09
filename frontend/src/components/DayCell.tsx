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
  } else if (cell.isWeekend && cell.isMakeupWorkday === false) {
    classes.push('day-cell--weekend')
  }
  if (isToday) {
    classes.push('day-cell--today')
  }
  if (isSelected) {
    classes.push('day-cell--selected')
  }

  const badge = badgeText(cell)

  return (
    <button
      type="button"
      className={classes.join(' ')}
      onClick={() => onSelect(cell.date)}
      aria-label={cell.date}
    >
      <span className="day-cell__solar">{cell.day}</span>
      <span className="day-cell__lunar">{badge ?? cell.lunarText}</span>
    </button>
  )
}
