from datetime import date

MIN_YEAR = 1900


def max_year(today: date | None = None) -> int:
    current = today or date.today()
    return current.year + 3
