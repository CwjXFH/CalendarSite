from __future__ import annotations

from app.db.database import get_connection


def get_holiday_map(start_date: str, end_date: str) -> dict[str, str]:
    """返回 date -> kind（holiday / workday）。"""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT date, kind
            FROM holiday_days
            WHERE date >= ? AND date <= ?
            """,
            (start_date, end_date),
        ).fetchall()
    return {row["date"]: row["kind"] for row in rows}
