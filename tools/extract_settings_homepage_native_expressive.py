#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RESOURCE_RE = re.compile(r"^\s*resource\s+(0x[0-9a-fA-F]+)\s+([^/\s]+)/(.+?)\s*$")
REF_RE = re.compile(r"=@(0x[0-9a-fA-F]+)")
DRAWABLE_RE = re.compile(r"drawable\(0x01010199\)=@(0x[0-9a-fA-F]+)")
COLOR_RE = re.compile(r"color\(0x010101a5\)=@(0x[0-9a-fA-F]+)")

def popen_resource_map(aapt2: Path, apk: Path) -> dict[str, str]:
    proc = subprocess.Popen(
        [str(aapt2), "dump", "resources", "--no-values", str(apk)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    assert proc.stdout is not None
    result: dict[str, str] = {}
    for line in proc.stdout:
        m = RESOURCE_RE.match(line)
        if not m:
            continue
        name = m.group(3).removesuffix(" PUBLIC")
        result[m.group(1).lower()] = f"{m.group(2)}/{name}"
    if proc.wait() != 0:
        raise RuntimeError("aapt2 resource dump failed")
    return result

def xmltree(aapt2: Path, apk: Path, name: str) -> tuple[str, str]:
    out = subprocess.run(
        [str(aapt2), "dump", "xmltree", "--file", name, str(apk)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout
    return name, out

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--aapt2", type=Path, required=True)
    p.add_argument("--settings-apk", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    idmap = popen_resource_map(args.aapt2, args.settings_apk)

    with zipfile.ZipFile(args.settings_apk) as zf:
        files = sorted(
            n for n in zf.namelist()
            if n.startswith("res/drawable/ic_homepage_") and n.endswith(".xml")
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        trees = dict(pool.map(lambda n: xmltree(args.aapt2, args.settings_apk, n), files))

    rows = []
    for path in files:
        text = trees[path]
        drawable_ids = DRAWABLE_RE.findall(text)
        color_ids = COLOR_RE.findall(text)
        # Search / AI-search wrappers are structurally different and intentionally
        # omitted from the category-icon table.
        if not drawable_ids:
            continue
        foreground = idmap.get(drawable_ids[-1].lower(), "")
        background = idmap.get(color_ids[0].lower(), "") if color_ids else ""
        foreground_name = foreground.split("/", 1)[-1]
        rows.append({
            "target_package": "com.android.settings",
            "homepage_wrapper": Path(path).stem,
            "container_size": "24dp",
            "foreground_size": "16dp",
            "inset": "4dp",
            "background_color": background.split("/", 1)[-1],
            "foreground_drawable": foreground_name,
            "foreground_kind": (
                "NATIVE_EXPRESSIVE"
                if "expressive" in foreground_name
                else "NATIVE_NON_EXPRESSIVE"
            ),
            "evidence": "BINARY_XML_DIRECT_REFERENCE",
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "target_package","homepage_wrapper","container_size","foreground_size",
        "inset","background_color","foreground_drawable","foreground_kind","evidence",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    expressive = sum(r["foreground_kind"] == "NATIVE_EXPRESSIVE" for r in rows)
    print(f"homepage_category_wrappers={len(rows)}")
    print(f"native_expressive_foregrounds={expressive}")
    print(f"native_non_expressive_foregrounds={len(rows)-expressive}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
