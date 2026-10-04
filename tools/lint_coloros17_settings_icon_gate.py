#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_MAP = ROOT / "compat/material-symbols/native_expressive_map.tsv"
MATERIAL_MAP = ROOT / "compat/material-symbols/coloros_icon_map.tsv"
ROUTE = ROOT / "compat/coloros17/settings_homepage_route.tsv"
HOMEPAGE = ROOT / "compat/coloros17/settings_oplus_homepage_icons.tsv"

def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        raw = [line for line in f if line.strip() and not line.lstrip().startswith("#")]
    return list(csv.DictReader(raw, delimiter="\t"))

def drawable_name(value: str) -> str:
    value = (value or "").strip()
    for prefix in ("@drawable/", "drawable/"):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value

def truthy(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes"}

def main() -> int:
    failures = []

    route = {r["stage"]: r for r in rows(ROUTE)}
    required = {
        "launcher_entry": "com.oplus.settings.feature.homepage.OplusSettingsHomepageActivity",
        "fragment_factory": "com.oplus.settings.feature.homepage.OplusTopLevelSettings",
        "screen_resource": "xml/top_level_settings_oplus",
    }
    for stage, needle in required.items():
        row = route.get(stage)
        if not row or needle not in "\t".join(row.values()):
            failures.append(f"missing homepage route evidence: {stage} -> {needle}")

    homepage = rows(HOMEPAGE)
    if len(homepage) != 42:
        failures.append(f"unexpected OPlus homepage icon row count: {len(homepage)} != 42")

    two_tone = sum(truthy(r.get("showTwoToneColor", "")) for r in homepage)
    if two_tone != 41:
        failures.append(f"unexpected OPlus two-tone row count: {two_tone} != 41")

    homepage_icons = {drawable_name(r.get("current_icon", "")) for r in homepage}
    explicit_expressive_current = [
        r.get("current_icon", "")
        for r in homepage
        if "expressive" in (r.get("current_icon", "") or "").lower()
    ]
    if explicit_expressive_current:
        failures.append(
            "OPlus homepage unexpectedly references explicit expressive icons: "
            f"{explicit_expressive_current}"
        )

    allowed_home_actions = {
        "KEEP_NATIVE",
        "NATIVE_EXPRESSIVE",
        "MATERIAL_SYMBOL_CANDIDATE",
        "NEEDS_REVIEW",
    }
    for row in homepage:
        action = row.get("action", "")
        if action not in allowed_home_actions:
            failures.append(
                f"invalid OPlus homepage source decision: {row.get('key')}={action}"
            )
        # Candidate rows document a source only; they are not shipping replacements.
        if action == "MATERIAL_SYMBOL_CANDIDATE" and not row.get("candidate", ""):
            failures.append(
                f"Material Symbol candidate missing glyph: {row.get('key')}"
            )

    for row in rows(NATIVE_MAP):
        if row["target_package"] != "com.android.settings":
            continue
        base = drawable_name(row["current_or_base_resource"])
        if base in homepage_icons:
            failures.append(
                "non-homepage native expressive table collides with OPlus homepage icon: "
                f"{base}"
            )
        if "NOT_OPLUS_HOMEPAGE_ICON_RESOURCE" not in row["verification"]:
            failures.append(
                "Settings native expressive row missing verified homepage exclusion: "
                f"{row['current_or_base_resource']}"
            )

    for row in rows(MATERIAL_MAP):
        if row["target_package"] != "com.android.settings":
            continue
        base = drawable_name(
            row.get("current_or_base_resource", "") or row.get("target_resource", "")
        )
        if base in homepage_icons and row.get("action") in {
            "MATERIAL_SYMBOL",
            "STATEFUL_SYMBOL",
        }:
            failures.append(f"OPlus homepage icon promoted to Material Symbol: {base}")

    if failures:
        print("settings icon gate violations:")
        for failure in failures:
            print(" -", failure)
        return 1

    print(
        "settings icon gate ok: "
        f"{len(homepage)} OPlus homepage rows / {two_tone} two-tone rows / "
        "homepage icon sources remain candidate-only"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
