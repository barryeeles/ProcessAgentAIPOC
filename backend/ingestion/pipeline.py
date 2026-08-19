"""
Orchestrates the full ingestion pipeline for a weekly upload.

Steps (in order):
  1. Load Excel bytes into LoadedData objects
  2. Apply delta to baseline DB tables
  3. Re-apply scope filter to full baseline
  4. Detect re-key candidates
  5. Record upload in upload_history
  Returns a summary dict suitable for the API response.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from config_loader import get_config
from database import get_connection, init_db
from ingestion.delta_processor import apply_delta
from ingestion.loader import LoadedData, load_main_workbook, load_releases_workbook
from ingestion.rekey_detector import detect_phantoms, detect_rekeys
from ingestion.scope_filter import apply_scope
from scoring.engine import run_scoring


UPLOADS_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"


def _current_week() -> str:
    """ISO week string, e.g. '2026-W34'."""
    now = datetime.now(timezone.utc)
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def run_ingestion(
    main_bytes: bytes | None,
    releases_bytes: bytes | None,
    main_filename: str = "EPIC.xlsx",
    releases_filename: str = "EPIC Releases.xlsx",
) -> dict:
    """
    Run the full ingestion pipeline.
    At least one of main_bytes or releases_bytes must be provided.
    """
    init_db()  # idempotent — safe to call on every ingestion
    upload_week = _current_week()
    warnings: list[str] = []

    main_data: LoadedData | None = None
    rel_data: LoadedData | None = None

    if main_bytes:
        main_data = load_main_workbook(main_bytes)
        warnings.extend(main_data.warnings)

    if releases_bytes:
        rel_data = load_releases_workbook(releases_bytes)
        warnings.extend(rel_data.warnings)

    with get_connection() as conn:
        # Merge into a single LoadedData for the delta processor
        merged = LoadedData()
        if main_data:
            merged.epics = main_data.epics
            merged.epic_transitions = main_data.epic_transitions
            merged.capabilities = main_data.capabilities
            merged.features = main_data.features
            merged.feature_transitions = main_data.feature_transitions
            merged.art_lookup = main_data.art_lookup
        if rel_data:
            merged.releases = rel_data.releases
            merged.epic_releases = rel_data.epic_releases
            merged.capability_releases = rel_data.capability_releases

        cfg = get_config()
        terminal_statuses = frozenset(cfg.scope.epic_terminal_statuses)
        apply_delta(conn, merged, upload_week, terminal_statuses=terminal_statuses)

        scope = apply_scope(conn)
        epics_active = conn.execute(
            "SELECT COUNT(*) FROM epics WHERE in_scope=1 AND is_active=1"
        ).fetchone()[0]
        epics_initially_closed = conn.execute(
            "SELECT COUNT(*) FROM epics WHERE in_scope=1 AND closed_at_initial_load=1"
        ).fetchone()[0]

        new_cap_keys = {c["cap_key"] for c in (main_data.capabilities if main_data else [])}
        new_feat_keys = {f["feature_key"] for f in (main_data.features if main_data else [])}
        rekey_candidates = detect_rekeys(conn, upload_week, new_cap_keys, new_feat_keys)
        _detect_phantoms = detect_phantoms(conn, upload_week)

        # Record upload
        conn.execute(
            """
            INSERT INTO upload_history
                (upload_week, uploaded_at, file_main, file_releases,
                 epics_processed, capabilities_processed, features_processed,
                 epics_in_scope, capabilities_in_scope, features_in_scope,
                 features_excluded, warnings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(upload_week) DO UPDATE SET
                uploaded_at            = excluded.uploaded_at,
                file_main              = excluded.file_main,
                file_releases          = excluded.file_releases,
                epics_processed        = excluded.epics_processed,
                capabilities_processed = excluded.capabilities_processed,
                features_processed     = excluded.features_processed,
                epics_in_scope         = excluded.epics_in_scope,
                capabilities_in_scope  = excluded.capabilities_in_scope,
                features_in_scope      = excluded.features_in_scope,
                features_excluded      = excluded.features_excluded,
                warnings               = excluded.warnings
            """,
            (
                upload_week,
                datetime.now(timezone.utc).isoformat(),
                main_filename if main_bytes else None,
                releases_filename if releases_bytes else None,
                len(merged.epics),
                len(merged.capabilities),
                len(merged.features),
                scope.epics_in_scope,
                scope.capabilities_in_scope,
                scope.features_in_scope,
                scope.features_excluded,
                "; ".join(warnings) if warnings else None,
            ),
        )

        # Scoring runs inside the same connection after upload_history is committed
        scoring_summary = run_scoring(conn, upload_week, cfg)

    # Archive files
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    if main_bytes:
        (UPLOADS_DIR / f"{upload_week}_{main_filename}").write_bytes(main_bytes)
    if releases_bytes:
        (UPLOADS_DIR / f"{upload_week}_{releases_filename}").write_bytes(releases_bytes)

    return {
        "upload_week": upload_week,
        "epics_processed": len(merged.epics),
        "capabilities_processed": len(merged.capabilities),
        "features_processed": len(merged.features),
        "epics_in_scope": scope.epics_in_scope,
        "epics_active": epics_active,
        "epics_initially_closed": epics_initially_closed,
        "capabilities_in_scope": scope.capabilities_in_scope,
        "features_in_scope": scope.features_in_scope,
        "features_excluded": scope.features_excluded,
        "capabilities_excluded": scope.capabilities_excluded,
        "capabilities_key_anomaly": scope.capabilities_key_anomaly,
        "dq_defects": scoring_summary["dq_defects"],
        "snapshots_written": scoring_summary["snapshots_written"],
        "blocked_features": scoring_summary["blocked_features"],
        "escalated_blocked": scoring_summary["escalated_blocked"],
        "rekey_candidates": [
            {
                "old_key": c.old_key,
                "new_key": c.new_key,
                "level": c.level,
                "confidence": c.confidence,
                "reason": c.reason,
            }
            for c in rekey_candidates
        ],
        "warnings": warnings,
    }
