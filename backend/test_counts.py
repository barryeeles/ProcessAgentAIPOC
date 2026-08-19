"""Quick DB count verification."""
import sys
sys.path.insert(0, ".")
from database import get_connection

with get_connection() as conn:
    ft = conn.execute("SELECT COUNT(*) FROM feature_transitions").fetchone()[0]
    et = conn.execute("SELECT COUNT(*) FROM epic_transitions").fetchone()[0]
    feats_with_hist = conn.execute(
        "SELECT COUNT(DISTINCT feature_key) FROM feature_transitions"
    ).fetchone()[0]
    in_scope_feats = conn.execute("SELECT COUNT(*) FROM features WHERE in_scope=1").fetchone()[0]
    blocked_feats = conn.execute(
        "SELECT COUNT(*) FROM features WHERE status='Blocked' AND in_scope=1"
    ).fetchone()[0]
    caps_no_feats = conn.execute(
        """SELECT COUNT(DISTINCT c.cap_key) FROM capabilities c
           LEFT JOIN features f ON f.cap_key=c.cap_key AND f.in_scope=1
           WHERE c.in_scope=1 AND f.feature_key IS NULL"""
    ).fetchone()[0]
    releases = conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
    cap_rels = conn.execute("SELECT COUNT(*) FROM capability_releases").fetchone()[0]

print(f"Feature transitions stored: {ft}  (spec: ~1903 in-scope)")
print(f"Epic transitions stored: {et}")
print(f"Features with any transition history: {feats_with_hist}  (spec: 362)")
print(f"In-scope features: {in_scope_feats}  (expected: 598)")
print(f"Blocked features (in-scope): {blocked_feats}  (spec: 9)")
print(f"In-scope Capabilities with no Features: {caps_no_feats}  (spec: ~219)")
print(f"Releases loaded: {releases}")
print(f"Capability-Release links: {cap_rels}")
