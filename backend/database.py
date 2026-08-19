"""SQLite setup: connection factory and schema initialisation."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "process_eval.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(_SCHEMA)
        _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """Idempotent column-level migrations for existing databases."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(epics)").fetchall()}
    if "is_active" not in existing:
        conn.execute("ALTER TABLE epics ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
    if "closed_at_initial_load" not in existing:
        conn.execute("ALTER TABLE epics ADD COLUMN closed_at_initial_load INTEGER NOT NULL DEFAULT 0")

    # Portfolio Funnel EPICs are pre-startup and must always be fully hidden.
    # Mark any that were left active by a prior ingestion run before this rule existed.
    conn.execute(
        "UPDATE epics SET is_active=0, closed_at_initial_load=1 "
        "WHERE status='Portfolio Funnel' AND (is_active=1 OR closed_at_initial_load=0)"
    )


_SCHEMA = """
-- ── Core entity tables (current state, updated by each delta) ─────────────

CREATE TABLE IF NOT EXISTS epics (
    epic_key                TEXT PRIMARY KEY,
    title                   TEXT NOT NULL,
    status                  TEXT NOT NULL,
    delivery_increment      TEXT,
    in_scope                INTEGER NOT NULL DEFAULT 1,
    -- is_active=0 means the EPIC is in a terminal status (Done/Cancelled/On Hold).
    -- closed_at_initial_load=1 means it was already terminal at the first full upload;
    --   those are excluded from all views. closed_at_initial_load=0 means it
    --   transitioned to terminal after being tracked as active — shown in "Recently Closed".
    is_active               INTEGER NOT NULL DEFAULT 1,
    closed_at_initial_load  INTEGER NOT NULL DEFAULT 0,
    updated_at              TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS capabilities (
    cap_key         TEXT PRIMARY KEY,
    epic_key        TEXT NOT NULL,
    title           TEXT NOT NULL,
    status          TEXT NOT NULL,
    delivery_increment TEXT,
    target_start_date  TEXT,
    target_end_date    TEXT,
    art             TEXT,
    in_scope        INTEGER NOT NULL DEFAULT 1,
    key_anomaly     INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cap_epic ON capabilities(epic_key);
CREATE INDEX IF NOT EXISTS idx_cap_scope ON capabilities(in_scope);

CREATE TABLE IF NOT EXISTS features (
    feature_key     TEXT PRIMARY KEY,
    cap_key         TEXT NOT NULL,
    title           TEXT NOT NULL,
    status          TEXT NOT NULL,
    delivery_increment TEXT,
    target_start_date  TEXT,
    target_end_date    TEXT,
    date_committed  TEXT,
    date_done       TEXT,
    created_date    TEXT NOT NULL,
    art             TEXT,
    in_scope        INTEGER NOT NULL DEFAULT 1,
    previously_blocked INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feat_cap ON features(cap_key);
CREATE INDEX IF NOT EXISTS idx_feat_scope ON features(in_scope);
CREATE INDEX IF NOT EXISTS idx_feat_status ON features(status);

CREATE TABLE IF NOT EXISTS releases (
    release_name    TEXT PRIMARY KEY,
    status          TEXT,
    start_date      TEXT,
    release_date    TEXT,
    progress        TEXT,
    description     TEXT
);

CREATE TABLE IF NOT EXISTS capability_releases (
    cap_key         TEXT NOT NULL,
    release_name    TEXT NOT NULL,
    PRIMARY KEY (cap_key, release_name)
);
CREATE INDEX IF NOT EXISTS idx_caprel_release ON capability_releases(release_name);

CREATE TABLE IF NOT EXISTS epic_releases (
    epic_key        TEXT NOT NULL,
    release_name    TEXT NOT NULL,
    PRIMARY KEY (epic_key, release_name)
);

-- ── Transition history (append-only) ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS feature_transitions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_key     TEXT NOT NULL,
    from_status     TEXT,
    to_status       TEXT NOT NULL,
    transition_date TEXT NOT NULL,
    upload_week     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ftrans_key ON feature_transitions(feature_key);
CREATE INDEX IF NOT EXISTS idx_ftrans_date ON feature_transitions(feature_key, transition_date);

CREATE TABLE IF NOT EXISTS epic_transitions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_key        TEXT NOT NULL,
    from_status     TEXT,
    to_status       TEXT NOT NULL,
    transition_date TEXT NOT NULL,
    upload_week     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_etrans_key ON epic_transitions(epic_key);

-- ── Snapshot store (immutable — one row per entity per week) ──────────────

CREATE TABLE IF NOT EXISTS weekly_snapshots (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_week             TEXT NOT NULL,
    entity_type             TEXT NOT NULL,
    entity_key              TEXT NOT NULL,
    parent_key              TEXT,
    ruleset_version         TEXT NOT NULL,
    dq_score                REAL,
    dq_defect_count         INTEGER,
    dq_attributed_elsewhere INTEGER,
    flow_score              REAL,
    kpi_score               REAL,
    overall_score           REAL,
    health_rag              TEXT,
    delivery_status         TEXT,
    reported_rag            TEXT,
    children_total          INTEGER,
    children_contributing   INTEGER,
    low_confidence          INTEGER NOT NULL DEFAULT 0,
    blocked_count           INTEGER NOT NULL DEFAULT 0,
    high_risk_count         INTEGER NOT NULL DEFAULT 0,
    UNIQUE(upload_week, entity_type, entity_key)
);
CREATE INDEX IF NOT EXISTS idx_snap_week ON weekly_snapshots(upload_week);
CREATE INDEX IF NOT EXISTS idx_snap_entity ON weekly_snapshots(entity_key);

-- ── Supporting tables ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS blocked_items (
    feature_key         TEXT NOT NULL,
    upload_week         TEXT NOT NULL,
    weeks_consecutive   INTEGER NOT NULL,
    stage               TEXT NOT NULL,
    di_band             TEXT,
    penalty_pct         REAL,
    PRIMARY KEY (feature_key, upload_week)
);

CREATE TABLE IF NOT EXISTS dq_defects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_week         TEXT NOT NULL,
    entity_key          TEXT NOT NULL,
    entity_type         TEXT NOT NULL,
    rule_set            TEXT NOT NULL,
    severity            TEXT NOT NULL,
    description         TEXT NOT NULL,
    scoring_attribution TEXT NOT NULL DEFAULT 'DQ',
    first_seen_week     TEXT,
    required_action     TEXT,
    narration           TEXT
);
CREATE INDEX IF NOT EXISTS idx_dq_week ON dq_defects(upload_week);
CREATE INDEX IF NOT EXISTS idx_dq_entity ON dq_defects(entity_key);

CREATE TABLE IF NOT EXISTS agent_runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name          TEXT NOT NULL,
    run_at              TEXT NOT NULL,
    upload_week         TEXT,
    records_processed   INTEGER,
    findings_count      INTEGER,
    status              TEXT NOT NULL,
    duration_seconds    REAL
);

CREATE TABLE IF NOT EXISTS rekey_log (
    old_key             TEXT NOT NULL,
    new_key             TEXT NOT NULL,
    detected_week       TEXT NOT NULL,
    confirmed           INTEGER NOT NULL DEFAULT 0,
    level               TEXT NOT NULL,
    PRIMARY KEY (old_key, detected_week)
);

CREATE TABLE IF NOT EXISTS upload_history (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_week         TEXT NOT NULL UNIQUE,
    uploaded_at         TEXT NOT NULL,
    file_main           TEXT,
    file_releases       TEXT,
    epics_processed     INTEGER,
    capabilities_processed INTEGER,
    features_processed  INTEGER,
    epics_in_scope      INTEGER,
    capabilities_in_scope INTEGER,
    features_in_scope   INTEGER,
    features_excluded   INTEGER,
    warnings            TEXT
);
"""
