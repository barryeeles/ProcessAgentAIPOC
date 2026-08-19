"""
Score rollup — count-weighted mean at every level with delivery-status override.

Weights: DQ 30% | Flow 40% | KPI 30%
Blocked penalty is subtracted from the Capability overall score before RAG assignment.
Reported RAG = worst(health_rag, delivery_status_rag).
Low-confidence flag: children_contributing < 50% of children_total.
"""
from __future__ import annotations

import sqlite3
from datetime import date

from config_loader import AppConfig
from scoring._utils import safe_date

_RAG_RANK = {"R": 0, "A": 1, "G": 2, "U": 3}


def run_rollup(
    conn: sqlite3.Connection,
    upload_week: str,
    config: AppConfig,
    dq: dict,
    flow: dict,
    kpi: dict,
    blocked: dict,
) -> dict:
    """Returns {caps: {...}, epics: {...}, releases: {...}}."""
    today = date.today()
    wt = config.weights
    t = config.thresholds

    dq_cap = dq["cap_scores"]
    flow_cap = flow["cap_scores"]
    kpi_cap = kpi["cap_scores"]
    blocked_feats = blocked["feature_results"]

    # ── Load entities ──────────────────────────────────────────────────────
    caps = {
        r["cap_key"]: dict(r)
        for r in conn.execute("SELECT * FROM capabilities WHERE in_scope = 1").fetchall()
    }
    features = [dict(r) for r in conn.execute(
        "SELECT * FROM features WHERE in_scope = 1"
    ).fetchall()]
    epics = {
        r["epic_key"]: dict(r)
        for r in conn.execute(
            "SELECT * FROM epics WHERE in_scope = 1 AND is_active = 1"
        ).fetchall()
    }

    cap_rel_rows = conn.execute(
        "SELECT cap_key, release_name FROM capability_releases"
    ).fetchall()
    cap_releases: dict[str, list[str]] = {}
    for r in cap_rel_rows:
        cap_releases.setdefault(r["cap_key"], []).append(r["release_name"])

    release_names: set[str] = {r["release_name"] for r in cap_rel_rows}

    # Group features by cap_key
    cap_feats: dict[str, list[dict]] = {}
    for f in features:
        cap_feats.setdefault(f["cap_key"], []).append(f)

    # Blocked penalty / count aggregated to Capability
    cap_blocked_penalty: dict[str, float] = {}
    cap_blocked_count: dict[str, int] = {}
    cap_escalated_count: dict[str, int] = {}
    for fk, br in blocked_feats.items():
        ck = br["cap_key"]
        cap_blocked_penalty[ck] = cap_blocked_penalty.get(ck, 0.0) + br["penalty_pct"]
        cap_blocked_count[ck] = cap_blocked_count.get(ck, 0) + 1
        if br["stage"] == "ESCALATE":
            cap_escalated_count[ck] = cap_escalated_count.get(ck, 0) + 1

    # ── Score each Capability ──────────────────────────────────────────────
    cap_scores: dict[str, dict] = {}
    for cap_key, cap in caps.items():
        feats = cap_feats.get(cap_key, [])
        children_total = len(feats)
        contributing = [
            f for f in feats if f["status"] not in ("Funnel", "Cancelled", "Blocked")
        ]
        children_contributing = len(contributing)
        low_confidence = (
            children_total > 0
            and children_contributing / children_total < t.low_confidence_threshold
        )

        dq_s = dq_cap.get(cap_key)
        fl_s = flow_cap.get(cap_key)
        kp_s = kpi_cap.get(cap_key)

        available = [
            (dq_s, wt.data_quality),
            (fl_s, wt.flow_throughput),
            (kp_s, wt.kpis),
        ]
        available = [(s, w) for s, w in available if s is not None]

        if available:
            total_w = sum(w for _, w in available)
            overall: float | None = sum(s * w for s, w in available) / total_w
            penalty = cap_blocked_penalty.get(cap_key, 0.0)
            overall = max(0.0, overall - penalty)
        else:
            overall = None

        health_rag = _rag(overall, t.rag_green_threshold, t.rag_amber_threshold)
        del_status = _delivery_status(cap, feats, today, t.delivery_at_risk_horizon_days)
        reported_rag = _worst(_delivery_to_rag(del_status), health_rag)

        cap_scores[cap_key] = {
            "entity_key": cap_key,
            "entity_type": "capability",
            "parent_key": cap["epic_key"],
            "dq_score": dq_s,
            "flow_score": fl_s,
            "kpi_score": kp_s,
            "overall_score": overall,
            "health_rag": health_rag,
            "delivery_status": del_status,
            "reported_rag": reported_rag,
            "children_total": children_total,
            "children_contributing": children_contributing,
            "low_confidence": 1 if low_confidence else 0,
            "blocked_count": cap_blocked_count.get(cap_key, 0),
            "high_risk_count": cap_escalated_count.get(cap_key, 0),
        }

    # ── Roll up to EPIC ────────────────────────────────────────────────────
    epic_cap_map: dict[str, list[dict]] = {}
    for ck, sc in cap_scores.items():
        ek = caps[ck]["epic_key"]
        epic_cap_map.setdefault(ek, []).append(sc)

    epic_scores: dict[str, dict] = {}
    for epic_key in epics:
        children = epic_cap_map.get(epic_key, [])
        epic_scores[epic_key] = _aggregate(
            epic_key, "epic", None, children, t.rag_green_threshold,
            t.rag_amber_threshold, t.low_confidence_threshold,
        )

    # ── Roll up to Release ────────────────────────────────────────────────
    release_scores: dict[str, dict] = {}
    for rname in release_names:
        children = [cap_scores[ck] for ck, rnames in cap_releases.items()
                    if rname in rnames and ck in cap_scores]
        release_scores[rname] = _aggregate(
            rname, "release", None, children, t.rag_green_threshold,
            t.rag_amber_threshold, t.low_confidence_threshold,
        )

    return {"caps": cap_scores, "epics": epic_scores, "releases": release_scores}


