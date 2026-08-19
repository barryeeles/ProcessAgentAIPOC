"""Shared date and Delivery Increment utilities used across scoring modules."""
from __future__ import annotations

import calendar
import re
from datetime import date


def parse_di(di_str) -> tuple[int, int] | None:
    """Parse 'DI26.2' -> (26, 2). Returns None if unparseable."""
    if not di_str:
        return None
    m = re.match(r"DI(\d{2})\.([1-4])", str(di_str).strip(), re.IGNORECASE)
    return (int(m.group(1)), int(m.group(2))) if m else None


def di_quarter_bounds(fy2: int, quarter: int, fiscal_start_month: int = 4) -> tuple[date, date]:
    """
    Return (start, end) for a DI quarter.

    UK fiscal convention: FY26 = April 2025 – March 2026.
      DI26.1 = Apr 2025 – Jun 2025
      DI26.2 = Jul 2025 – Sep 2025
      DI26.3 = Oct 2025 – Dec 2025
      DI26.4 = Jan 2026 – Mar 2026
    """
    fy_full = 2000 + fy2
    base_month = fiscal_start_month + (quarter - 1) * 3  # raw month number (may exceed 12)
    base_year = fy_full - 1

    start_year = base_year + (base_month - 1) // 12
    start_month = (base_month - 1) % 12 + 1

    end_base = base_month + 2
    end_year = base_year + (end_base - 1) // 12
    end_month = (end_base - 1) % 12 + 1
    _, last_day = calendar.monthrange(end_year, end_month)

    return date(start_year, start_month, 1), date(end_year, end_month, last_day)


def current_quarter_bounds(fiscal_start_month: int = 4, today: date | None = None) -> tuple[date, date]:
    """Return (start, end) for the DI quarter that contains today."""
    if today is None:
        today = date.today()
    months_into = (today.month - fiscal_start_month) % 12
    quarter = months_into // 3 + 1
    fy2 = ((today.year + 1) if today.month >= fiscal_start_month else today.year) % 100
    return di_quarter_bounds(fy2, quarter, fiscal_start_month)


def safe_date(s) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None
