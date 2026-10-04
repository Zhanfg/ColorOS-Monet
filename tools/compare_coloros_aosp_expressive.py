#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

def read_col(path: Path, name: str) -> set[str]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if not reader.fieldnames or name not in reader.fieldnames:
            raise RuntimeError(f"{path} missing column {name}")
        return {row[name] for row in reader if row.get(name)}

def main() -> int:
    p = argparse.ArgumentParser(
        description="Compare ColorOS native Expressive resources with an AOSP Settings extraction."
    )
    p.add_argument("--coloros-pairs", type=Path, required=True)
    p.add_argument("--coloros-unmatched", type=Path, required=True)
    p.add_argument("--aosp-wrappers", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    coloros = read_col(args.coloros_pairs, "expressive_resource") | read_col(
        args.coloros_unmatched, "expressive_resource"
    )
    aosp = read_col(args.aosp_wrappers, "expressive_resource")

    common = sorted(coloros & aosp)
    coloros_only = sorted(coloros - aosp)
    aosp_only = sorted(aosp - coloros)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["resource", "status"])
        w.writerows((x, "COLOROS_AND_AOSP") for x in common)
        w.writerows((x, "COLOROS_ONLY") for x in coloros_only)
        w.writerows((x, "AOSP_ONLY") for x in aosp_only)

    print(f"coloros_expressive={len(coloros)}")
    print(f"aosp_wrappers={len(aosp)}")
    print(f"common={len(common)}")
    print(f"coloros_only={len(coloros_only)}")
    print(f"aosp_only={len(aosp_only)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