# ── helpers ────────────────────────────────────────────────────────────────

def _aggregate(
    entity_key: str,
    entity_type: str,
    parent_key: str | None,
    children: list[dict],
    green_t: float,
    amber_t: float,
    lc_t: float,
) -> dict:
    scored = [c for c in children if c.get("overall_score") is not None]
    ct = len(children)
    cc = len(scored)
    lc = ct > 0 and cc / ct < lc_t
    overall = sum(c["overall_score"] for c in scored) / cc if scored else None
    health_rag = _rag(overall, green_t, amber_t)
    worst_del = min(
        (_delivery_to_rag(c.get("delivery_status", "unassessed")) for c in children),
        key=lambda r: _RAG_RANK.get(r, 3),
        default="U",
    )
    reported_rag = _worst(worst_del, health_rag)
    return {
        "entity_key": entity_key,
        "entity_type": entity_type,
        "parent_key": parent_key,
        "dq_score": None,
        "flow_score": None,
        "kpi_score": None,
        "overall_score": overall,
        "health_rag": health_rag,
        "delivery_status": "unassessed",
        "reported_rag": reported_rag,
        "children_total": ct,
        "children_contributing": cc,
        "low_confidence": 1 if lc else 0,
        "blocked_count": sum(c.get("blocked_count", 0) for c in children),
        "high_risk_count": sum(c.get("high_risk_count", 0) for c in children),
    }


def _rag(score: float | None, green_t: float, amber_t: float) -> str:
    if score is None:
        return "U"
    frac = score / 100.0
    return "G" if frac >= green_t else ("A" if frac >= amber_t else "R")


def _delivery_status(cap: dict, feats: list[dict], today: date, at_risk_days: int) -> str:
    end = safe_date(cap.get("target_end_date"))
    if end is None:
        return "unassessed"
    non_done = [f for f in feats if f.get("status") not in ("Done", "Cancelled")]
    if end < today and non_done:
        return "late"
    if any(
        f.get("status") == "Blocked"
        or (end is not None and (end - today).days <= at_risk_days and f.get("status") not in ("Done", "Cancelled"))
        for f in feats
    ):
        return "at_risk"
    return "on_track"


def _delivery_to_rag(status: str) -> str:
    return {"on_track": "G", "at_risk": "A", "late": "R"}.get(status, "U")


def _worst(a: str, b: str) -> str:
    return min(a, b, key=lambda r: _RAG_RANK.get(r, 3))
