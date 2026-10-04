#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

def read(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--unmatched", type=Path, required=True)
    p.add_argument("--overlap", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args=p.parse_args()

    overlap=defaultdict(list)
    for row in read(args.overlap):
        overlap[row["resource_name"]].append(row)

    fields=[
        "target_package","resource_type","expressive_resource","classification",
        "upstream_source","upstream_path","provenance_status","notes",
    ]
    out=[]
    for row in read(args.unmatched):
        matches=[]
        for candidate in overlap.get(row["expressive_resource"], []):
            packages=(candidate.get("target_packages") or "").split(",")
            if not packages or row["target_package"] in packages or "android" in packages:
                matches.append(candidate)
        preferred=next((m for m in matches if m["status"]=="EXACT_ANDROID17_NAME_MATCH"), matches[0] if matches else None)
        item={k:row.get(k,"") for k in ("target_package","resource_type","expressive_resource","classification")}
        if preferred and preferred["status"]=="EXACT_ANDROID17_NAME_MATCH":
            item.update(
                upstream_source=preferred.get("upstream_source",""),
                upstream_path=preferred.get("upstream_path",""),
                provenance_status="EXACT_ANDROID17_NAME_MATCH",
                notes="ColorOS resource name is exactly present in pinned Android 17 upstream",
            )
        else:
            item.update(
                upstream_source=preferred.get("upstream_source","") if preferred else "",
                upstream_path=preferred.get("upstream_path","") if preferred else "",
                provenance_status=preferred.get("status","NO_ANDROID17_MATCH") if preferred else "NO_ANDROID17_MATCH",
                notes="Keep ColorOS-native; do not synthesize a replacement from name alone",
            )
        out.append(item)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        w.writeheader(); w.writerows(out)

    exact=sum(r["provenance_status"]=="EXACT_ANDROID17_NAME_MATCH" for r in out)
    print(f"rows={len(out)} exact_android17={exact} non_exact={len(out)-exact}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
