#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/"compat/material-symbols/settings_homepage_full_source_map.tsv"

ALLOWED_SOURCE={
    "KEEP_NATIVE",
    "NATIVE_EXPRESSIVE",
    "MATERIAL_SYMBOL",
}

def main() -> int:
    with MAP.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))

    errors=[]
    seen=set()
    for row in rows:
        key=row["key"]
        if key in seen:
            errors.append(f"{key}: duplicate")
        seen.add(key)

        source=row["preferred_source"]
        candidate=row["preferred_candidate"]
        confidence=row["confidence"]
        status=row["status"]

        if source not in ALLOWED_SOURCE:
            errors.append(f"{key}: invalid preferred_source {source}")
        if confidence not in {"HIGH","MEDIUM","LOW"}:
            errors.append(f"{key}: invalid confidence {confidence}")
        if status not in {"MAPPED","PROBE_READY","NEEDS_REVIEW"}:
            errors.append(f"{key}: invalid status {status}")

        if source=="NATIVE_EXPRESSIVE":
            if confidence!="HIGH" or not candidate.startswith(("ic_","settingslib_")):
                errors.append(f"{key}: unsafe native expressive mapping")
            if status!="PROBE_READY":
                errors.append(f"{key}: native expressive row must be PROBE_READY")
        elif source=="MATERIAL_SYMBOL":
            if confidence not in {"HIGH","MEDIUM"} or not candidate:
                errors.append(f"{key}: unsafe Material Symbol mapping")
            if status!="PROBE_READY":
                errors.append(f"{key}: Material Symbol row must be PROBE_READY")
        elif source=="KEEP_NATIVE" and candidate:
            errors.append(f"{key}: KEEP_NATIVE unexpectedly has preferred_candidate")

    if len(rows)!=42:
        errors.append(f"expected 42 homepage rows, got {len(rows)}")

    if errors:
        print("settings icon bridge policy violations:")
        for err in errors:
            print(" -",err)
        return 1

    counts={}
    for row in rows:
        counts[row["preferred_source"]]=counts.get(row["preferred_source"],0)+1
    print("settings icon bridge policy ok:",counts)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
