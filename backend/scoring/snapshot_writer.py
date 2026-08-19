"""Writes one immutable weekly_snapshots row per in-scope entity per upload week."""
from __future__ import annotations

import sqlite3

from config_loader import AppConfig


def write_snapshots(
    conn: sqlite3.Connection,
    upload_week: str,
    config: AppConfig,
    scores: dict,
) -> int:
    """Insert snapshot rows. IGNORE on conflict (snapshots are immutable once written)."""
    rv = config.ruleset_version
    rows: list[dict] = []

    for group in ("caps", "epics", "releases"):
        for sc in scores.get(group, {}).values():
            rows.append({
                "upload_week": upload_week,
                "entity_type": sc.get("entity_type", group.rstrip("s")),
                "entity_key": sc["entity_key"],
                "parent_key": sc.get("parent_key"),
                "ruleset_version": rv,
                "dq_score": sc.get("dq_score"),
                "dq_defect_count": None,
                "dq_attributed_elsewhere": None,
                "flow_score": sc.get("flow_score"),
                "kpi_score": sc.get("kpi_score"),
                "overall_score": sc.get("overall_score"),
                "health_rag": sc.get("health_rag", "U"),
                "delivery_status": sc.get("delivery_status", "unassessed"),
                "reported_rag": sc.get("reported_rag", "U"),
                "children_total": sc.get("children_total", 0),
                "children_contributing": sc.get("children_contributing", 0),
                "low_confidence": sc.get("low_confidence", 0),
                "blocked_count": sc.get("blocked_count", 0),
                "high_risk_count": sc.get("high_risk_count", 0),
            })

    if rows:
        conn.executemany(
            """INSERT OR IGNORE INTO weekly_snapshots
               (upload_week, entity_type, entity_key, parent_key, ruleset_version,
                dq_score, dq_defect_count, dq_attributed_elsewhere,
                flow_score, kpi_score, overall_score,
                health_rag, delivery_status, reported_rag,
                children_total, children_contributing, low_confidence,
                blocked_count, high_risk_count)
               VALUES
               (:upload_week, :entity_type, :entity_key, :parent_key, :ruleset_version,
                :dq_score, :dq_defect_count, :dq_attributed_elsewhere,
                :flow_score, :kpi_score, :overall_score,
                :health_rag, :delivery_status, :reported_rag,
                :children_total, :children_contributing, :low_confidence,
                :blocked_count, :high_risk_count)""",
            rows,
        )

    return len(rows)
