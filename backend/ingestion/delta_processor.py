"""
Applies loaded data to the SQLite baseline.

First upload: full dump — inserts everything.
Subsequent uploads: delta — upserts changed records; appends new transitions only
(de-duplicated on feature_key + from_status + to_status + transition_date).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from ingestion.loader import LoadedData


_NOW = lambda: datetime.now(timezone.utc).isoformat()


_DEFAULT_TERMINAL = frozenset({"Done", "Cancelled", "On Hold"})


def apply_delta(
    conn: sqlite3.Connection,
    data: LoadedData,
    upload_week: str,
    terminal_statuses: frozenset[str] | set[str] | None = None,
) -> None:
    """
    Upsert entities and append new transitions.
    *upload_week* is an ISO week string, e.g. '2026-W34'.
    *terminal_statuses*: EPIC statuses treated as closed. EPICs already in a
    terminal status at the first upload are excluded from the active dashboard
    (closed_at_initial_load=1). EPICs that transition to terminal status in a
    later delta move to the "Recently Closed" section (closed_at_initial_load=0).
    """
    if terminal_statuses is None:
        terminal_statuses = _DEFAULT_TERMINAL
    terminal_statuses = frozenset(terminal_statuses)

    now = _NOW()
    is_first_upload = conn.execute("SELECT COUNT(*) FROM upload_history").fetchone()[0] == 0

    # ── Releases (upsert) ─────────────────────────────────────────────────
    for r in data.releases:
        conn.execute(
            """
            INSERT INTO releases (release_name, status, start_date, release_date, progress, description)
            VALUES (:release_name, :status, :start_date, :release_date, :progress, :description)
            ON CONFLICT(release_name) DO UPDATE SET
                status       = excluded.status,
                start_date   = COALESCE(excluded.start_date, releases.start_date),
                release_date = COALESCE(excluded.release_date, releases.release_date),
                progress     = excluded.progress,
                description  = excluded.description
            """,
            r,
        )

    # ── EPIC–Release links (replace all from this upload) ─────────────────
    if data.epic_releases:
        epic_keys_in_upload = {r["epic_key"] for r in data.epic_releases}
        for ek in epic_keys_in_upload:
            conn.execute("DELETE FROM epic_releases WHERE epic_key = ?", (ek,))
        conn.executemany(
            "INSERT OR IGNORE INTO epic_releases (epic_key, release_name) VALUES (:epic_key, :release_name)",
            data.epic_releases,
        )

    # ── Capability–Release links (replace all from this upload) ───────────
    if data.capability_releases:
        cap_keys_in_upload = {r["cap_key"] for r in data.capability_releases}
        for ck in cap_keys_in_upload:
            conn.execute("DELETE FROM capability_releases WHERE cap_key = ?", (ck,))
        conn.executemany(
            "INSERT OR IGNORE INTO capability_releases (cap_key, release_name) VALUES (:cap_key, :release_name)",
            data.capability_releases,
        )

    # ── EPICs (upsert with active/closed tracking) ────────────────────────
    for e in data.epics:
        is_terminal = e["status"] in terminal_statuses

        if is_first_upload:
            is_active = 0 if is_terminal else 1
            closed_at_initial_load = 1 if is_terminal else 0
        else:
            prev = conn.execute(
                "SELECT is_active, closed_at_initial_load FROM epics WHERE epic_key=?",
                (e["epic_key"],),
            ).fetchone()
            if prev is None:
                # Brand-new EPIC appearing mid-tracking
                is_active = 0 if is_terminal else 1
                closed_at_initial_load = 0
            elif prev["is_active"] == 1 and is_terminal:
                # Was active, now closed — move to Recently Closed
                is_active = 0
                closed_at_initial_load = 0
            else:
                # Already closed, or still active — preserve existing flags
                is_active = prev["is_active"]
                closed_at_initial_load = prev["closed_at_initial_load"]

        conn.execute(
            """
            INSERT INTO epics
                (epic_key, title, status, delivery_increment, in_scope,
                 is_active, closed_at_initial_load, updated_at)
            VALUES
                (:epic_key, :title, :status, :delivery_increment, 1,
                 :is_active, :closed_at_initial_load, :updated_at)
            ON CONFLICT(epic_key) DO UPDATE SET
                title                  = excluded.title,
                status                 = excluded.status,
                delivery_increment     = excluded.delivery_increment,
                is_active              = excluded.is_active,
                closed_at_initial_load = excluded.closed_at_initial_load,
                updated_at             = excluded.updated_at
            """,
            {**e, "is_active": is_active, "closed_at_initial_load": closed_at_initial_load, "updated_at": now},
        )

    # ── Capabilities (upsert) ─────────────────────────────────────────────
    for c in data.capabilities:
        conn.execute(
            """
            INSERT INTO capabilities
                (cap_key, epic_key, title, status, delivery_increment,
                 target_start_date, target_end_date, in_scope, key_anomaly, updated_at)
            VALUES
                (:cap_key, :epic_key, :title, :status, :delivery_increment,
                 :target_start_date, :target_end_date, 1, 0, :updated_at)
            ON CONFLICT(cap_key) DO UPDATE SET
                epic_key           = excluded.epic_key,
                title              = excluded.title,
                status             = excluded.status,
                delivery_increment = excluded.delivery_increment,
                target_start_date  = excluded.target_start_date,
                target_end_date    = excluded.target_end_date,
                updated_at         = excluded.updated_at
            """,
            {**c, "updated_at": now},
        )

    # ── Features (upsert, ART enriched) ───────────────────────────────────
    art = data.art_lookup
    for f in data.features:
        f_art = art.get(f["feature_key"])
        conn.execute(
            """
            INSERT INTO features
                (feature_key, cap_key, title, status, delivery_increment,
                 target_start_date, target_end_date, date_committed, date_done,
                 created_date, art, in_scope, previously_blocked, updated_at)
            VALUES
                (:feature_key, :cap_key, :title, :status, :delivery_increment,
                 :target_start_date, :target_end_date, :date_committed, :date_done,
                 :created_date, :art, 1, 0, :updated_at)
            ON CONFLICT(feature_key) DO UPDATE SET
                cap_key            = excluded.cap_key,
                title              = excluded.title,
                status             = excluded.status,
                delivery_increment = excluded.delivery_increment,
                target_start_date  = excluded.target_start_date,
                target_end_date    = excluded.target_end_date,
                date_committed     = excluded.date_committed,
                date_done          = excluded.date_done,
                created_date       = excluded.created_date,
                art                = excluded.art,
                updated_at         = excluded.updated_at
            """,
            {**f, "art": f_art, "updated_at": now},
        )

    # ── EPIC Transitions (append-only, de-duplicate) ───────────────────────
    existing_etrans = set(
        conn.execute(
            "SELECT epic_key || '|' || COALESCE(from_status,'') || '|' || to_status || '|' || COALESCE(transition_date,'') FROM epic_transitions"
        ).fetchall()
    )
    existing_etrans = {r[0] for r in existing_etrans}

    new_etrans = []
    for t in data.epic_transitions:
        if not t.get("transition_date"):
            continue  # skip dateless transitions — unusable for stagnation/KPI clocks
        sig = f"{t['epic_key']}|{t['from_status'] or ''}|{t['to_status']}|{t['transition_date']}"
        if sig not in existing_etrans:
            new_etrans.append({**t, "upload_week": upload_week})
            existing_etrans.add(sig)

    if new_etrans:
        conn.executemany(
            """
            INSERT INTO epic_transitions (epic_key, from_status, to_status, transition_date, upload_week)
            VALUES (:epic_key, :from_status, :to_status, :transition_date, :upload_week)
            """,
            new_etrans,
        )

    # ── Feature Transitions (append-only, de-duplicate) ───────────────────
    # Load existing signatures — only for feature keys present in this upload
    # (avoids loading the full 150k-row table into memory every time)
    upload_feature_keys = {t["feature_key"] for t in data.feature_transitions}
    if upload_feature_keys:
        placeholders = ",".join("?" * len(upload_feature_keys))
        existing_ftrans = {
            r[0]
            for r in conn.execute(
                f"SELECT feature_key || '|' || COALESCE(from_status,'') || '|' || to_status || '|' || COALESCE(transition_date,'') "
                f"FROM feature_transitions WHERE feature_key IN ({placeholders})",
                list(upload_feature_keys),
            ).fetchall()
        }
    else:
        existing_ftrans = set()

    new_ftrans = []
    for t in data.feature_transitions:
        if not t.get("transition_date"):
            continue  # skip dateless transitions
        sig = f"{t['feature_key']}|{t['from_status'] or ''}|{t['to_status']}|{t['transition_date']}"
        if sig not in existing_ftrans:
            new_ftrans.append({**t, "upload_week": upload_week})
            existing_ftrans.add(sig)

    if new_ftrans:
        conn.executemany(
            """
            INSERT INTO feature_transitions (feature_key, from_status, to_status, transition_date, upload_week)
            VALUES (:feature_key, :from_status, :to_status, :transition_date, :upload_week)
            """,
            new_ftrans,
        )
