#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "compat/coloros17/settings_homepage_runtime_policy.tsv"

def main() -> int:
    with POLICY.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    failures = []
    if len(rows) != 42:
        failures.append(f"expected 42 homepage rows, got {len(rows)}")

    for row in rows:
        key = row["key"]
        if row["primary_owner"] != "OPLUS_PREFERENCE_GLYPH_AND_TINT":
            failures.append(f"{key}: primary owner drifted")
        if row["primary_action"] != "KEEP_CURRENT_GLYPH":
            failures.append(f"{key}: primary action must keep current glyph")
        if "NATIVE_GATE_FIRST" not in row["release_gate"]:
            failures.append(f"{key}: missing native-gate-first release gate")

        secondary = row["secondary_source"]
        candidate = row["secondary_candidate"]
        if not secondary and candidate:
            failures.append(f"{key}: candidate exists without secondary source")
        if secondary and secondary not in {"NATIVE_EXPRESSIVE","MATERIAL_SYMBOL"}:
            failures.append(f"{key}: invalid secondary source {secondary}")
        if secondary and "POST_GATE_VISUAL_REVIEW_ONLY" not in row["release_gate"]:
            failures.append(f"{key}: secondary candidate lacks post-gate-only guard")

    if failures:
        print("homepage runtime policy violations:")
        for failure in failures:
            print(" -", failure)
        return 1

    secondary = sum(bool(r["secondary_source"]) for r in rows)
    print(f"homepage runtime policy ok: rows={len(rows)} secondary_candidates={secondary}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
