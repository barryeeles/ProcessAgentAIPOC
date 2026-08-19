"""Dashboard API endpoints — read-only queries against baseline + snapshots."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from database import get_connection

router = APIRouter()


# ── Shared helpers ─────────────────────────────────────────────────────────

def _latest_week(conn) -> str | None:
    row = conn.execute(
        "SELECT upload_week FROM upload_history ORDER BY upload_week DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def _upload_weeks(conn, n: int = 11) -> list[str]:
    """Return the last n upload weeks, newest first."""
    return [
        r[0]
        for r in conn.execute(
            "SELECT upload_week FROM upload_history ORDER BY upload_week DESC LIMIT ?", (n,)
        ).fetchall()
    ]


def _sparklines_bulk(
    conn,
    entity_keys: list[str],
    entity_type: str,
    n: int = 11,
) -> dict[str, list]:
    """
    Return {entity_key: [rag|None, ...]} with n entries, oldest→newest.
    Weeks with no snapshot get None (rendered as grey dot in UI).
    """
    if not entity_keys:
        return {}
    weeks = _upload_weeks(conn, n)
    if not weeks:
        return {k: [None] * n for k in entity_keys}

    ph_k = ",".join("?" * len(entity_keys))
    ph_w = ",".join("?" * len(weeks))
    rows = conn.execute(
        f"SELECT entity_key, upload_week, reported_rag FROM weekly_snapshots "
        f"WHERE entity_key IN ({ph_k}) AND entity_type = ? AND upload_week IN ({ph_w})",
        entity_keys + [entity_type] + weeks,
    ).fetchall()

    rag_map = {(r["entity_key"], r["upload_week"]): r["reported_rag"] for r in rows}

    result: dict[str, list] = {}
    for key in entity_keys:
        # Build chronological list (oldest first); pad leading Nones for missing weeks
        dots = [rag_map.get((key, w)) for w in reversed(weeks)]
        result[key] = [None] * (n - len(dots)) + dots
    return result


# ── SLT view ───────────────────────────────────────────────────────────────

_SLT_SQL = """
    WITH cap_avg AS (
        SELECT c.epic_key,
               COUNT(*)                                          AS cap_total,
               AVG(s.dq_score)                                  AS avg_dq,
               AVG(s.flow_score)                                AS avg_flow,
               AVG(s.kpi_score)                                 AS avg_kpi,
               COUNT(s.flow_score)                              AS flow_cap_count,
               COUNT(s.kpi_score)                               AS kpi_cap_count
        FROM weekly_snapshots s
        JOIN capabilities c ON c.cap_key = s.entity_key AND c.in_scope = 1
        WHERE s.entity_type = 'capability' AND s.upload_week = :w
        GROUP BY c.epic_key
    )
    SELECT
        e.epic_key, e.title, e.status,
        s.overall_score, s.health_rag, s.reported_rag, s.delivery_status,
        s.children_total, s.children_contributing, s.low_confidence,
        s.blocked_count, s.high_risk_count,
        ca.avg_dq, ca.avg_flow, ca.avg_kpi,
        ca.cap_total, ca.flow_cap_count, ca.kpi_cap_count
    FROM epics e
    LEFT JOIN weekly_snapshots s
        ON s.entity_key = e.epic_key AND s.upload_week = :w AND s.entity_type = 'epic'
    LEFT JOIN cap_avg ca ON ca.epic_key = e.epic_key
    WHERE e.in_scope = 1 AND {filter}
    ORDER BY e.epic_key
