"""
KPI scoring — Full Cycle Time, Delivery Predictability, Delivery Cycle Time.

Scope: open Features (not Cancelled) + Features completed within the current DI quarter.
All clocks are always-running; backward transitions do not reset KPI clocks.

  Full Cycle Time      first → In Analysis         → date_done / today   SLA 150d
  Delivery Predictability  date_committed column   → date_done / today   SLA 90d
  Delivery Cycle Time  first → In Development      → date_done / today   SLA 90d

Capability KPI score = mean score across in-scope Features,
                       where score per Feature = mean of available KPI scores.
"""
from __future__ import annotations

import sqlite3
from datetime import date

from config_loader import AppConfig
from scoring._utils import current_quarter_bounds, safe_date


def run_kpis(
    conn: sqlite3.Connection,
    upload_week: str,
    config: AppConfig,
) -> dict:
    """Returns {cap_scores: {cap_key: float|None}, feature_kpis: {feat_key: {...}}}."""
    today = date.today()
    fiscal_sm = config.fiscal_calendar["start_month"]
    q_start, q_end = current_quarter_bounds(fiscal_sm, today)
    t = config.thresholds
    ks = config.kpi_scores

    features = [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM features WHERE in_scope = 1 AND status != 'Cancelled'"
        ).fetchall()
    ]

    # KPI scope: open OR completed in current DI quarter
    kpi_feats = [
        f for f in features
        if (d := safe_date(f.get("date_done"))) is None or q_start <= d <= q_end
    ]

    if not kpi_feats:
        all_cap_keys = {dict(r)["cap_key"] for r in conn.execute(
            "SELECT cap_key FROM capabilities WHERE in_scope = 1"
        ).fetchall()}
        return {"cap_scores": {ck: None for ck in all_cap_keys}, "feature_kpis": {}}

    feat_keys = [f["feature_key"] for f in kpi_feats]
    placeholders = ",".join("?" * len(feat_keys))

    # First transition dates into In Analysis and In Development
    first_trans: dict[tuple[str, str], str] = {
        (r["feature_key"], r["to_status"]): r["first_date"]
        for r in conn.execute(
            f"""SELECT feature_key, to_status, MIN(transition_date) AS first_date
                FROM feature_transitions
                WHERE feature_key IN ({placeholders})
                  AND to_status IN ('In Analysis', 'In Development')
                  AND transition_date IS NOT NULL
                GROUP BY feature_key, to_status""",
            feat_keys,
        ).fetchall()
    }

    feature_kpis: dict[str, dict] = {}
    cap_kpi_scores: dict[str, list[float]] = {}

    for f in kpi_feats:
        fk = f["feature_key"]
        ck = f["cap_key"]
        done_date = safe_date(f.get("date_done"))
        end = done_date or today

        fct_start = safe_date(first_trans.get((fk, "In Analysis")))
        dp_start = safe_date(f.get("date_committed"))
        dct_start = safe_date(first_trans.get((fk, "In Development")))

        fct = _kpi(fct_start, end, t.kpi_full_cycle_time_sla, t.kpi_amber_zone_pct, ks)
        dp = _kpi(dp_start, end, t.kpi_delivery_predictability_sla, t.kpi_amber_zone_pct, ks)
        dct = _kpi(dct_start, end, t.kpi_delivery_cycle_time_sla, t.kpi_amber_zone_pct, ks)

        feature_kpis[fk] = {"fct": fct, "dp": dp, "dct": dct}

        scores = [r["score"] for r in [fct, dp, dct] if r is not None]
        if scores:
            cap_kpi_scores.setdefault(ck, []).append(sum(scores) / len(scores))

    all_cap_keys = {dict(r)["cap_key"] for r in conn.execute(
        "SELECT cap_key FROM capabilities WHERE in_scope = 1"
    ).fetchall()}
    cap_scores: dict[str, float | None] = {
        ck: (sum(cap_kpi_scores[ck]) / len(cap_kpi_scores[ck]) if ck in cap_kpi_scores else None)
        for ck in all_cap_keys
    }

    return {"cap_scores": cap_scores, "feature_kpis": feature_kpis}


def _kpi(start: date | None, end: date, sla: int, amber_pct: float, scores_map: dict) -> dict | None:
    if start is None:
        return None
    elapsed = max(0, (end - start).days)
    if elapsed < sla * amber_pct:
        rag, score = "G", scores_map["green"]
    elif elapsed <= sla:
        rag, score = "A", scores_map["amber"]
    else:
        rag, score = "R", scores_map["red"]
    return {"elapsed_days": elapsed, "sla": sla, "rag": rag, "score": score}
