"""Drilldown API endpoints — delivery, release, epic, capability, and feature detail."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from database import get_connection

router = APIRouter()

_TODAY = date.today  # callable so tests can patch


# ── Shared helpers ─────────────────────────────────────────────────────────

def _latest_week(conn) -> str | None:
    row = conn.execute(
        "SELECT upload_week FROM upload_history ORDER BY upload_week DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def _upload_weeks(conn, n: int = 11) -> list[str]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT upload_week FROM upload_history ORDER BY upload_week DESC LIMIT ?", (n,)
        ).fetchall()
    ]


def _sparklines_for(conn, entity_keys: list[str], entity_type: str, n: int = 11) -> dict[str, list]:
    if not entity_keys:
        return {}
    weeks = _upload_weeks(conn, n)
    if not weeks:
        return {k: [None] * n for k in entity_keys}

    ph_k = ",".join("?" * len(entity_keys))
    ph_w = ",".join("?" * len(weeks))
    rows = conn.execute(
        f"SELECT entity_key, upload_week, reported_rag FROM weekly_snapshots "
        f"WHERE entity_key IN ({ph_k}) AND entity_type=? AND upload_week IN ({ph_w})",
        entity_keys + [entity_type] + weeks,
    ).fetchall()
    rag_map = {(r["entity_key"], r["upload_week"]): r["reported_rag"] for r in rows}

    result: dict[str, list] = {}
    for key in entity_keys:
        dots = [rag_map.get((key, w)) for w in reversed(weeks)]
        result[key] = [None] * (n - len(dots)) + dots
    return result


def _snap(conn, entity_key: str, entity_type: str, week: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM weekly_snapshots WHERE entity_key=? AND entity_type=? AND upload_week=?",
        (entity_key, entity_type, week),
    ).fetchone()
    return dict(row) if row else None


# ── KPI helpers ────────────────────────────────────────────────────────────

_KPI_SLA = {
    "full_cycle_time": 150,
    "delivery_predictability": 90,
    "delivery_cycle_time": 90,
}
_KPI_AMBER_PCT = 0.80


def _first_transition_date(conn, feature_key: str, to_status: str) -> date | None:
    row = conn.execute(
        "SELECT transition_date FROM feature_transitions "
        "WHERE feature_key=? AND to_status=? ORDER BY transition_date ASC LIMIT 1",
        (feature_key, to_status),
    ).fetchone()
    if not row:
        return None
    try:
        return date.fromisoformat(row[0])
    except (ValueError, TypeError):
        return None


def _safe_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def _kpi_entry(start: date | None, end: date | None, sla: int) -> dict | None:
    if start is None:
        return None
    today = _TODAY()
    end_d = end or today
    elapsed = (end_d - start).days
    pct = elapsed / sla
    if pct < _KPI_AMBER_PCT:
        rag = "G"
        score = 100
    elif pct <= 1.0:
        rag = "A"
        score = 70
    else:
        rag = "R"
        score = 20
    return {
        "start_date": start.isoformat(),
        "end_date": end_d.isoformat(),
        "elapsed_days": elapsed,
        "sla_days": sla,
        "rag": rag,
        "score": score,
        "is_complete": end is not None,
    }


def _feature_kpis(conn, feature: dict) -> dict:
    fk = feature["feature_key"]
    done = _safe_date(feature.get("date_done"))

    fct_start = _first_transition_date(conn, fk, "In Analysis")
    dp_start = _safe_date(feature.get("date_committed"))
    dct_start = _first_transition_date(conn, fk, "In Development")

    return {
        "full_cycle_time": _kpi_entry(fct_start, done, _KPI_SLA["full_cycle_time"]),
        "delivery_predictability": _kpi_entry(dp_start, done, _KPI_SLA["delivery_predictability"]),
        "delivery_cycle_time": _kpi_entry(dct_start, done, _KPI_SLA["delivery_cycle_time"]),
    }


# ── GET /api/delivery/{epic_key} ───────────────────────────────────────────

@router.get("/delivery/{epic_key}")
def get_delivery_view(epic_key: str, week: str | None = Query(None)) -> JSONResponse:
    """
    Delivery Manager view — one row per Release linked to the given EPIC.
    Also returns capabilities that are in scope for the EPIC but not linked to any release.
    """
    with get_connection() as conn:
        epic = conn.execute(
            "SELECT * FROM epics WHERE epic_key=?", (epic_key,)
        ).fetchone()
        if not epic:
            raise HTTPException(status_code=404, detail=f"EPIC {epic_key!r} not found")

        w = week or _latest_week(conn)
        if not w:
            return JSONResponse(content={
                "epic": dict(epic), "week": None,
                "releases": [], "unassigned_capabilities": [],
            })

        release_names = [
            r[0]
            for r in conn.execute(
                "SELECT release_name FROM epic_releases WHERE epic_key=? ORDER BY release_name",
                (epic_key,),
            ).fetchall()
        ]

        # ── Releases ───────────────────────────────────────────────────────
        if release_names:
            ph = ",".join("?" * len(release_names))
            rel_rows = conn.execute(
                f"SELECT * FROM releases WHERE release_name IN ({ph}) ORDER BY release_date",
                release_names,
            ).fetchall()

            rel_snaps = {
                r["entity_key"]: dict(r)
                for r in conn.execute(
                    f"SELECT * FROM weekly_snapshots "
                    f"WHERE entity_key IN ({ph}) AND entity_type='release' AND upload_week=?",
                    release_names + [w],
                ).fetchall()
            }
            rel_sparklines = _sparklines_for(conn, release_names, "release")
        else:
            rel_rows = []
            rel_snaps = {}
            rel_sparklines = {}

        # ── Capabilities not linked to any release ─────────────────────────
        unassigned_cap_rows = conn.execute(
            "SELECT cap_key, title, status, delivery_increment "
            "FROM capabilities "
            "WHERE epic_key = ? AND in_scope = 1 "
            "  AND cap_key NOT IN (SELECT cap_key FROM capability_releases)",
            (epic_key,),
        ).fetchall()

        unassigned_keys = [r["cap_key"] for r in unassigned_cap_rows]

        if unassigned_keys:
            ph_uc = ",".join("?" * len(unassigned_keys))
            uc_snaps = {
                r["entity_key"]: dict(r)
                for r in conn.execute(
                    f"SELECT * FROM weekly_snapshots "
                    f"WHERE entity_key IN ({ph_uc}) AND entity_type='capability' AND upload_week=?",
                    unassigned_keys + [w],
                ).fetchall()
            }
            uc_sparklines = _sparklines_for(conn, unassigned_keys, "capability")
            uc_defect_rows = conn.execute(
                f"SELECT entity_key, rule_set, severity, description "
                f"FROM dq_defects WHERE upload_week=? AND entity_key IN ({ph_uc})",
                [w] + unassigned_keys,
            ).fetchall()
            uc_defects: dict[str, list] = {}
            for r in uc_defect_rows:
                uc_defects.setdefault(r["entity_key"], []).append({
                    "rule_set": r["rule_set"],
                    "severity": r["severity"],
                    "description": r["description"],
                })
        else:
            uc_snaps = {}
            uc_sparklines = {}
            uc_defects = {}

    releases = []
    for r in rel_rows:
        d = dict(r)
        rn = d["release_name"]
        d["snapshot"] = rel_snaps.get(rn, {})
        d["sparkline"] = rel_sparklines.get(rn, [None] * 11)
        releases.append(d)

    # Include releases in epic_releases but not in releases table (orphaned links)
    found_names = {r["release_name"] for r in rel_rows}
    for rn in release_names:
        if rn not in found_names:
            releases.append({
                "release_name": rn, "status": None,
                "start_date": None, "release_date": None,
                "snapshot": rel_snaps.get(rn, {}),
                "sparkline": rel_sparklines.get(rn, [None] * 11),
            })

    unassigned_capabilities = [
        {
            "cap_key": r["cap_key"],
            "title": r["title"],
            "status": r["status"],
            "delivery_increment": r["delivery_increment"],
            "snapshot": uc_snaps.get(r["cap_key"], {}),
            "sparkline": uc_sparklines.get(r["cap_key"], [None] * 11),
            "dq_defects": uc_defects.get(r["cap_key"], []),
        }
        for r in unassigned_cap_rows
    ]

    return JSONResponse(content={
        "epic": dict(epic),
        "week": w,
        "releases": releases,
        "unassigned_capabilities": unassigned_capabilities,
    })


# ── GET /api/release/{release_name:path} ─────────────────────────────────

@router.get("/release/{release_name:path}")
def get_release_view(release_name: str, week: str | None = Query(None)) -> JSONResponse:
    """
    Release Manager view — one row per Capability linked to the given Release.
    """
    with get_connection() as conn:
        release = conn.execute(
            "SELECT * FROM releases WHERE release_name=?", (release_name,)
        ).fetchone()

        w = week or _latest_week(conn)
        if not w:
            return JSONResponse(content={
                "release": dict(release) if release else {"release_name": release_name},
                "week": None,
                "capabilities": [],
            })

        cap_keys = [
            r[0]
            for r in conn.execute(
                "SELECT cap_key FROM capability_releases WHERE release_name=? ORDER BY cap_key",
                (release_name,),
            ).fetchall()
        ]

        if not cap_keys:
            return JSONResponse(content={
                "release": dict(release) if release else {"release_name": release_name},
                "week": w,
                "capabilities": [],
            })

        ph = ",".join("?" * len(cap_keys))
        cap_rows = conn.execute(
            f"SELECT * FROM capabilities WHERE cap_key IN ({ph}) AND in_scope=1 ORDER BY cap_key",
            cap_keys,
        ).fetchall()

        cap_keys_in_scope = [r["cap_key"] for r in cap_rows]
        snaps = {}
        if cap_keys_in_scope:
            ph2 = ",".join("?" * len(cap_keys_in_scope))
            snaps = {
                r["entity_key"]: dict(r)
                for r in conn.execute(
                    f"SELECT * FROM weekly_snapshots "
                    f"WHERE entity_key IN ({ph2}) AND entity_type='capability' AND upload_week=?",
                    cap_keys_in_scope + [w],
                ).fetchall()
            }

        sparklines = _sparklines_for(conn, cap_keys_in_scope, "capability")

    capabilities = []
    for c in cap_rows:
        d = dict(c)
        ck = d["cap_key"]
        d["snapshot"] = snaps.get(ck, {})
        d["sparkline"] = sparklines.get(ck, [None] * 11)
        capabilities.append(d)

    return JSONResponse(content={
        "release": dict(release) if release else {"release_name": release_name},
        "week": w,
        "capabilities": capabilities,
    })


# ── GET /api/epic/{key} ────────────────────────────────────────────────────

@router.get("/epic/{key}")
def get_epic_detail(key: str, week: str | None = Query(None)) -> JSONResponse:
    """Full EPIC detail: scores, transitions, blocked features."""
    with get_connection() as conn:
        epic = conn.execute("SELECT * FROM epics WHERE epic_key=?", (key,)).fetchone()
        if not epic:
            raise HTTPException(status_code=404, detail=f"EPIC {key!r} not found")

        w = week or _latest_week(conn)
        snap = _snap(conn, key, "epic", w) if w else None
        sparklines = _sparklines_for(conn, [key], "epic")

        transitions = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM epic_transitions WHERE epic_key=? ORDER BY transition_date",
                (key,),
            ).fetchall()
        ]

        # Releases this EPIC belongs to
        releases = [
            r[0]
            for r in conn.execute(
                "SELECT release_name FROM epic_releases WHERE epic_key=? ORDER BY release_name",
                (key,),
            ).fetchall()
        ]

        # Blocked features under this EPIC (via cap)
        cap_keys = [
            r[0]
            for r in conn.execute(
                "SELECT cap_key FROM capabilities WHERE epic_key=? AND in_scope=1", (key,)
            ).fetchall()
        ]
        blocked: list[dict] = []
        if cap_keys and w:
            ph = ",".join("?" * len(cap_keys))
            blocked_feats = conn.execute(
                f"SELECT bi.*, f.title, f.cap_key FROM blocked_items bi "
                f"JOIN features f ON f.feature_key = bi.feature_key "
                f"WHERE bi.upload_week=? AND f.cap_key IN ({ph}) "
                f"ORDER BY bi.stage, bi.weeks_consecutive DESC",
                [w] + cap_keys,
            ).fetchall()
            blocked = [dict(r) for r in blocked_feats]

        # DQ defect count for this EPIC's capabilities
        dq_count = 0
        if cap_keys and w:
            ph = ",".join("?" * len(cap_keys))
            dq_count = conn.execute(
                f"SELECT COUNT(*) FROM dq_defects "
                f"WHERE upload_week=? AND entity_key IN ({ph})",
                [w] + cap_keys,
            ).fetchone()[0]

    return JSONResponse(content={
        "epic": dict(epic),
        "week": w,
        "snapshot": snap,
        "sparkline": sparklines.get(key, [None] * 11),
        "transitions": transitions,
        "releases": releases,
        "blocked_features": blocked,
        "dq_defect_count": dq_count,
    })


# ── GET /api/capability/{key} ──────────────────────────────────────────────

@router.get("/capability/{key}")
def get_capability_detail(key: str, week: str | None = Query(None)) -> JSONResponse:
    """
    Full Capability detail: features list, snapshot scores, DQ defects, blocked items.
    """
    with get_connection() as conn:
        cap = conn.execute("SELECT * FROM capabilities WHERE cap_key=?", (key,)).fetchone()
        if not cap:
            raise HTTPException(status_code=404, detail=f"Capability {key!r} not found")

        w = week or _latest_week(conn)
        snap = _snap(conn, key, "capability", w) if w else None
        sparklines = _sparklines_for(conn, [key], "capability")

        features = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM features WHERE cap_key=? AND in_scope=1 ORDER BY feature_key",
                (key,),
            ).fetchall()
        ]
        feat_keys = [f["feature_key"] for f in features]

        # Blocked items for features of this capability
        blocked: list[dict] = []
        if feat_keys and w:
            ph = ",".join("?" * len(feat_keys))
            blocked_rows = conn.execute(
                f"SELECT bi.*, f.title FROM blocked_items bi "
                f"JOIN features f ON f.feature_key = bi.feature_key "
                f"WHERE bi.upload_week=? AND bi.feature_key IN ({ph}) "
                f"ORDER BY bi.stage, bi.weeks_consecutive DESC",
                [w] + feat_keys,
            ).fetchall()
            blocked = [dict(r) for r in blocked_rows]

        # DQ defects for this capability
        dq_defects: list[dict] = []
        if w:
            dq_rows = conn.execute(
                "SELECT * FROM dq_defects WHERE upload_week=? AND entity_key=? "
                "ORDER BY severity, rule_set",
                (w, key),
            ).fetchall()
            dq_defects = [dict(r) for r in dq_rows]

        # Releases this capability belongs to
        releases = [
            r[0]
            for r in conn.execute(
                "SELECT release_name FROM capability_releases WHERE cap_key=? ORDER BY release_name",
                (key,),
            ).fetchall()
        ]

    return JSONResponse(content={
        "capability": dict(cap),
        "week": w,
        "snapshot": snap,
        "sparkline": sparklines.get(key, [None] * 11),
        "features": features,
        "blocked_features": blocked,
        "dq_defects": dq_defects,
        "releases": releases,
    })


# ── GET /api/feature/{key} ─────────────────────────────────────────────────

@router.get("/feature/{key}")
def get_feature_detail(key: str, week: str | None = Query(None)) -> JSONResponse:
    """
    Feature detail: current state, full transition history, KPI clocks, blocked status.
    """
    with get_connection() as conn:
        feat = conn.execute("SELECT * FROM features WHERE feature_key=?", (key,)).fetchone()
        if not feat:
            raise HTTPException(status_code=404, detail=f"Feature {key!r} not found")

        w = week or _latest_week(conn)

        transitions = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM feature_transitions WHERE feature_key=? ORDER BY transition_date",
                (key,),
            ).fetchall()
        ]

        blocked_row = None
        if w:
            bi = conn.execute(
                "SELECT * FROM blocked_items WHERE feature_key=? AND upload_week=?",
                (key, w),
            ).fetchone()
            blocked_row = dict(bi) if bi else None

        dq_defects: list[dict] = []
        if w:
            dq_rows = conn.execute(
                "SELECT * FROM dq_defects "
                "WHERE upload_week=? AND entity_key=? ORDER BY severity, rule_set",
                (w, key),
            ).fetchall()
            dq_defects = [dict(r) for r in dq_rows]

        kpis = _feature_kpis(conn, dict(feat))

    return JSONResponse(content={
        "feature": dict(feat),
        "week": w,
        "transitions": transitions,
        "kpis": kpis,
        "blocked": blocked_row,
        "dq_defects": dq_defects,
    })
