#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

def read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def expressive_forms(base: str) -> set[str]:
    forms = {f"{base}_expressive", f"expressive_{base}"}
    for suffix in ("_filled", "_icon", "_normal", "_pressed", "_disabled", "_themed"):
        if base.endswith(suffix):
            stem = base[: -len(suffix)]
            forms.add(f"{stem}_expressive")
    return forms

def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Prioritize deterministic Material Symbol candidates behind native "
            "ColorOS Expressive siblings. This is review metadata only."
        )
    )
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--expressive-inventory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--package", action="append", dest="packages")
    args = p.parse_args()

    expressive: dict[str, set[str]] = defaultdict(set)
    for row in read_dicts(args.expressive_inventory):
        expressive[row["target_package"]].add(row["resource_name"])

    packages = set(args.packages or [])
    rows = []
    for row in read_dicts(args.candidates):
        package = row["target_package"]
        if packages and package not in packages:
            continue

        siblings = sorted(
            expressive_forms(row["resource_name"]) & expressive.get(package, set())
        )
        row = dict(row)
        row["native_expressive_sibling"] = ";".join(siblings)
        row["review_action"] = (
            "PREFER_NATIVE_EXPRESSIVE" if siblings else "MATERIAL_SYMBOL_REVIEW"
        )
        rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else [
        "target_package","resource_type","resource_name","classification",
        "source_target","matched_form","material_symbol","score","reason",
        "state_hint","native_expressive_sibling","review_action",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    counts = Counter((r["target_package"], r["review_action"]) for r in rows)
    print(f"rows={len(rows)}")
    for (package, action), count in sorted(counts.items()):
        print(f"{package}\t{action}\t{count}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