"""


@router.get("/slt")
def get_slt_view(week: str | None = Query(None)) -> JSONResponse:
    """
    SLT view — one row per active in-scope EPIC with scores and sparklines.
    'recently_closed' contains EPICs that transitioned to Done/Cancelled/On Hold
    after the first upload (closed_at_initial_load = 0).
    """
    with get_connection() as conn:
        w = week or _latest_week(conn)
        if not w:
            return JSONResponse(content={"week": None, "epics": [], "recently_closed": []})

        active = conn.execute(
            _SLT_SQL.format(filter="e.is_active = 1"), {"w": w}
        ).fetchall()

        closed = conn.execute(
            _SLT_SQL.format(filter="e.is_active = 0 AND e.closed_at_initial_load = 0"),
            {"w": w},
        ).fetchall()

        all_keys = [r["epic_key"] for r in active] + [r["epic_key"] for r in closed]
        sparklines = _sparklines_bulk(conn, all_keys, "epic")

    def _fmt(rows: list) -> list[dict]:
        out = []
        for r in rows:
            d = dict(r)
            d["sparkline"] = sparklines.get(d["epic_key"], [None] * 11)
            out.append(d)
        return out

    return JSONResponse(content={
        "week": w,
        "epics": _fmt(active),
        "recently_closed": _fmt(closed),
    })


# ── Scope summary (Transparency Panel) ────────────────────────────────────

@router.get("/scope-summary")
def get_scope_summary() -> JSONResponse:
    """Scope counts for the Transparency Panel."""
    with get_connection() as conn:
        epics_total   = conn.execute("SELECT COUNT(*) FROM epics").fetchone()[0]
        epics_in      = conn.execute("SELECT COUNT(*) FROM epics WHERE in_scope=1").fetchone()[0]
        epics_active  = conn.execute("SELECT COUNT(*) FROM epics WHERE in_scope=1 AND is_active=1").fetchone()[0]
        epics_hist    = conn.execute("SELECT COUNT(*) FROM epics WHERE in_scope=1 AND closed_at_initial_load=1").fetchone()[0]
        epics_closed  = conn.execute("SELECT COUNT(*) FROM epics WHERE in_scope=1 AND is_active=0 AND closed_at_initial_load=0").fetchone()[0]
        caps_total    = conn.execute("SELECT COUNT(*) FROM capabilities").fetchone()[0]
        caps_in       = conn.execute("SELECT COUNT(*) FROM capabilities WHERE in_scope=1").fetchone()[0]
        feats_total   = conn.execute("SELECT COUNT(*) FROM features").fetchone()[0]
        feats_in      = conn.execute("SELECT COUNT(*) FROM features WHERE in_scope=1").fetchone()[0]
        transitions   = conn.execute("SELECT COUNT(*) FROM feature_transitions").fetchone()[0]
        defects       = conn.execute("SELECT COUNT(*) FROM dq_defects").fetchone()[0]
        snapshots     = conn.execute("SELECT COUNT(*) FROM weekly_snapshots").fetchone()[0]

    return JSONResponse(content={
        "epics": {
            "total": epics_total,
            "in_scope": epics_in,
            "active": epics_active,
            "historical_excluded": epics_hist,
            "recently_closed": epics_closed,
            "excluded": epics_total - epics_in,
        },
        "capabilities": {"total": caps_total, "in_scope": caps_in, "excluded": caps_total - caps_in},
        "features": {"total": feats_total, "in_scope": feats_in, "excluded": feats_total - feats_in},
        "feature_transitions_total": transitions,
        "dq_defects_total": defects,
        "snapshots_total": snapshots,
    })


# ── Blocked items (SLT-level callout) ─────────────────────────────────────

_STAGE_RANK = {"ESCALATE": 4, "PRIORITY": 3, "WARNING": 2, "FLAGGED": 1}

@router.get("/blocked")
def get_blocked(week: str | None = Query(None)) -> JSONResponse:
    """All blocked items for the week with EPIC/cap/feature context, ordered by severity."""
    with get_connection() as conn:
        w = week or _latest_week(conn)
        if not w:
            return JSONResponse(content={"week": None, "items": []})

        rows = conn.execute(
            """
            SELECT
                bi.feature_key, bi.weeks_consecutive, bi.stage, bi.di_band, bi.penalty_pct,
                f.title      AS feature_title,
                c.cap_key, c.title AS cap_title,
                e.epic_key,  e.title AS epic_title
            FROM blocked_items bi
            JOIN features     f ON f.feature_key = bi.feature_key
            JOIN capabilities c ON c.cap_key      = f.cap_key
            JOIN epics        e ON e.epic_key      = c.epic_key
            WHERE bi.upload_week = ?
            ORDER BY
                CASE bi.stage
                    WHEN 'ESCALATE' THEN 4 WHEN 'PRIORITY' THEN 3
                    WHEN 'WARNING'  THEN 2 ELSE 1
                END DESC,
                bi.weeks_consecutive DESC
            """,
            (w,),
        ).fetchall()

    return JSONResponse(content={
        "week": w,
        "items": [dict(r) for r in rows],
    })


# ── Metadata ───────────────────────────────────────────────────────────────

@router.get("/metadata")
def get_metadata() -> JSONResponse:
    """Available upload weeks and latest upload info."""
    with get_connection() as conn:
        weeks = [
            r[0]
            for r in conn.execute(
                "SELECT upload_week FROM upload_history ORDER BY upload_week DESC"
            ).fetchall()
        ]
        latest = conn.execute(
            "SELECT * FROM upload_history ORDER BY upload_week DESC LIMIT 1"
        ).fetchone()

    return JSONResponse(content={
        "available_weeks": weeks,
        "latest": dict(latest) if latest else None,
    })
