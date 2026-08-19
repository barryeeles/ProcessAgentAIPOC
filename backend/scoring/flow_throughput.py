"""
Flow throughput scoring — stagnation clocks and phase classification.

Stagnation clock: always running, never paused. Days since the most recent
forward transition (higher ordinal). Fallback to created_date.

Phase:
  Scoping  — In Analysis, PI Backlog, PI Planning     (10/20-day ladder)
  Delivery — Committed and beyond                      (10/20/30-day ladder)
  Excluded — Funnel (pre-analysis), Done, Cancelled, Blocked

Capability flow score = count-weighted mean of scored in-flight Features.
"""
from __future__ import annotations

import sqlite3
from datetime import date

from config_loader import AppConfig
from scoring._utils import safe_date


_EXCLUDED = frozenset({"Funnel", "Done", "Cancelled", "Blocked"})

# Statuses that mean "this entity is complete and closed"
_TERMINAL = frozenset({"Done", "Cancelled"})


def run_flow_throughput(
    conn: sqlite3.Connection,
    upload_week: str,
    config: AppConfig,
) -> dict:
    """Returns {cap_scores: {cap_key: float|None}, feature_scores: {feat_key: int|None}}."""
    today = date.today()
    ordinal_map = config.feature_ordinal_map
    scoping_set = set(config.status_normalisation["feature"].get("scoping_set", []))
    t = config.thresholds
    fs = config.flow_scores

    features = [dict(r) for r in conn.execute(
        "SELECT * FROM features WHERE in_scope = 1"
    ).fetchall()]

    # Load all forward-transition candidates for in-scope features in one query
    raw_trans = conn.execute(
        """SELECT ft.feature_key, ft.from_status, ft.to_status, ft.transition_date
           FROM feature_transitions ft
           JOIN features f ON f.feature_key = ft.feature_key
           WHERE f.in_scope = 1 AND ft.transition_date IS NOT NULL"""
    ).fetchall()

    feat_trans: dict[str, list[dict]] = {}
    for row in raw_trans:
        feat_trans.setdefault(row["feature_key"], []).append(dict(row))

    # ── Score each feature ────────────────────────────────────────────────
    feature_scores: dict[str, int | None] = {}
    for f in features:
        fk = f["feature_key"]
        status = f["status"]

        if status in _EXCLUDED:
            feature_scores[fk] = None
            continue

        stag = _stagnation_days(f, feat_trans.get(fk, []), ordinal_map, today)
        is_scoping = status in scoping_set

        if is_scoping:
            if stag >= t.scoping_budget_days:
                score = fs["phase_budget_breach"]
            elif stag >= t.stagnation_scoping_priority:
                score = fs["priority_risk"]
            elif stag >= t.stagnation_scoping_warning:
                score = fs["warning1"]
            else:
                score = fs["healthy"]
        else:
            if stag >= t.stagnation_delivery_alert:
                score = fs["high_alert"]
            elif stag >= t.stagnation_delivery_warning2:
                score = fs["warning2"]
            elif stag >= t.stagnation_delivery_warning1:
                score = fs["warning1"]
            else:
                score = fs["healthy"]

        feature_scores[fk] = score

    # ── Roll up to Capability: mean of non-None scores ────────────────────
    cap_feat_scores: dict[str, list[int]] = {}
    for f in features:
        sc = feature_scores.get(f["feature_key"])
        if sc is not None:
            cap_feat_scores.setdefault(f["cap_key"], []).append(sc)

    cap_rows = conn.execute(
        "SELECT cap_key, status FROM capabilities WHERE in_scope = 1"
    ).fetchall()
    all_cap_keys = {dict(r)["cap_key"] for r in cap_rows}
    cap_statuses = {dict(r)["cap_key"]: dict(r)["status"] for r in cap_rows}

    cap_scores: dict[str, float | None] = {
        ck: (sum(cap_feat_scores[ck]) / len(cap_feat_scores[ck]) if ck in cap_feat_scores else None)
        for ck in all_cap_keys
    }

    # ── Flow violation: all features Done/Cancelled but capability is not ──────
    # A capability stuck in a non-terminal status despite all work being complete
    # is a process failure — assign the lowest flow score so it scores rather
    # than being silently excluded from the flow dimension.
    cap_feature_index: dict[str, list[dict]] = {}
    for f in features:
        cap_feature_index.setdefault(f["cap_key"], []).append(f)

    for ck in all_cap_keys:
        if cap_scores[ck] is not None:
            continue  # already scored from active features
        feats = cap_feature_index.get(ck, [])
        if not feats:
            continue  # no features at all; nothing to assess
        if not all(f["status"] in _TERMINAL for f in feats):
            continue  # some features are still in-flight; no violation
        if cap_statuses.get(ck, "") in _TERMINAL:
            continue  # capability is Done or Cancelled; consistent
        # All features are terminal but capability has not been closed — violation
        cap_scores[ck] = float(fs["high_alert"])

    return {"cap_scores": cap_scores, "feature_scores": feature_scores}


def _stagnation_days(
    feature: dict,
    transitions: list[dict],
    ordinal_map: dict[str, int],
    today: date,
) -> int:
    """Days since the most recent forward transition. Falls back to created_date."""
    last_forward: str | None = None
    for t in transitions:
        from_ord = ordinal_map.get(t.get("from_status") or "", 0)
        to_ord = ordinal_map.get(t.get("to_status") or "", 0)
        if to_ord > from_ord:
            td = t["transition_date"]
            if last_forward is None or td > last_forward:
                last_forward = td

    ref = safe_date(last_forward) or safe_date(feature.get("created_date"))
    return max(0, (today - ref).days) if ref else 0
