#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ALLOWED_SOURCE = {
    "KEEP_NATIVE",
    "NATIVE_EXPRESSIVE",
    "MATERIAL_SYMBOL",
}
ALLOWED_STATUS = {
    "MAPPED",
    "PROBE_READY",
    "NEEDS_REVIEW",
}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--table", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    args = p.parse_args()

    with args.catalog.open(encoding="utf-8", newline="") as f:
        catalog_rows = list(csv.DictReader(f, delimiter="	"))
    symbols = {r["symbol"] for r in catalog_rows if r.get("symbol")}

    failures = []
    rows = []
    with args.table.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="	")
        expected = {
            "key","current_icon","preferred_source","preferred_candidate",
            "material_symbol_fallback","confidence","status","notes",
        }
        if set(reader.fieldnames or []) != expected:
            failures.append(f"unexpected header: {reader.fieldnames}")
        rows = list(reader)

    seen = set()
    for row in rows:
        key = row["key"]
        if key in seen:
            failures.append(f"duplicate key: {key}")
        seen.add(key)

        source = row["preferred_source"]
        if source not in ALLOWED_SOURCE:
            failures.append(f"{key}: invalid preferred_source={source}")

        if row["confidence"] not in {"HIGH","MEDIUM","LOW"}:
            failures.append(f"{key}: invalid confidence={row['confidence']}")
        if row["status"] not in ALLOWED_STATUS:
            failures.append(f"{key}: invalid status={row['status']}")

        fallback = row["material_symbol_fallback"]
        if fallback and fallback not in symbols:
            failures.append(f"{key}: missing Material Symbol fallback={fallback}")

        if source == "MATERIAL_SYMBOL":
            candidate = row["preferred_candidate"]
            if not candidate:
                failures.append(f"{key}: MATERIAL_SYMBOL without preferred_candidate")
            elif candidate not in symbols:
                failures.append(f"{key}: missing Material Symbol candidate={candidate}")
            if row["status"] != "PROBE_READY":
                failures.append(f"{key}: MATERIAL_SYMBOL row must be PROBE_READY")

        if source == "NATIVE_EXPRESSIVE":
            if not row["preferred_candidate"].startswith(("ic_","settingslib_")):
                failures.append(f"{key}: suspicious native Expressive candidate={row['preferred_candidate']}")

        if source == "KEEP_NATIVE" and row["preferred_candidate"]:
            failures.append(f"{key}: KEEP_NATIVE must not set preferred_candidate")

    if len(rows) != 42:
        failures.append(f"expected 42 OPlus homepage rows, got {len(rows)}")

    if failures:
        print("homepage source-map validation failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    counts = {}
    for row in rows:
        counts[row["preferred_source"]] = counts.get(row["preferred_source"], 0) + 1
    print(f"homepage source-map ok: rows={len(rows)} counts={counts}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
