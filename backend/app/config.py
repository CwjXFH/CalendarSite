from datetime import date

MIN_YEAR = 1900
SITE_URL = "https://wannianli.site"
SITE_NAME = "万年历"


def max_year(today: date | None = None) -> int:
    current = today or date.today()
    return current.year + 3
