#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import urllib.request
from pathlib import Path

API="https://api.github.com"
UPSTREAM="google/material-design-icons"
FAMILY="materialsymbolsrounded"
SIZE="24"

def load_source(path: Path) -> dict[str,str]:
    out={}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        k,v=line.split("=",1)
        out[k.strip()]=v.strip()
    return out

def rows(path: Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8",newline="") as f:
        lines=[line for line in f if line.strip() and not line.lstrip().startswith("#")]
    return list(csv.DictReader(lines,delimiter="\t"))

def api_json(url: str, token: str) -> dict:
    headers={"Accept":"application/vnd.github+json","User-Agent":"ColorOS-Monet-icon-review/1"}
    if token:
        headers["Authorization"]=f"Bearer {token}"
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_file(path: str, ref: str, token: str) -> bytes:
    url=f"{API}/repos/{UPSTREAM}/contents/{path}?ref={ref}"
    data=api_json(url,token)
    if data.get("encoding")!="base64":
        raise RuntimeError(f"unexpected encoding for {path}: {data.get('encoding')}")
    return base64.b64decode(data["content"])

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def material_name(symbol: str, filled: bool) -> str:
    suffix="_fill1" if filled else ""
    return f"{symbol}{suffix}_{SIZE}px.xml"

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--homepage",type=Path,required=True)
    p.add_argument("--upstream-lock",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()

    lock=load_source(args.upstream_lock)
    ref=lock["ref"]
    token=os.environ.get("GITHUB_TOKEN","")
    args.output.mkdir(parents=True,exist_ok=True)

    manifest=[]
    seen=set()
    for row in rows(args.homepage):
        if row["action"]!="MATERIAL_SYMBOL_CANDIDATE":
            continue
        symbol=row["candidate"]
        if not symbol:
            raise RuntimeError(f"{row['key']}: candidate action without symbol")

        # One copy per homepage preference, even if symbols repeat, because tint/category
        # metadata belongs to the ColorOS consumer rather than to the glyph itself.
        d=args.output/"candidates"/row["key"]
        d.mkdir(parents=True,exist_ok=True)

        for state,filled in (("base",False),("selected",True)):
            name=material_name(symbol,filled)
            upstream_path=f"symbols/android/{symbol}/{FAMILY}/{name}"
            try:
                data=fetch_file(upstream_path,ref,token)
                available="1"
            except Exception:
                if filled:
                    # selected/fill1 is optional in review packs
                    available="0"
                    data=b""
                else:
                    raise

            if data:
                (d/f"{state}.xml").write_bytes(data)

            manifest.append({
                "key":row["key"],
                "parent_key":row["parent_key"],
                "preference_class":row["preference_class"],
                "current_icon":row["current_icon"],
                "controller":row["controller"],
                "native_tint_type":row["native_tint_type"],
                "showTwoToneColor":row["showTwoToneColor"],
                "symbol":symbol,
                "family":FAMILY,
                "size":SIZE,
                "state":state,
                "available":available,
                "upstream_path":upstream_path,
                "upstream_ref":ref,
                "sha256":digest(data) if data else "",
            })
        seen.add(symbol)

    license_data=fetch_file("LICENSE",ref,token)
    (args.output/"UPSTREAM_LICENSE.txt").write_bytes(license_data)

    fields=list(manifest[0].keys()) if manifest else []
    with (args.output/"REVIEW_MANIFEST.tsv").open("w",encoding="utf-8",newline="") as f:
        if fields:
            w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
            w.writeheader()
            w.writerows(manifest)

    readme=[
        "ColorOS 17 Settings homepage Material Symbols review pack",
        "",
        f"Pinned upstream: {UPSTREAM}@{ref}",
        f"Family: {FAMILY}",
        f"Optical size: {SIZE}",
        "",
        "This is NOT a flashable overlay.",
        "It contains only Google Material Symbols candidates for OPlus homepage rows",
        "whose semantics were classified as generic gaps.",
        "",
        "ColorOS preference class/two-tone tint metadata remains authoritative.",
        "Native Expressive/OEM-specific rows are intentionally not copied here.",
        "",
        f"Unique candidate symbols: {len(seen)}",
        f"Homepage candidate rows: {len({m['key'] for m in manifest})}",
    ]
    (args.output/"README.txt").write_text("\n".join(readme)+"\n",encoding="utf-8")
    print(f"candidate_rows={len({m['key'] for m in manifest})}")
    print(f"unique_symbols={len(seen)}")
    print(f"manifest_rows={len(manifest)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
