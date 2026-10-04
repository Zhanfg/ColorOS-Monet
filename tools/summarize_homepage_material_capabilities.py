#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--review-manifest",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()

    with args.review_manifest.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))

    by={}
    for row in rows:
        by.setdefault(row["key"],{})[row["state"]]=row

    out=[]
    for key,states in sorted(by.items()):
        base=states.get("base")
        selected=states.get("selected")
        if not base:
            continue
        out.append({
            "key":key,
            "current_icon":base["current_icon"],
            "symbol":base["symbol"],
            "family":base["family"],
            "size":base["size"],
            "base_sha256":base["sha256"],
            "fill1_sha256":selected["sha256"] if selected else "",
            "fill1_changes_geometry":"true" if selected and selected["sha256"] and selected["sha256"]!=base["sha256"] else "false",
            "native_tint_type":base["native_tint_type"],
            "status":"PENDING_GLYPH_SWAP_PROBE",
        })

    fields=list(out[0].keys()) if out else []
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8",newline="") as f:
        if fields:
            w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
            w.writeheader()
            w.writerows(out)
    print(f"candidate_capability_rows={len(out)}")
    print(f"distinct_fill_geometry={sum(r['fill1_changes_geometry']=='true' for r in out)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
