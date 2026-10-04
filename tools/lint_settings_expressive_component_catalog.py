#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TABLE=ROOT/"compat/coloros17/settings_expressive_component_catalog.tsv"

ALLOWED={
    "USE_NATIVE_COMPONENT",
    "PRESERVE_OPLUS_OWNER",
    "KEEP_NATIVE_UNTIL_TRACE",
}

def main() -> int:
    with TABLE.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(
            (line for line in f if line.strip() and not line.lstrip().startswith("#")),
            delimiter="\t",
        ))
    errors=[]
    for row in rows:
        if row["decision"] not in ALLOWED:
            errors.append(f"{row['component']}: invalid decision {row['decision']}")
        if row["confidence"] not in {"HIGH","MEDIUM","LOW"}:
            errors.append(f"{row['component']}: invalid confidence {row['confidence']}")
        if not row["owner"] or not row["activation"]:
            errors.append(f"{row['component']}: owner/activation missing")
        if "CardHook" in row["owner"] or "ListHook" in row["owner"]:
            errors.append(f"{row['component']}: legacy global hook is not a native owner")
    if errors:
        print("Settings Expressive component catalog violations:")
        for error in errors:
            print(" -",error)
        return 1
    print(f"Settings Expressive component catalog ok: {len(rows)} components")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
