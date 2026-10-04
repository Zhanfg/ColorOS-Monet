#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "compat/material-symbols/native_expressive_map.tsv"
ROUTE = ROOT / "compat/coloros17/settings_homepage_route.tsv"

def main() -> int:
    failures=[]

    with ROUTE.open(encoding="utf-8", newline="") as f:
        rows=list(csv.DictReader(f, delimiter="\t"))
    route={r["stage"]:r for r in rows}
    required={
        "launcher_entry":"com.oplus.settings.feature.homepage.OplusSettingsHomepageActivity",
        "fragment_factory":"com.oplus.settings.feature.homepage.OplusTopLevelSettings",
        "screen_resource":"xml/top_level_settings_oplus",
    }
    for stage,needle in required.items():
        row=route.get(stage)
        if not row or needle not in "\t".join(row.values()):
            failures.append(f"missing homepage route evidence: {stage} -> {needle}")

    with MAP.open(encoding="utf-8", newline="") as f:
        raw=[line for line in f if line.strip()]
    if not raw:
        failures.append("native expressive map is empty")
        raw=[]
    if raw and raw[0].startswith("#"):
        header=raw[0].lstrip("# ").rstrip("\n")
        data=[line for line in raw[1:] if not line.startswith("#")]
        reader=csv.DictReader(data, fieldnames=header.split("\t"), delimiter="\t")
    else:
        reader=csv.DictReader((line for line in raw if not line.startswith("#")), delimiter="\t")
    for row in reader:
            if row["target_package"]!="com.android.settings":
                continue
            if row["decision"] in {"MATERIAL_SYMBOL","STATEFUL_SYMBOL"}:
                failures.append(
                    f"Settings homepage/native expressive row prematurely promoted: "
                    f"{row['current_or_base_resource']}={row['decision']}"
                )
            if "PENDING_OPLUS_TOP_LEVEL_XML_CONSUMER" not in row["verification"]:
                failures.append(
                    f"Settings row missing OPlus XML consumer gate: {row['current_or_base_resource']}"
                )

    if failures:
        print("settings icon gate violations:")
        for x in failures:
            print(" -",x)
        return 1

    print("settings icon gate ok: ColorOS homepage remains native until top_level_settings_oplus consumer is verified")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
