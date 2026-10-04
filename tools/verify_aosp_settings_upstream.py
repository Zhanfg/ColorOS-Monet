#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import urllib.request
from pathlib import Path

PREFIX=")]}'\n"

def fetch_text(url: str) -> str:
    req=urllib.request.Request(url, headers={"User-Agent":"ColorOS-Monet-upstream-verifier/1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

def fetch_json(url: str):
    text=fetch_text(url)
    if text.startswith(PREFIX):
        text=text[len(PREFIX):]
    return json.loads(text)

def fetch_gitiles_file(base: str, ref: str, path: str) -> bytes:
    url=f"{base}/+/{ref}/{path}?format=TEXT"
    raw=fetch_text(url).strip()
    return base64.b64decode(raw)

def resolve_ref(base: str, ref: str) -> tuple[str, dict]:
    # Gitiles commit endpoint returns metadata including commit/tree/parents.
    data=fetch_json(f"{base}/+/{ref}?format=JSON")
    commit=data.get("commit") or data.get("id")
    if not commit:
        raise RuntimeError(f"Gitiles response did not expose commit id for {ref}: {data.keys()}")
    return commit, data

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args=p.parse_args()

    cfg={}
    for line in args.source.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        k,v=line.split("=",1)
        cfg[k.strip()]=v.strip()

    base=cfg.get("repository","https://android.googlesource.com/platform/packages/apps/Settings").rstrip("/")
    branch=cfg.get("branch","android17-release")
    branch_ref=cfg.get("branch_ref",f"refs/heads/{branch}")
    branch_head, branch_meta=resolve_ref(base, branch_ref)

    pinned=cfg.get("pinned_commit") or branch_head
    pinned_commit, pinned_meta=resolve_ref(base, pinned)
    if pinned_commit != pinned:
        raise RuntimeError(f"pinned commit did not resolve exactly: {pinned} -> {pinned_commit}")

    required=[
        "res/drawable/ic_settings_display_expressive.xml",
        "res/drawable/ic_settings_privacy_expressive.xml",
        "res/drawable/ic_settings_security_expressive.xml",
        "res/drawable/ic_settings_location_expressive.xml",
        "res/drawable/ic_notifications_expressive.xml",
        "res/drawable/ic_help_expressive.xml",
    ]
    verified=[]
    for path in required:
        data=fetch_gitiles_file(base, pinned, path)
        if not data.strip():
            raise RuntimeError(f"empty upstream file: {path}")
        verified.append((path,len(data)))

    out=[
        f"repository={base}",
        f"branch={branch}",
        f"branch_ref={branch_ref}",
        f"branch_head={branch_head}",
        f"pinned_commit={pinned}",
        f"pinned_tree={pinned_meta.get('tree','')}",
        f"update_available={1 if branch_head != pinned else 0}",
        "status=verified_pinned",
        f"verified_file_count={len(verified)}",
    ]
    for i,(path,size) in enumerate(verified,1):
        out.append(f"verified_file_{i}={path}|{size}")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text("\n".join(out)+"\n",encoding="utf-8")
    print("\n".join(out))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
