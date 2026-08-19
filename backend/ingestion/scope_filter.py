"""
Resolves scope membership for the full accumulated baseline.

Scope rule (§3.2): a Capability is in scope only if its parent EPIC is in scope.
A Feature is in scope only if its parent Capability is in scope. EPIC scope is
determined by key prefix (FCM / RN — configurable).

This module is called on every upload against the full accumulated baseline,
because re-parenting can change scope membership between uploads.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from config_loader import get_config


@dataclass
class ScopeSummary:
    epics_total: int
    epics_in_scope: int
    capabilities_total: int
    capabilities_in_scope: int
    capabilities_excluded: int
    capabilities_key_anomaly: int
    features_total: int
    features_in_scope: int
    features_excluded: int


def apply_scope(conn: sqlite3.Connection) -> ScopeSummary:
    """
    Re-evaluate scope for every entity in the baseline.
    Updates the in_scope column on epics, capabilities, and features in place.
    Returns a summary of counts for the Transparency Panel.
    """
    cfg = get_config()
    epic_prefixes = tuple(cfg.scope.epic_key_prefixes)
    cap_prefixes = tuple(cfg.scope.capability_key_prefixes)

    # ── EPICs ──────────────────────────────────────────────────────────────
    # All EPICs are loaded; in_scope = 1 iff key prefix matches
    conn.execute("UPDATE epics SET in_scope = 0")
    if epic_prefixes:
        placeholders = ",".join("?" for _ in epic_prefixes)
        patterns = [f"{p}-%" for p in epic_prefixes]
        # sqlite LIKE for each prefix
        for prefix in epic_prefixes:
            conn.execute(
                "UPDATE epics SET in_scope = 1 WHERE epic_key LIKE ?",
                (f"{prefix}-%",),
            )

    # ── Capabilities ───────────────────────────────────────────────────────
    # In scope iff their parent EPIC is in scope
    conn.execute("UPDATE capabilities SET in_scope = 0")
    conn.execute(
        """
        UPDATE capabilities SET in_scope = 1
        WHERE epic_key IN (SELECT epic_key FROM epics WHERE in_scope = 1)
        """
    )

    # Flag Capabilities whose own key prefix is unexpected (not FCM/RN/FCB)
    conn.execute("UPDATE capabilities SET key_anomaly = 0")
    for prefix in cap_prefixes:
        conn.execute(
            "UPDATE capabilities SET key_anomaly = 0 WHERE cap_key LIKE ?",
            (f"{prefix}-%",),
        )
    # Anything in_scope but key doesn't match any expected prefix → anomaly
    conditions = " AND ".join(f"cap_key NOT LIKE ?" for _ in cap_prefixes)
    params = [f"{p}-%" for p in cap_prefixes]
    conn.execute(
        f"UPDATE capabilities SET key_anomaly = 1 WHERE in_scope = 1 AND ({conditions})",
        params,
    )

    # ── Features ───────────────────────────────────────────────────────────
    conn.execute("UPDATE features SET in_scope = 0")
    conn.execute(
        """
        UPDATE features SET in_scope = 1
        WHERE cap_key IN (SELECT cap_key FROM capabilities WHERE in_scope = 1)
        """
    )

    # ── Gather counts ──────────────────────────────────────────────────────
    def count(table: str, where: str = "") -> int:
        sql = f"SELECT COUNT(*) FROM {table}"
        if where:
            sql += f" WHERE {where}"
        return conn.execute(sql).fetchone()[0]

    return ScopeSummary(
        epics_total=count("epics"),
        epics_in_scope=count("epics", "in_scope = 1"),
        capabilities_total=count("capabilities"),
        capabilities_in_scope=count("capabilities", "in_scope = 1"),
        capabilities_excluded=count("capabilities", "in_scope = 0"),
        capabilities_key_anomaly=count("capabilities", "key_anomaly = 1"),
        features_total=count("features"),
        features_in_scope=count("features", "in_scope = 1"),
        features_excluded=count("features", "in_scope = 0"),
    )
