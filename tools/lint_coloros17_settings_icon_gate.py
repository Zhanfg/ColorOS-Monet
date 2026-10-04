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
        raw=[line for line in f if line.strip() and not line.lstrip().startswith("#")]
    return list(csv.DictReader(raw, delimiter="\t"))

def main() -> int:
    failures=[]

    route={r["stage"]:r for r in rows(ROUTE)}
    required={
        "launcher_entry":"com.oplus.settings.feature.homepage.OplusSettingsHomepageActivity",
        "fragment_factory":"com.oplus.settings.feature.homepage.OplusTopLevelSettings",
        "screen_resource":"xml/top_level_settings_oplus",
    }
    for stage,needle in required.items():
        row=route.get(stage)
        if not row or needle not in "\t".join(row.values()):
            failures.append(f"missing homepage route evidence: {stage} -> {needle}")

    homepage=rows(HOMEPAGE)
    if len(homepage)!=42:
        failures.append(f"unexpected OPlus homepage icon row count: {len(homepage)} != 42")
    two_tone=sum(r["show_two_tone"]=="1" for r in homepage)
    if two_tone!=41:
        failures.append(f"unexpected OPlus two-tone row count: {two_tone} != 41")
    expressive_names=[r["icon_resource"] for r in homepage if "expressive" in r["icon_resource"].lower()]
    if expressive_names:
        failures.append(f"OPlus homepage unexpectedly references explicit expressive icons: {expressive_names}")

    homepage_icons={r["icon_resource"] for r in homepage}

    for row in rows(NATIVE_MAP):
        if row["target_package"]!="com.android.settings":
            continue
        if row["current_or_base_resource"] in homepage_icons:
            failures.append(
                f"native expressive map collides with OPlus homepage-owned icon: "
                f"{row['current_or_base_resource']}"
            )
        if "NOT_OPLUS_HOMEPAGE_ICON_RESOURCE" not in row["verification"]:
            failures.append(
                f"Settings native expressive row missing verified homepage exclusion: "
                f"{row['current_or_base_resource']}"
            )

    for row in rows(MATERIAL_MAP):
        if row["target_package"]!="com.android.settings":
            continue
        if row["current_or_base_resource"] if "current_or_base_resource" in row else False:
            base=row["current_or_base_resource"]
        else:
            base=row.get("target_resource","")
        if base in homepage_icons and row.get("action") in {"MATERIAL_SYMBOL","STATEFUL_SYMBOL"}:
            failures.append(f"OPlus homepage icon promoted to Material Symbol: {base}")

    if failures:
        print("settings icon gate violations:")
        for x in failures:
            print(" -",x)
        return 1

    print(
        "settings icon gate ok: "
        "42 OPlus homepage icon rows / 41 native two-tone rows / "
        "no bulk Expressive or Material Symbol replacement"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
