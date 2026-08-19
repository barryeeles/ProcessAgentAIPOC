"""DQ Cleanup Checklist endpoints."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse

from database import get_connection

router = APIRouter()

_SECTIONS = [
    ("RS1", "Release Assignment"),
    ("RS2", "Capability–Feature Consistency"),
    ("RS3", "Date & DI Completeness"),
    ("RS4", "Date Boundary Violations"),
    ("RS5", "Release Link Integrity"),
]

_SEV_ORDER = {"HIGH": 0, "MEDIUM": 1, "WARNING": 2}


def _latest_week(conn) -> str | None:
    row = conn.execute(
        "SELECT upload_week FROM upload_history ORDER BY upload_week DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def _fetch_defects(conn, w: str, epic_key: str | None) -> list[dict]:
    if epic_key:
        rows = conn.execute(
            """
            SELECT d.* FROM dq_defects d
            WHERE d.upload_week = ?
              AND (
                d.entity_key IN (SELECT cap_key  FROM capabilities WHERE epic_key = ?)
                OR
                d.entity_key IN (
                    SELECT f.feature_key FROM features f
                    JOIN capabilities c ON c.cap_key = f.cap_key
                    WHERE c.epic_key = ?
                )
                OR
                d.entity_key IN (
                    SELECT release_name FROM epic_releases WHERE epic_key = ?
                )
              )
            ORDER BY d.severity, d.rule_set
            """,
            (w, epic_key, epic_key, epic_key),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM dq_defects WHERE upload_week = ? ORDER BY severity, rule_set",
            (w,),
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/checklist")
def get_checklist(
    week: str | None = Query(None),
    epic_key: str | None = Query(None),
) -> JSONResponse:
    """DQ defects grouped into RS1–RS5 sections."""
    with get_connection() as conn:
        w = week or _latest_week(conn)
        if not w:
            return JSONResponse(content={"week": None, "sections": [], "total": 0})
        defects = _fetch_defects(conn, w, epic_key)

    # Group by rule_set prefix
    buckets: dict[str, list[dict]] = {k: [] for k, _ in _SECTIONS}
    for d in defects:
        prefix = d["rule_set"][:3]
        if prefix in buckets:
            buckets[prefix].append(d)

    sections = []
    for code, title in _SECTIONS:
        items = sorted(buckets[code], key=lambda x: (_SEV_ORDER.get(x["severity"], 9), x["rule_set"]))
        sections.append({"section": code, "title": title, "defects": items, "count": len(items)})

    return JSONResponse(content={"week": w, "sections": sections, "total": len(defects)})


@router.get("/checklist/export")
def export_checklist(
    week: str | None = Query(None),
    epic_key: str | None = Query(None),
) -> StreamingResponse:
    """Download DQ defects as CSV."""
    with get_connection() as conn:
        w = week or _latest_week(conn)
        defects = _fetch_defects(conn, w, epic_key) if w else []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "section", "rule_set", "severity", "entity_type", "entity_key",
        "description", "required_action", "first_seen_week", "scoring_attribution",
    ])
    for d in defects:
        prefix = d["rule_set"][:3]
        section_title = next((t for c, t in _SECTIONS if c == prefix), prefix)
        writer.writerow([
            section_title,
            d.get("rule_set", ""),
            d.get("severity", ""),
            d.get("entity_type", ""),
            d.get("entity_key", ""),
            d.get("description", ""),
            d.get("required_action") or "",
            d.get("first_seen_week") or "",
            d.get("scoring_attribution", ""),
        ])

    output.seek(0)
    filename = f"dq_checklist_{w or 'unknown'}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
