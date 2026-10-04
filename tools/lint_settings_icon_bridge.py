#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/"compat/coloros17/settings_oplus_homepage_icons.tsv"

ALLOWED_ACTIONS={
    "KEEP_NATIVE",
    "NATIVE_EXPRESSIVE",
    "MATERIAL_SYMBOL_CANDIDATE",
}

def main() -> int:
    with MAP.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(
            (line for line in f if line.strip() and not line.lstrip().startswith("#")),
            delimiter="\t",
        ))
    errors=[]
    for row in rows:
        action=row["action"]
        if action not in ALLOWED_ACTIONS:
            errors.append(f"{row['key']}: invalid action {action}")
        if action=="NATIVE_EXPRESSIVE":
            if row["confidence"]!="HIGH" or not row["candidate"].startswith(("ic_","settingslib_")):
                errors.append(f"{row['key']}: unsafe native expressive mapping")
        if action=="MATERIAL_SYMBOL_CANDIDATE" and not row["candidate"]:
            errors.append(f"{row['key']}: material candidate missing symbol")
        if action=="KEEP_NATIVE" and row["candidate"]:
            errors.append(f"{row['key']}: KEEP_NATIVE unexpectedly has candidate")

    if errors:
        print("settings icon bridge policy violations:")
        for err in errors:
            print(" -",err)
        return 1

    counts={}
    for row in rows:
        counts[row["action"]]=counts.get(row["action"],0)+1
    print("settings icon bridge policy ok:",counts)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
