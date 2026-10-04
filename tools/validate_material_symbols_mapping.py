#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

def asset_name(symbol: str, size: str, variant: str) -> str:
    suffix = "" if variant in {"", "base"} else f"_{variant}"
    return f"{symbol}{suffix}_{size}px.xml"

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--upstream", type=Path, required=True)
    p.add_argument("--mapping", type=Path, required=True)
    args = p.parse_args()

    android = args.upstream / "symbols" / "android"
    failures = []
    rows = 0
    with args.mapping.open(encoding="utf-8", newline="") as f:
        for raw in f:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            cols = next(csv.reader([raw], delimiter="\t"))
            if len(cols) != 11:
                failures.append(f"invalid column count: {raw.rstrip()}")
                continue
            (
                package, resource, semantic, symbol, family, size,
                unselected, selected, action, confidence, notes,
            ) = cols
            rows += 1

            directory = android / symbol / family
            if not directory.is_dir():
                failures.append(f"{package}:{resource}: missing {symbol}/{family}")
                continue

            base = directory / asset_name(symbol, size, unselected)
            if not base.is_file():
                failures.append(f"{package}:{resource}: missing {base.name}")

            if action == "STATEFUL_SYMBOL":
                active = directory / asset_name(symbol, size, selected)
                if not active.is_file():
                    failures.append(f"{package}:{resource}: missing {active.name}")

            if action not in {"KEEP_NATIVE","MATERIAL_SYMBOL","STATEFUL_SYMBOL","NEEDS_REVIEW"}:
                failures.append(f"{package}:{resource}: invalid action {action}")
            if confidence not in {"HIGH","MEDIUM","LOW"}:
                failures.append(f"{package}:{resource}: invalid confidence {confidence}")

    if failures:
        print("mapping validation failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print(f"mapping validation ok: {rows} rows")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
