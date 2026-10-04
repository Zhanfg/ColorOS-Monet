#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

def dict_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        lines=[line for line in f if line.strip() and not line.lstrip().startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))

def native_resources(pairs: Path, native_map: Path, unmatched: Path) -> set[str]:
    out=set()
    for row in dict_rows(pairs):
        out.add(row["expressive_resource"])
    for row in dict_rows(unmatched):
        out.add(row["expressive_resource"])

    with native_map.open(encoding="utf-8", newline="") as f:
        for raw in f:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            cols=next(csv.reader([raw], delimiter="\t"))
            if len(cols)>=4:
                out.add(cols[3])
    return out

def main() -> int:
    p=argparse.ArgumentParser(
        description="Validate OPlus homepage icon candidates against current native Expressive resources and pinned Material Symbols."
    )
    p.add_argument("--homepage", type=Path, required=True)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--native-pairs", type=Path, required=True)
    p.add_argument("--native-map", type=Path, required=True)
    p.add_argument("--native-unmatched", type=Path, required=True)
    args=p.parse_args()

    catalog={
        line.strip()
        for line in args.catalog.read_text(encoding="utf-8").splitlines()[1:]
        if line.strip()
    }
    native=native_resources(args.native_pairs,args.native_map,args.native_unmatched)

    failures=[]
    counts={"NATIVE_EXPRESSIVE":0,"MATERIAL_SYMBOL_CANDIDATE":0,"KEEP_NATIVE":0,"NEEDS_REVIEW":0}
    for row in dict_rows(args.homepage):
        action=row["action"]
        candidate=row["candidate"]
        if action not in counts:
            failures.append(f"{row['key']}: unsupported action {action}")
            continue
        counts[action]+=1

        if action=="NATIVE_EXPRESSIVE":
            if not candidate:
                failures.append(f"{row['key']}: missing native Expressive candidate")
            elif candidate not in native:
                failures.append(
                    f"{row['key']}: native Expressive candidate not proven in current ROM: {candidate}"
                )
        elif action=="MATERIAL_SYMBOL_CANDIDATE":
            if not candidate:
                failures.append(f"{row['key']}: missing Material Symbol candidate")
            elif candidate not in catalog:
                failures.append(
                    f"{row['key']}: Material Symbol missing from pinned upstream: {candidate}"
                )
        elif action=="KEEP_NATIVE" and candidate:
            failures.append(f"{row['key']}: KEEP_NATIVE must not name replacement candidate")

    print("homepage candidate counts:")
    for key in sorted(counts):
        print(f"  {key}={counts[key]}")

    if failures:
        print("homepage candidate validation failed:")
        for failure in failures:
            print(" -",failure)
        return 1

    print("VERIFIED: every OPlus homepage replacement candidate exists in its declared source")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
