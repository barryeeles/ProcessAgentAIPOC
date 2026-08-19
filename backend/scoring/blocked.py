"""
Blocked Feature penalty ladder.

For each currently-Blocked in-scope Feature:
  - Count consecutive upload weeks it has been Blocked (from blocked_items history)
  - Determine DI band: pre_di / early (month 1) / mid (month 2) / late (month 3)
  - Assign stage: 1wk=FLAGGED, 2wk=WARNING, 3wk=PRIORITY, >=4wk=ESCALATE
  - Penalty: 0% if pre_di; otherwise FLAGGED=2%, WARNING=5%, PRIORITY=10%, ESCALATE=15%

Re-blocking resets the consecutive counter to 1 (gap in blocked_items = new block event).
Writes results to blocked_items table.
"""
from __future__ import annotations

import sqlite3
from datetime import date

from config_loader import AppConfig
from scoring._utils import di_quarter_bounds, parse_di, safe_date


def run_blocked(
    conn: sqlite3.Connection,
    upload_week: str,
    config: AppConfig,
) -> dict:
    """Returns {feature_results: {feat_key: {...}}, total: int, escalated: int}."""
    today = date.today()
    fiscal_sm = config.fiscal_calendar["start_month"]
    penalties = config.blocked_penalties

    blocked_feats = conn.execute(
        "SELECT feature_key, cap_key, delivery_increment FROM features "
        "WHERE in_scope = 1 AND status = 'Blocked'"
    ).fetchall()

    if not blocked_feats:
        return {"feature_results": {}, "total": 0, "escalated": 0}

    feat_keys = [r["feature_key"] for r in blocked_feats]
    ph = ",".join("?" * len(feat_keys))

    # Previous blocked_items entries (ordered to walk back consecutively)
    prev_blocked: dict[str, list[str]] = {}
    for r in conn.execute(
        f"SELECT feature_key, upload_week FROM blocked_items "
        f"WHERE feature_key IN ({ph}) ORDER BY upload_week DESC",
        feat_keys,
    ).fetchall():
        prev_blocked.setdefault(r["feature_key"], []).append(r["upload_week"])

    # All upload weeks in ascending order (to check consecutive adjacency)
    all_uploads = [
        r[0]
        for r in conn.execute(
            "SELECT upload_week FROM upload_history ORDER BY upload_week ASC"
        ).fetchall()
    ]

    # Earliest "→ Blocked" transition date per feature (to determine DI band)
    first_block_dates: dict[str, str] = {
        r["feature_key"]: r["first_date"]
        for r in conn.execute(
            f"SELECT feature_key, MIN(transition_date) AS first_date "
            f"FROM feature_transitions "
            f"WHERE feature_key IN ({ph}) AND to_status = 'Blocked' AND transition_date IS NOT NULL "
            f"GROUP BY feature_key",
            feat_keys,
        ).fetchall()
        if r["first_date"]
    }

    feature_results: dict[str, dict] = {}
    rows: list[dict] = []
    escalated = 0

    for row in blocked_feats:
        fk = row["feature_key"]
        ck = row["cap_key"]
        di_str = row["delivery_increment"]

        consecutive = _consecutive(fk, upload_week, prev_blocked.get(fk, []), all_uploads)

        if consecutive >= 4:
            stage = "ESCALATE"
        elif consecutive == 3:
            stage = "PRIORITY"
        elif consecutive == 2:
            stage = "WARNING"
        else:
            stage = "FLAGGED"

        block_date = safe_date(first_block_dates.get(fk)) or today
        di_band = _di_band(di_str, block_date, fiscal_sm)
        penalty = 0.0 if di_band == "pre_di" else penalties.get(stage, 0.0)

        if stage == "ESCALATE":
            escalated += 1

        feature_results[fk] = {
            "feature_key": fk,
            "cap_key": ck,
            "stage": stage,
            "di_band": di_band,
            "penalty_pct": penalty,
            "weeks_consecutive": consecutive,
        }
        rows.append({
            "feature_key": fk,
            "upload_week": upload_week,
            "weeks_consecutive": consecutive,
            "stage": stage,
            "di_band": di_band,
            "penalty_pct": penalty,
        })

    if rows:
        conn.executemany(
            """INSERT OR REPLACE INTO blocked_items
               (feature_key, upload_week, weeks_consecutive, stage, di_band, penalty_pct)
               VALUES (:feature_key, :upload_week, :weeks_consecutive, :stage, :di_band, :penalty_pct)""",
            rows,
        )

    return {"feature_results": feature_results, "total": len(feature_results), "escalated": escalated}


def _consecutive(
    feat_key: str,
    current_week: str,
    prev_weeks: list[str],
    all_uploads: list[str],
) -> int:
    """Count consecutive uploads (including current) where this feature was blocked."""
    if not prev_weeks:
        return 1
    prev_set = set(prev_weeks)
    try:
        cur_idx = all_uploads.index(current_week)
    except ValueError:
        return 1
    count = 1
    for i in range(cur_idx - 1, -1, -1):
        if all_uploads[i] in prev_set:
            count += 1
        else:
            break
    return count


def _di_band(di_str: str | None, block_date: date, fiscal_sm: int) -> str:
    """Return 'pre_di' | 'early' | 'mid' | 'late'. Defaults to 'mid' if unparseable."""
    parsed = parse_di(di_str)
    if not parsed:
        return "mid"
    fy2, q = parsed
    try:
        di_start, _ = di_quarter_bounds(fy2, q, fiscal_sm)
    except Exception:
        return "mid"
    if block_date < di_start:
        return "pre_di"
    months_in = (block_date.year - di_start.year) * 12 + (block_date.month - di_start.month)
    return "early" if months_in == 0 else ("mid" if months_in == 1 else "late")
