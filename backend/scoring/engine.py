"""Orchestrates all scoring modules for a given upload week."""
from __future__ import annotations

import sqlite3

from config_loader import AppConfig
from scoring.blocked import run_blocked
from scoring.data_quality import run_data_quality
from scoring.flow_throughput import run_flow_throughput
from scoring.kpis import run_kpis
from scoring.rollup import run_rollup
from scoring.snapshot_writer import write_snapshots


def run_scoring(conn: sqlite3.Connection, upload_week: str, config: AppConfig) -> dict:
    """
    Run the full scoring pipeline and write immutable snapshots.
    Order: DQ → Flow → KPIs → Blocked → Rollup → Snapshots.
    Returns a summary dict for the API response.
    """
    dq = run_data_quality(conn, upload_week, config)
    flow = run_flow_throughput(conn, upload_week, config)
    kpi = run_kpis(conn, upload_week, config)
    blk = run_blocked(conn, upload_week, config)
    scores = run_rollup(conn, upload_week, config, dq, flow, kpi, blk)
    n_snaps = write_snapshots(conn, upload_week, config, scores)

    return {
        "dq_defects": dq["total_defects"],
        "snapshots_written": n_snaps,
        "blocked_features": blk["total"],
        "escalated_blocked": blk["escalated"],
    }
