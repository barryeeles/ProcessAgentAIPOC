"""
Detects key mutations (FCB re-keying) and phantom records.

When a Capability or Feature is re-associated with a Backlog parent, JIRA
re-keys it to an FCB-* key. The old key stops appearing in deltas (absence =
unchanged), creating a phantom — an in-scope record that never updates.

Strategy (§13.2):
  1. For each new FCB-* key, try to match against an existing baseline record
     by title (+ created_date for Features).
  2. Corroborate the match with a second signal before flagging.
  3. Quarantine (don't auto-merge) on weak matches.
  4. Detect phantoms: in-scope records with no update for ≥N weeks while
     their parent or children have changed.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from config_loader import get_config


@dataclass
class RekeyCandidate:
    old_key: str
    new_key: str
    level: str            # 'capability' | 'feature'
    confidence: str       # 'high' | 'low'
    reason: str


def detect_rekeys(
    conn: sqlite3.Connection,
    upload_week: str,
    new_cap_keys: set[str],
    new_feat_keys: set[str],
) -> list[RekeyCandidate]:
    """
    Compare newly-uploaded FCB-* keys against the existing baseline.
    Returns candidates for human review — does NOT auto-merge.
    """
    cfg = get_config()
    candidates: list[RekeyCandidate] = []

    # ── Capability re-keys ─────────────────────────────────────────────────
    new_fcb_caps = {k for k in new_cap_keys if k.upper().startswith("FCB-")}
    for new_key in new_fcb_caps:
        # Look up the title of this new FCB Capability in the DB (just inserted)
        row = conn.execute(
            "SELECT title FROM capabilities WHERE cap_key = ?", (new_key,)
        ).fetchone()
        if not row:
            continue
        title = row["title"]

        # Find a baseline Capability with the same title but a different key
        existing = conn.execute(
            "SELECT cap_key FROM capabilities WHERE title = ? AND cap_key != ? AND cap_key NOT LIKE 'FCB-%'",
            (title, new_key),
        ).fetchone()
        if not existing:
            continue
        old_key = existing["cap_key"]

        # Corroborate: do the new FCB key's Features overlap with the old key's?
        old_features = {
            r[0]
            for r in conn.execute(
                "SELECT feature_key FROM features WHERE cap_key = ?", (old_key,)
            ).fetchall()
        }
        new_features = {
            r[0]
            for r in conn.execute(
                "SELECT feature_key FROM features WHERE cap_key = ?", (new_key,)
            ).fetchall()
        }
        overlap = old_features & new_features
        confidence = "high" if len(overlap) >= 2 or (old_features and not new_features) else "low"

        candidates.append(RekeyCandidate(
            old_key=old_key,
            new_key=new_key,
            level="capability",
            confidence=confidence,
            reason=f"Title match; {len(overlap)} child Feature(s) overlap",
        ))

    # ── Feature re-keys ────────────────────────────────────────────────────
    new_fcb_feats = {k for k in new_feat_keys if k.upper().startswith("FCB-")}
    for new_key in new_fcb_feats:
        row = conn.execute(
            "SELECT title, created_date FROM features WHERE feature_key = ?", (new_key,)
        ).fetchone()
        if not row:
            continue
        title, created_date = row["title"], row["created_date"]

        existing = conn.execute(
            """SELECT feature_key FROM features
               WHERE title = ? AND created_date = ? AND feature_key != ?
               AND feature_key NOT LIKE 'FCB-%'""",
            (title, created_date, new_key),
        ).fetchone()
        if not existing:
            continue
        old_key = existing["feature_key"]
        confidence = "high"   # title + created_date is near-unique per spec §13.2
        candidates.append(RekeyCandidate(
            old_key=old_key,
            new_key=new_key,
            level="feature",
            confidence=confidence,
            reason="Title + Created date match",
        ))

    # ── Persist candidates ─────────────────────────────────────────────────
    for c in candidates:
        conn.execute(
            """
            INSERT OR IGNORE INTO rekey_log (old_key, new_key, detected_week, confirmed, level)
            VALUES (?, ?, ?, 0, ?)
            """,
            (c.old_key, c.new_key, upload_week, c.level),
        )

    return candidates


def detect_phantoms(conn: sqlite3.Connection, upload_week: str) -> list[str]:
    """
    Return keys of in-scope records that look like phantom re-key victims:
    no update for ≥N weeks while their parent/children have changed.
    Currently returns keys only — flagged in DQ checklist, not auto-resolved.
    """
    cfg = get_config()
    n_weeks = cfg.thresholds.rekey_phantom_weeks

    # Simple heuristic: in-scope Capabilities whose updated_at is older than
    # N upload cycles AND whose Features were updated more recently.
    # (Full week-counter logic requires upload_history; this is a PoC approximation.)
    phantoms: list[str] = []

    rows = conn.execute(
        """
        SELECT c.cap_key, c.updated_at,
               MAX(f.updated_at) AS latest_child_update
        FROM capabilities c
        LEFT JOIN features f ON f.cap_key = c.cap_key AND f.in_scope = 1
        WHERE c.in_scope = 1
        GROUP BY c.cap_key
        HAVING latest_child_update > c.updated_at
        """
    ).fetchall()

    # A real phantom would have been static for many weeks — flag in the
    # rekey_log only if the key looks like it hasn't been updated at all
    # across the last N upload cycles (upload_history table tracks this).
    # For now return the candidates so they appear in the DQ checklist.
    for row in rows:
        phantoms.append(row["cap_key"])

    return phantoms
