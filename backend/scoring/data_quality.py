"""
Data Quality scoring — Rule Sets 1–5.

Writes defects to dq_defects and returns per-Capability DQ scores (0–100).
Score per Capability: max(0, 100 - sum of DQ-attributed defect weights)
  Weights: HIGH=3, MEDIUM=2, WARNING=1
"""
from __future__ import annotations

import sqlite3
from datetime import date

from config_loader import AppConfig
from scoring._utils import di_quarter_bounds, parse_di, safe_date


_POST_BACKLOG = {
    "In Analysis", "PI Backlog", "PI Planning", "Committed",
    "In Development", "Dev Complete", "In Testing", "Test Complete",
    "Deploying", "Deployment Complete", "Releasing", "Done",
    "Ready for Delivery", "In Review",
}


def run_data_quality(
    conn: sqlite3.Connection,
    upload_week: str,
    config: AppConfig,
) -> dict:
    """Run all DQ rule sets. Returns {cap_scores, defects, total_defects}."""
    today = date.today()
    fiscal_sm = config.fiscal_calendar["start_month"]
    sev_w = config.dq_severity_weights

    # ── Load data ──────────────────────────────────────────────────────────
    caps = {
        r["cap_key"]: dict(r)
        for r in conn.execute(
            "SELECT c.*, e.status AS epic_status FROM capabilities c "
            "JOIN epics e ON e.epic_key = c.epic_key WHERE c.in_scope = 1"
        ).fetchall()
    }

    all_features = [dict(r) for r in conn.execute(
        "SELECT * FROM features WHERE in_scope = 1"
    ).fetchall()]
    cap_features: dict[str, list[dict]] = {}
    for f in all_features:
        cap_features.setdefault(f["cap_key"], []).append(f)

    cap_rel_rows = conn.execute(
        "SELECT cap_key, release_name FROM capability_releases"
    ).fetchall()
    cap_releases: dict[str, list[str]] = {}
    for r in cap_rel_rows:
        cap_releases.setdefault(r["cap_key"], []).append(r["release_name"])

    epic_rel_rows = conn.execute(
        "SELECT epic_key, release_name FROM epic_releases"
    ).fetchall()
    epic_releases: dict[str, set[str]] = {}
    for r in epic_rel_rows:
        epic_releases.setdefault(r["epic_key"], set()).add(r["release_name"])

    releases = {
        r["release_name"]: dict(r)
        for r in conn.execute("SELECT * FROM releases").fetchall()
    }

    # ── Clear previous defects for this week and rebuild ──────────────────
    conn.execute("DELETE FROM dq_defects WHERE upload_week = ?", (upload_week,))
    defects: list[dict] = []

    # ── RS1A: Capability with no release link ─────────────────────────────
    for cap_key, cap in caps.items():
        if cap_key not in cap_releases:
            sev = _di_sev(cap.get("delivery_increment"), today, fiscal_sm)
            defects.append(_d(
                upload_week, cap_key, "capability", "RS1A", sev,
                f"Capability {cap_key} has no Fix Version (release) assigned.",
                "Assign a release via JIRA Fix Versions.",
            ))

    # ── RS1B: Release name missing EPIC prefix / missing dates ────────────
    seen_release_date_check: set[str] = set()
    for cap_key, rel_names in cap_releases.items():
        cap = caps.get(cap_key, {})
        epic_key = cap.get("epic_key", "")
        epic_prefix = epic_key.split("-")[0] if "-" in epic_key else ""
        for rname in rel_names:
            rel = releases.get(rname, {})
            if epic_prefix and epic_prefix not in rname:
                defects.append(_d(
                    upload_week, cap_key, "capability", "RS1B", "MEDIUM",
                    f"Release '{rname}' does not contain EPIC prefix '{epic_prefix}'.",
                    "Rename the release to include the EPIC key prefix.",
                ))
            if rname not in seen_release_date_check:
                seen_release_date_check.add(rname)
                if not rel.get("start_date"):
                    defects.append(_d(
                        upload_week, rname, "release", "RS1B", "MEDIUM",
                        f"Release '{rname}' has no Start Date.",
                        "Add a Start Date to the release in JIRA.",
                    ))
                if not rel.get("release_date"):
                    defects.append(_d(
                        upload_week, rname, "release", "RS1B", "MEDIUM",
                        f"Release '{rname}' has no Release Date.",
                        "Add a Release Date to the release in JIRA.",
                    ))

    # ── RS1C: Capability linked to >1 release ─────────────────────────────
    for cap_key, rel_names in cap_releases.items():
        if len(rel_names) > 1:
            defects.append(_d(
                upload_week, cap_key, "capability", "RS1C", "HIGH",
                f"Capability {cap_key} is linked to {len(rel_names)} releases: "
                f"{', '.join(sorted(rel_names))}.",
                "Reduce to a single release; split the Capability if work spans multiple releases.",
            ))

    # ── RS2: Capability status vs child Feature status inconsistencies ─────
    for cap_key, cap in caps.items():
        feats = cap_features.get(cap_key, [])
        if not feats:
            continue
        cap_status = cap.get("status", "")
        has_blocked_child = any(f["status"] == "Blocked" for f in feats)
        active = [f for f in feats if f["status"] not in ("Cancelled",)]

        if not active:
            continue

        # RS2C (precedence 3): Capability Done but has non-Done, non-Cancelled children
        # Blocked children suppress this rule
        if cap_status == "Done" and not has_blocked_child:
            non_done = [f for f in active if f["status"] != "Done"]
            if non_done:
                defects.append(_d(
                    upload_week, cap_key, "capability", "RS2C", "HIGH",
                    f"Capability {cap_key} is Done but has {len(non_done)} non-Done "
                    f"child Feature(s) (e.g. {non_done[0]['feature_key']}).",
                    "Close or cancel remaining child Features.",
                ))

        # RS2A (precedence 1): All active children completed/deploying but Capability not advanced
        elif cap_status not in ("Done", "Cancelled", "Releasing", "Deployment Complete", "Deploying"):
            late_statuses = {"Done", "Deploying", "Deployment Complete", "Releasing", "Test Complete"}
            all_late = all(f["status"] in late_statuses for f in active)
            if all_late:
                defects.append(_d(
                    upload_week, cap_key, "capability", "RS2A", "MEDIUM",
                    f"All {len(active)} active Features in {cap_key} are in late/done status "
                    f"but Capability is still '{cap_status}'.",
                    "Advance Capability status to reflect Feature completion.",
                ))

    # ── RS3: Post-Backlog missing DI / target dates; Target End < Start ────
    for cap_key, cap in caps.items():
        if cap.get("status") in (None, "Funnel", "Cancelled"):
            continue
        if cap.get("status") in _POST_BACKLOG:
            for field, label in [
                ("delivery_increment", "Delivery Increment"),
                ("target_start_date", "Target Start Date"),
                ("target_end_date", "Target End Date"),
            ]:
                if not cap.get(field):
                    defects.append(_d(
                        upload_week, cap_key, "capability", "RS3", "MEDIUM",
                        f"Capability {cap_key} is post-Backlog but missing {label}.",
                        f"Set {label} in JIRA.",
                    ))
        ts, te = safe_date(cap.get("target_start_date")), safe_date(cap.get("target_end_date"))
        if ts and te and te < ts:
            defects.append(_d(
                upload_week, cap_key, "capability", "RS3", "HIGH",
                f"Capability {cap_key} Target End ({te}) is before Target Start ({ts}).",
                "Correct Target Start/End dates in JIRA.",
            ))

    for f in all_features:
        if f.get("status") in (None, "Funnel", "Cancelled"):
            continue
        if not f.get("delivery_increment"):
            defects.append(_d(
                upload_week, f["feature_key"], "feature", "RS3", "MEDIUM",
                f"Feature {f['feature_key']} is post-Funnel but has no Delivery Increment.",
                "Set the Delivery Increment field in JIRA.",
            ))
        ts, te = safe_date(f.get("target_start_date")), safe_date(f.get("target_end_date"))
        if ts and te and te < ts:
            defects.append(_d(
                upload_week, f["feature_key"], "feature", "RS3", "HIGH",
                f"Feature {f['feature_key']} Target End ({te}) is before Target Start ({ts}).",
                "Correct Target Start/End dates in JIRA.",
            ))

    # ── RS4: Date boundary violations ─────────────────────────────────────
    for cap_key, cap in caps.items():
        cap_end = safe_date(cap.get("target_end_date"))
        for rname in cap_releases.get(cap_key, []):
            rel = releases.get(rname, {})
            rel_date = safe_date(rel.get("release_date"))
            if cap_end and rel_date and cap_end > rel_date:
                defects.append(_d(
                    upload_week, cap_key, "capability", "RS4", "HIGH",
                    f"Capability {cap_key} Target End ({cap_end}) exceeds "
                    f"Release '{rname}' date ({rel_date}).",
                    "Align Capability target dates with the Release schedule.",
                ))
        for feat in cap_features.get(cap_key, []):
            feat_end = safe_date(feat.get("target_end_date"))
            if cap_end and feat_end and feat_end > cap_end:
                defects.append(_d(
                    upload_week, feat["feature_key"], "feature", "RS4", "MEDIUM",
                    f"Feature {feat['feature_key']} Target End ({feat_end}) exceeds "
                    f"parent Capability {cap_key} Target End ({cap_end}).",
                    "Align Feature target dates within the Capability boundary.",
                ))

    # ── RS5: Release orphan/link anomalies ────────────────────────────────
    # RS5A: Capability's release not in parent EPIC's release list → HIGH
    for cap_key, cap in caps.items():
        epic_key = cap.get("epic_key")
        epic_rel_set = epic_releases.get(epic_key, set())
        if not epic_rel_set:
            continue
        for rname in cap_releases.get(cap_key, []):
            if rname not in epic_rel_set:
                defects.append(_d(
                    upload_week, cap_key, "capability", "RS5A", "HIGH",
                    f"Capability {cap_key} release '{rname}' is not in parent "
                    f"EPIC {epic_key}'s release list.",
                    "Add the release to the parent EPIC in JIRA, or reassign the Capability.",
                ))

    # RS5B: Release in the release table not linked to any Capability → WARNING
    linked_releases = {rn for rns in cap_releases.values() for rn in rns}
    for rname in releases:
        if rname not in linked_releases:
            defects.append(_d(
                upload_week, rname, "release", "RS5B", "WARNING",
                f"Release '{rname}' has no Capabilities linked to it.",
                "Link Capabilities to this release or remove the empty release.",
            ))

    # ── Persist defects ────────────────────────────────────────────────────
    if defects:
        conn.executemany(
            """INSERT INTO dq_defects
               (upload_week, entity_key, entity_type, rule_set, severity,
                description, scoring_attribution, required_action)
               VALUES (:upload_week, :entity_key, :entity_type, :rule_set, :severity,
                       :description, :scoring_attribution, :required_action)""",
            defects,
        )

    # ── Per-Capability DQ score ────────────────────────────────────────────
    # Feature defects roll up to their parent capability
    feat_to_cap = {f["feature_key"]: f["cap_key"] for f in all_features}
    cap_weight_sum: dict[str, float] = {}
    for d in defects:
        if d["scoring_attribution"] != "DQ":
            continue
        ek = d["entity_key"]
        if d["entity_type"] == "feature":
            ek = feat_to_cap.get(ek, ek)
        cap_weight_sum[ek] = cap_weight_sum.get(ek, 0.0) + sev_w.get(d["severity"], 0)

    cap_scores: dict[str, float] = {
        cap_key: max(0.0, 100.0 - cap_weight_sum.get(cap_key, 0.0))
        for cap_key in caps
    }

    return {"cap_scores": cap_scores, "defects": defects, "total_defects": len(defects)}


# ── helpers ────────────────────────────────────────────────────────────────

def _di_sev(di_str, today: date, fiscal_sm: int) -> str:
    parsed = parse_di(di_str)
    if not parsed:
        return "WARNING"
    fy2, q = parsed
    try:
        start, end = di_quarter_bounds(fy2, q, fiscal_sm)
    except Exception:
        return "WARNING"
    if today > end:
        return "HIGH"
    if today >= start:
        return "MEDIUM"
    return "WARNING"


def _d(
    upload_week: str,
    entity_key: str,
    entity_type: str,
    rule_set: str,
    severity: str,
    description: str,
    required_action: str,
    attribution: str = "DQ",
) -> dict:
    return {
        "upload_week": upload_week,
        "entity_key": entity_key,
        "entity_type": entity_type,
        "rule_set": rule_set,
        "severity": severity,
        "description": description,
        "scoring_attribution": attribution,
        "required_action": required_action,
    }
